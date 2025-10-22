import frappe
import os
import json
import re
import subprocess
from pathlib import Path

@frappe.whitelist()
def parse_and_extract_artifacts(message_id):
    """
    Parse a Claude message and extract code artifacts
    """
    try:
        message = frappe.get_doc("Chat Message", message_id)
        content = message.message_content
        
        artifacts = extract_code_blocks(content)
        
        return {
            "success": True,
            "artifacts": artifacts
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Artifact Extraction Error")
        return {
            "success": False,
            "error": str(e)
        }


def extract_code_blocks(content):
    """
    Extract code blocks from markdown content
    """
    artifacts = []
    
    # Pattern for code blocks with file paths
    # Example: ```python:apps/myapp/myapp/module/file.py
    pattern = r'```(?:(\w+):(.+?)|(\w+))\n(.*?)```'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        language = match.group(1) or match.group(3)
        filepath = match.group(2)
        code = match.group(4).strip()
        
        if filepath:
            artifacts.append({
                "type": "file",
                "language": language,
                "filepath": filepath,
                "code": code
            })
        else:
            # Try to infer file type from code content
            inferred = infer_artifact_type(code, language)
            if inferred:
                artifacts.append(inferred)
    
    # Also look for explicit file path mentions
    file_patterns = [
        r'(?:Create|Add|Save) (?:file|this) (?:to|at|in):\s*`([^`]+)`',
        r'File(?:path)?:\s*`([^`]+)`',
        r'Save as:\s*`([^`]+)`'
    ]
    
    for pattern in file_patterns:
        for match in re.finditer(pattern, content):
            filepath = match.group(1)
            # Find the code block near this mention
            # This is a simplified approach
            artifacts.append({
                "type": "file",
                "filepath": filepath,
                "code": "",  # Would need more sophisticated extraction
                "needs_manual_review": True
            })
    
    return artifacts


def infer_artifact_type(code, language):
    """
    Infer what type of artifact this is based on code content
    """
    code_lower = code.lower()
    
    # Check for DocType JSON
    if language == "json" and '"doctype": "DocType"' in code:
        try:
            data = json.loads(code)
            if data.get("doctype") == "DocType":
                return {
                    "type": "doctype",
                    "artifact_type": "json",
                    "name": data.get("name", "Unknown"),
                    "code": code
                }
        except:
            pass
    
    # Check for Python controller
    if language == "python" and "frappe.model.document import Document" in code:
        # Try to extract class name
        class_match = re.search(r'class\s+(\w+)\(Document\)', code)
        if class_match:
            return {
                "type": "doctype",
                "artifact_type": "python",
                "name": class_match.group(1),
                "code": code
            }
    
    # Check for JavaScript
    if language in ["javascript", "js"] and "frappe.ui.form.on" in code:
        # Extract DocType name from frappe.ui.form.on('DocTypeName'
        match = re.search(r"frappe\.ui\.form\.on\(['\"](\w+)['\"]", code)
        if match:
            return {
                "type": "doctype",
                "artifact_type": "js",
                "name": match.group(1),
                "code": code
            }
    
    # Check for API function
    if language == "python" and "@frappe.whitelist()" in code:
        return {
            "type": "function",
            "artifact_type": "python",
            "code": code
        }
    
    return None


@frappe.whitelist()
def apply_artifacts(session_id, message_id, artifacts_json):
    """
    Apply extracted artifacts to the target app
    """
    try:
        artifacts = json.loads(artifacts_json)
        session = frappe.get_doc("Generation Session", session_id)
        
        if not session.target_app:
            frappe.throw("Target app not specified in session")
        
        # Get app path from settings or infer it
        app_path = get_app_path(session.target_app)
        
        if not app_path or not os.path.exists(app_path):
            frappe.throw(f"App path not found: {app_path}")
        
        results = []
        
        for artifact in artifacts:
            try:
                result = apply_single_artifact(artifact, app_path, session)
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "artifact": artifact.get("type", "unknown")
                })
        
        # Run post-apply actions
        post_apply_actions(app_path, session.target_app)
        
        # Update session with applied artifacts
        update_session_artifacts(session, results)
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Apply Artifacts Error")
        return {
            "success": False,
            "error": str(e)
        }


