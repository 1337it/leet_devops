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
    Extract code blocks from markdown content with improved parsing
    """
    artifacts = []
    
    # Pattern 1: Code blocks with file paths
    # Example: ```python:apps/myapp/myapp/module/file.py
    pattern1 = r'```(?:(\w+):(.+?))\n(.*?)```'
    matches1 = re.finditer(pattern1, content, re.DOTALL)
    
    for match in matches1:
        language = match.group(1)
        filepath = match.group(2).strip()
        code = match.group(3).strip()
        
        if code:
            artifacts.append({
                "type": "file",
                "language": language,
                "filepath": filepath,
                "code": code,
                "source": "explicit_path"
            })
    
    # Pattern 2: Standard code blocks
    pattern2 = r'```(\w+)\n(.*?)```'
    matches2 = re.finditer(pattern2, content, re.DOTALL)
    
    for match in matches2:
        language = match.group(1)
        code = match.group(2).strip()
        
        if not code:
            continue
            
        # Check if this was already captured with explicit path
        already_captured = False
        for artifact in artifacts:
            if artifact.get("code") == code:
                already_captured = True
                break
        
        if not already_captured:
            # Try to infer file type from code content
            inferred = infer_artifact_type(code, language)
            if inferred:
                artifacts.append(inferred)
    
    # Pattern 3: Look for file path mentions before code blocks
    # Example: "File: api/my_function.py" followed by code block
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Check for file path indicators
        file_indicators = [
            r'(?:File|Path|Filepath|Save (?:as|to|in)):\s*[`"]?([^\s`"]+\.\w+)[`"]?',
            r'(?:Create|Add) (?:this )?file (?:at|in|to):\s*[`"]?([^\s`"]+\.\w+)[`"]?',
        ]
        
        for indicator_pattern in file_indicators:
            match = re.search(indicator_pattern, line, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                # Look for code block after this line
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip().startswith('```'):
                        # Extract this code block
                        code_start = j + 1
                        code_end = code_start
                        for k in range(code_start, len(lines)):
                            if lines[k].strip().startswith('```'):
                                code_end = k
                                break
                        
                        code = '\n'.join(lines[code_start:code_end]).strip()
                        language = lines[j].strip()[3:].strip() or "text"
                        
                        if code:
                            artifacts.append({
                                "type": "file",
                                "language": language,
                                "filepath": filepath,
                                "code": code,
                                "source": "path_before_block"
                            })
                        break
    
    # Remove duplicates based on code content
    seen_codes = set()
    unique_artifacts = []
    for artifact in artifacts:
        code_hash = hash(artifact.get("code", ""))
        if code_hash not in seen_codes:
            seen_codes.add(code_hash)
            unique_artifacts.append(artifact)
    
    return unique_artifacts


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
        
        frappe.logger().info(f"Applying {len(artifacts)} artifacts for session {session_id}")
        
        if not session.target_app:
            frappe.throw("Target app not specified in session")
        
        # Get app path from settings or infer it
        app_path = get_app_path(session.target_app)
        
        frappe.logger().info(f"Using app path: {app_path}")
        
        if not app_path or not os.path.exists(app_path):
            frappe.throw(f"App path not found: {app_path}. Please configure it in DevOps Settings.")
        
        results = []
        
        for i, artifact in enumerate(artifacts):
            frappe.logger().info(f"Processing artifact {i+1}/{len(artifacts)}: {artifact.get('type')}")
            try:
                result = apply_single_artifact(artifact, app_path, session)
                results.append(result)
                
                # Log the result
                if result.get("success"):
                    frappe.logger().info(f"Successfully applied: {result.get('message')}")
                else:
                    frappe.logger().error(f"Failed to apply: {result.get('error')}")
                    
            except Exception as e:
                error_msg = f"Exception applying artifact: {str(e)}"
                frappe.logger().error(error_msg)
                frappe.log_error(frappe.get_traceback(), "Apply Single Artifact Error")
                results.append({
                    "success": False,
                    "error": error_msg,
                    "artifact": artifact.get("type", "unknown")
                })
        
        # Log summary
        success_count = sum(1 for r in results if r.get("success"))
        frappe.logger().info(f"Applied {success_count}/{len(results)} artifacts successfully")
        
        # Run post-apply actions
        try:
            post_apply_actions(app_path, session.target_app)
        except Exception as e:
            frappe.logger().error(f"Post-apply actions failed: {str(e)}")
        
        # Update session with applied artifacts
        try:
            update_session_artifacts(session, results)
        except Exception as e:
            frappe.logger().error(f"Failed to update session artifacts: {str(e)}")
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count
            }
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
            "error": f"Unknown artifact type: {artifact_type}",
            "artifact": artifact
        }


def apply_doctype_artifact(artifact, app_path, session):
    """
    Apply a DocType artifact with improved validation and error handling
    """
    artifact_type = artifact.get("artifact_type")  # json, python, js
    doctype_name = artifact.get("name", "Unknown")
    code = artifact.get("code")
    
    if not code or len(code.strip()) < 10:
        return {
            "success": False,
            "error": f"Code content is empty or too short for {doctype_name}",
            "type": "doctype"
        }
    
    # Convert DocType name to snake_case for folder name
    folder_name = frappe.scrub(doctype_name)
    
    # Determine module - use session's target_module if specified
    preferred_module = session.target_module if hasattr(session, 'target_module') else None
    module = get_or_create_module(app_path, session.target_app, preferred_module)
    module_path = os.path.join(app_path, session.target_app, module, "doctype", folder_name)
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(module_path, exist_ok=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create directory {module_path}: {str(e)}",
            "type": "doctype"
        }
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(module_path, "__init__.py")
    try:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("")
    except Exception as e:
        frappe.log_error(f"Failed to create __init__.py: {str(e)}")
    
    # Write the appropriate file
    filepath = None
    try:
        if artifact_type == "json":
            filepath = os.path.join(module_path, f"{folder_name}.json")
            
            # Validate JSON before writing
            try:
                data = json.loads(code)
                # Ensure it has required fields
                if "doctype" not in data or data.get("doctype") != "DocType":
                    return {
                        "success": False,
                        "error": f"Invalid DocType JSON - missing 'doctype' field",
                        "type": "doctype"
                    }
                # Set the name if not present
                if "name" not in data or not data.get("name"):
                    data["name"] = doctype_name
                # Set module if not present
                if "module" not in data or not data.get("module"):
                    data["module"] = module.replace('_', ' ').title()
                    
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=1)
                    
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON format: {str(e)}",
                    "type": "doctype"
                }
                
        elif artifact_type == "python":
            filepath = os.path.join(module_path, f"{folder_name}.py")
            
            # Add standard header if not present
            if "# Copyright" not in code and "# License" not in code:
                header = f"# Copyright (c) 2025, Leet DevOps\n# For license information, please see license.txt\n\n"
                code = header + code
            
            # Ensure imports are present
            if "import frappe" not in code:
                # Add after header/comments
                lines = code.split('\n')
                insert_at = 0
                for i, line in enumerate(lines):
                    if not line.strip().startswith('#') and line.strip():
                        insert_at = i
                        break
                lines.insert(insert_at, "import frappe\nfrom frappe.model.document import Document\n")
                code = '\n'.join(lines)
            
            with open(filepath, 'w') as f:
                f.write(code)
                
        elif artifact_type == "js":
            filepath = os.path.join(module_path, f"{folder_name}.js")
            
            # Add standard header if not present
            if "// Copyright" not in code:
                header = f"// Copyright (c) 2025, Leet DevOps\n// For license information, please see license.txt\n\n"
                code = header + code
            
            with open(filepath, 'w') as f:
                f.write(code)
        
        # Verify file was created and has content
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size < 10:
                return {
                    "success": False,
                    "error": f"File created but appears empty: {filepath}",
                    "type": "doctype"
                }
            
            return {
                "success": True,
                "type": "doctype",
                "name": doctype_name,
                "file": filepath,
                "artifact_type": artifact_type,
                "message": f"Created {artifact_type} file for {doctype_name} ({file_size} bytes)"
            }
        else:
            return {
                "success": False,
                "error": f"File was not created: {filepath}",
                "type": "doctype"
            }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Apply DocType Artifact Error")
        return {
            "success": False,
            "error": f"Exception while creating file: {str(e)}",
            "type": "doctype",
            "name": doctype_name
        }
    
    return {
        "success": False,
        "error": f"Unknown error occurred for {doctype_name}",
        "type": "doctype"
    }


def apply_function_artifact(artifact, app_path, session):
    """
    Apply a function artifact with improved validation
    """
    code = artifact.get("code")
    
    if not code or len(code.strip()) < 10:
        return {
            "success": False,
            "error": "Function code is empty or too short",
            "type": "function"
        }
    
    # Determine where to put the function
    api_path = os.path.join(app_path, session.target_app, "api")
    
    # Create api directory if it doesn't exist
    try:
        os.makedirs(api_path, exist_ok=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create api directory: {str(e)}",
            "type": "function"
        }
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(api_path, "__init__.py")
    try:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("")
    except Exception as e:
        frappe.log_error(f"Failed to create __init__.py: {str(e)}")
    
    # Try to extract function name
    func_match = re.search(r'def\s+(\w+)\s*\(', code)
    func_name = func_match.group(1) if func_match else "custom_function"
    
    # Create or append to functions file
    filepath = os.path.join(api_path, f"{frappe.scrub(func_name)}.py")
    
    try:
        # Add standard imports if not present
        if "import frappe" not in code:
            header = "import frappe\n"
            if "json" in code.lower():
                header += "import json\n"
            header += "\n"
            code = header + code
        
        # Ensure whitelist decorator is present for API functions
        if "def " in code and "@frappe.whitelist()" not in code:
            # Add decorator before function definition
            lines = code.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and i > 0:
                    # Check if previous line is already a decorator
                    if not new_lines[-1].strip().startswith('@'):
                        new_lines.append("@frappe.whitelist()")
                new_lines.append(line)
            code = '\n'.join(new_lines)
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        # Verify file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size < 10:
                return {
                    "success": False,
                    "error": f"File created but appears empty: {filepath}",
                    "type": "function"
                }
            
            return {
                "success": True,
                "type": "function",
                "name": func_name,
                "file": filepath,
                "message": f"Created function {func_name} ({file_size} bytes)"
            }
        else:
            return {
                "success": False,
                "error": f"File was not created: {filepath}",
                "type": "function"
            }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Apply Function Artifact Error")
        return {
            "success": False,
            "error": f"Failed to create function file: {str(e)}",
            "type": "function",
            "name": func_name
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


def get_or_create_module(app_path, app_name, preferred_module=None):
    """
    Get existing module or create a default one
    Improved module detection with better name handling
    """
    modules_file = os.path.join(app_path, app_name, "modules.txt")
    
    existing_modules = []
    
    if os.path.exists(modules_file):
        with open(modules_file, 'r') as f:
            modules = [line.strip() for line in f.readlines() if line.strip()]
            existing_modules = modules
            
            # If preferred module specified, use it
            if preferred_module:
                for module in modules:
                    if frappe.scrub(module).lower() == preferred_module.lower() or module.lower() == preferred_module.lower():
                        return frappe.scrub(module)
            
            # Otherwise, try to find the most appropriate module
            # Prefer modules that match the app name
            app_name_parts = app_name.replace('_', ' ').split()
            for module in modules:
                module_parts = module.lower().replace('_', ' ').split()
                if any(part in module_parts for part in app_name_parts):
                    module_path = os.path.join(app_path, app_name, frappe.scrub(module))
                    if os.path.exists(module_path):
                        return frappe.scrub(module)
            
            # Just use the first module that has a doctype folder
            for module in modules:
                module_path = os.path.join(app_path, app_name, frappe.scrub(module))
                doctype_path = os.path.join(module_path, "doctype")
                if os.path.exists(doctype_path):
                    return frappe.scrub(module)
            
            # Use first module
            if modules:
                return frappe.scrub(modules[0])
    
    # Create a default module based on app name
    # Convert app_name to proper title case
    default_module_title = app_name.replace('_', ' ').title()
    default_module_scrub = frappe.scrub(default_module_title)
    
    # Add to modules.txt
    with open(modules_file, 'a') as f:
        f.write(f"{default_module_title}\n")
    
    # Create module directory structure
    module_path = os.path.join(app_path, app_name, default_module_scrub)
    os.makedirs(module_path, exist_ok=True)
    
    # Create __init__.py
    init_file = os.path.join(module_path, "__init__.py")
    if not os.path.exists(init_file):
        Path(init_file).touch()
    
    # Create doctype directory
    doctype_path = os.path.join(module_path, "doctype")
    os.makedirs(doctype_path, exist_ok=True)
    
    doctype_init = os.path.join(doctype_path, "__init__.py")
    if not os.path.exists(doctype_init):
        Path(doctype_init).touch()
    
    frappe.msgprint(f"Created new module: {default_module_title}", alert=True)
    
    return default_module_scrub


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
    Enhanced with extraction details
    """
    try:
        message = frappe.get_doc("Chat Message", message_id)
        session = frappe.get_doc("Generation Session", message.session)
        
        artifacts = extract_code_blocks(message.message_content)
        
        frappe.logger().info(f"Extracted {len(artifacts)} artifacts from message {message_id}")
        
        previews = []
        for i, artifact in enumerate(artifacts):
            preview = generate_preview(artifact, session)
            preview["artifact_index"] = i
            preview["code_length"] = len(artifact.get("code", ""))
            preview["source"] = artifact.get("source", "unknown")
            previews.append(preview)
            
            frappe.logger().info(f"Artifact {i}: type={artifact.get('type')}, length={preview['code_length']}")
        
        return {
            "success": True,
            "previews": previews,
            "total_artifacts": len(artifacts),
            "message_length": len(message.message_content)
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