def apply_single_artifact(artifact, app_path, session):
    """
    Apply a single artifact
    """
    artifact_type = artifact.get("type")
    
    if artifact_type == "doctype":
        return apply_doctype_artifact(artifact, app_path, session)
    elif artifact_type == "function":
        return apply_function_artifact(artifact, app_path, session)
    elif artifact_type == "file":
        return apply_file_artifact(artifact, app_path, session)
    else:
        return {
            "success": False,
            "error": f"Unknown artifact type: {artifact_type}"
        }


def apply_doctype_artifact(artifact, app_path, session):
    """
    Apply a DocType artifact
    """
    artifact_type = artifact.get("artifact_type")  # json, python, js
    doctype_name = artifact.get("name", "Unknown")
    code = artifact.get("code")
    
    # Convert DocType name to snake_case for folder name
    folder_name = frappe.scrub(doctype_name)
    
    # Determine module (use first module or create default)
    module = get_or_create_module(app_path, session.target_app)
    module_path = os.path.join(app_path, session.target_app, module, "doctype", folder_name)
    
    # Create directory if it doesn't exist
    os.makedirs(module_path, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(module_path, "__init__.py")
    if not os.path.exists(init_file):
        Path(init_file).touch()
    
    # Write the appropriate file
    if artifact_type == "json":
        filepath = os.path.join(module_path, f"{folder_name}.json")
        with open(filepath, 'w') as f:
            # Pretty print JSON
            data = json.loads(code)
            json.dump(data, f, indent=1)
    elif artifact_type == "python":
        filepath = os.path.join(module_path, f"{folder_name}.py")
        with open(filepath, 'w') as f:
            f.write(code)
    elif artifact_type == "js":
        filepath = os.path.join(module_path, f"{folder_name}.js")
        with open(filepath, 'w') as f:
            f.write(code)
    
    return {
        "success": True,
        "type": "doctype",
        "name": doctype_name,
        "file": filepath,
        "message": f"Created {artifact_type} file for {doctype_name}"
    }


def apply_function_artifact(artifact, app_path, session):
    """
    Apply a function artifact
    """
    code = artifact.get("code")
    
    # Determine where to put the function
    # Default to api folder
    module = get_or_create_module(app_path, session.target_app)
    api_path = os.path.join(app_path, session.target_app, "api")
    
    # Create api directory if it doesn't exist
    os.makedirs(api_path, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(api_path, "__init__.py")
    if not os.path.exists(init_file):
        Path(init_file).touch()
    
    # Try to extract function name
    func_match = re.search(r'def\s+(\w+)\s*\(', code)
    func_name = func_match.group(1) if func_match else "custom_function"
    
    # Create or append to functions file
    filepath = os.path.join(api_path, f"{frappe.scrub(func_name)}.py")
    
    with open(filepath, 'w') as f:
        # Add imports if not present
        if "import frappe" not in code:
            f.write("import frappe\n\n")
        f.write(code)
    
    return {
        "success": True,
        "type": "function",
        "name": func_name,
        "file": filepath,
        "message": f"Created function {func_name}"
    }


def apply_file_artifact(artifact, app_path, session):
    """
    Apply a file artifact with explicit filepath
    """
    filepath = artifact.get("filepath")
    code = artifact.get("code")
    
    if not filepath:
        return {
            "success": False,
            "error": "No filepath specified"
        }
    
    # Make sure path is within app directory
    if not filepath.startswith(session.target_app):
        # Prepend app path
        filepath = os.path.join(session.target_app, filepath)
    
    full_path = os.path.join(app_path, "..", filepath)
    full_path = os.path.normpath(full_path)
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w') as f:
        f.write(code)
    
    return {
        "success": True,
        "type": "file",
        "file": full_path,
        "message": f"Created file at {filepath}"
    }


def get_app_path(app_name):
    """
    Get the path to the app directory
    """
    # First check settings
    settings = frappe.get_single("DevOps Settings")
    if settings.app_path and os.path.exists(settings.app_path):
        return settings.app_path
    
    # Try to find it in bench
    bench_path = frappe.utils.get_bench_path()
    app_path = os.path.join(bench_path, "apps", app_name)
    
    if os.path.exists(app_path):
        return app_path
    
    return None


def get_or_create_module(app_path, app_name):
    """
    Get existing module or create a default one
    """
    modules_file = os.path.join(app_path, app_name, "modules.txt")
    
    if os.path.exists(modules_file):
        with open(modules_file, 'r') as f:
            modules = [line.strip() for line in f.readlines() if line.strip()]
            if modules:
                # Return first module, converted to snake_case for path
                return frappe.scrub(modules[0])
    
    # Create a default module
    default_module = app_name.replace("_", " ").title()
    
    # Add to modules.txt
    with open(modules_file, 'a') as f:
        f.write(f"{default_module}\n")
    
    # Create module directory
    module_path = os.path.join(app_path, app_name, frappe.scrub(default_module))
    os.makedirs(module_path, exist_ok=True)
    
    # Create __init__.py
    Path(os.path.join(module_path, "__init__.py")).touch()
    
    # Create doctype directory
    doctype_path = os.path.join(module_path, "doctype")
    os.makedirs(doctype_path, exist_ok=True)
    Path(os.path.join(doctype_path, "__init__.py")).touch()
    
    return frappe.scrub(default_module)


def post_apply_actions(app_path, app_name):
    """
    Run necessary commands after applying artifacts
    """
    try:
        # Get bench path
        bench_path = frappe.utils.get_bench_path()
        
        # Run migrate (in background to not block)
        frappe.enqueue(
            run_bench_migrate,
            queue='long',
            timeout=300,
            app_name=app_name
        )
        
        # Clear cache
        frappe.clear_cache()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Post Apply Actions Error")


def run_bench_migrate(app_name):
    """
    Run bench migrate for the site
    """
    try:
        bench_path = frappe.utils.get_bench_path()
        site = frappe.local.site
        
        # Run migrate
        cmd = f"cd {bench_path} && bench --site {site} migrate"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            frappe.log_error(result.stderr, "Migrate Error")
        else:
            frappe.publish_realtime(
                event="migrate_complete",
                message={"status": "success", "app": app_name},
                user=frappe.session.user
            )
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Bench Migrate Error")


def update_session_artifacts(session, results):
    """
    Update session with applied artifacts information
    """
    artifacts_info = []
    
    for result in results:
        if result.get("success"):
            artifacts_info.append({
                "type": result.get("type"),
                "name": result.get("name", ""),
                "file": result.get("file", ""),
                "message": result.get("message", "")
            })
    
    current_artifacts = session.artifacts_generated or ""
    new_artifacts = "\n\n" + json.dumps(artifacts_info, indent=2)
    
    session.artifacts_generated = current_artifacts + new_artifacts
    session.save(ignore_permissions=True)


@frappe.whitelist()
def preview_artifacts(message_id):
    """
    Preview what will be applied without actually applying
    """
    try:
        message = frappe.get_doc("Chat Message", message_id)
        session = frappe.get_doc("Generation Session", message.session)
        
        artifacts = extract_code_blocks(message.message_content)
        
        previews = []
        for artifact in artifacts:
            preview = generate_preview(artifact, session)
            previews.append(preview)
        
        return {
            "success": True,
            "previews": previews
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Preview Artifacts Error")
        return {
            "success": False,
            "error": str(e)
        }


def generate_preview(artifact, session):
    """
    Generate a preview of what will be applied
    """
    artifact_type = artifact.get("type")
    
    if artifact_type == "doctype":
        name = artifact.get("name", "Unknown")
        art_type = artifact.get("artifact_type", "")
        module = "default_module"  # Simplified for preview
        
        return {
            "type": "doctype",
            "name": name,
            "description": f"Will create {art_type} file for DocType: {name}",
            "path": f"{session.target_app}/{module}/doctype/{frappe.scrub(name)}/",
            "action": "Create"
        }
    elif artifact_type == "function":
        code = artifact.get("code", "")
        func_match = re.search(r'def\s+(\w+)\s*\(', code)
        func_name = func_match.group(1) if func_match else "custom_function"
        
        return {
            "type": "function",
            "name": func_name,
            "description": f"Will create function: {func_name}",
            "path": f"{session.target_app}/api/{frappe.scrub(func_name)}.py",
            "action": "Create"
        }
    elif artifact_type == "file":
        filepath = artifact.get("filepath", "unknown")
        
        return {
            "type": "file",
            "name": os.path.basename(filepath),
            "description": f"Will create file at: {filepath}",
            "path": filepath,
            "action": "Create"
        }
    
    return {
        "type": "unknown",
        "description": "Unknown artifact type",
        "action": "Skip"
    }
