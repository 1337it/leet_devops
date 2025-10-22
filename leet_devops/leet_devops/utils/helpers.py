import frappe
import re
import json
import os


def parse_claude_response_for_doctypes(response_text):
    """
    Parse Claude's response to extract DocType specifications
    
    Returns: List of dictionaries with doctype_name and specification
    """
    doctypes = []
    
    # Try to find JSON blocks in the response
    json_pattern = r'```json\s*(.*?)\s*```'
    json_matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    for match in json_matches:
        try:
            data = json.loads(match)
            # Check if it's a DocType definition
            if isinstance(data, dict) and 'doctype' in data and data.get('doctype') == 'DocType':
                doctypes.append({
                    'doctype_name': data.get('name', 'Unnamed DocType'),
                    'specification': json.dumps(data, indent=2)
                })
        except json.JSONDecodeError:
            continue
    
    # Also look for explicit mentions of DocTypes
    doctype_pattern = r'(?:create|add|make)\s+(?:a\s+)?(?:doctype|DocType)\s+(?:called|named)?\s*["\']?([A-Z][A-Za-z\s]+)["\']?'
    doctype_matches = re.findall(doctype_pattern, response_text, re.IGNORECASE)
    
    for match in doctype_matches:
        doctype_name = match.strip()
        if not any(dt['doctype_name'] == doctype_name for dt in doctypes):
            doctypes.append({
                'doctype_name': doctype_name,
                'specification': f"DocType mentioned in conversation: {doctype_name}"
            })
    
    return doctypes


def parse_claude_response_for_files(response_text):
    """
    Parse Claude's response to extract file operations
    
    Returns: Dictionary with 'create' and 'modify' lists
    """
    files_to_create = []
    files_to_modify = []
    
    # Look for file path patterns
    # Pattern 1: Create file at path
    create_pattern = r'(?:create|write|save)\s+(?:file|a file)\s+(?:at|to)?\s*[:\s]+[`"\']?([\w/\-.]+)[`"\']?'
    create_matches = re.findall(create_pattern, response_text, re.IGNORECASE)
    
    for file_path in create_matches:
        files_to_create.append(file_path)
    
    # Pattern 2: Modify existing file
    modify_pattern = r'(?:modify|update|edit|change)\s+(?:file|the file)\s+[`"\']?([\w/\-.]+)[`"\']?'
    modify_matches = re.findall(modify_pattern, response_text, re.IGNORECASE)
    
    for file_path in modify_matches:
        files_to_modify.append(file_path)
    
    # Pattern 3: Code blocks with file paths as comments
    code_block_pattern = r'```(?:python|json|javascript)?\s*\n(?:#|//)\s*(?:File|Path):\s*([\w/\-.]+)\s*\n(.*?)```'
    code_matches = re.findall(code_block_pattern, response_text, re.DOTALL)
    
    for file_path, content in code_matches:
        files_to_create.append({
            'path': file_path.strip(),
            'content': content.strip()
        })
    
    return {
        'create': files_to_create,
        'modify': files_to_modify
    }


def extract_code_blocks(response_text):
    """
    Extract all code blocks from Claude's response
    
    Returns: List of dictionaries with language and content
    """
    code_blocks = []
    
    # Pattern for code blocks with language
    pattern = r'```(\w+)?\s*\n(.*?)```'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    for language, content in matches:
        code_blocks.append({
            'language': language or 'text',
            'content': content.strip()
        })
    
    return code_blocks


def create_doctype_file_structure(doctype_name, doctype_json, app_path):
    """
    Create the file structure for a DocType
    
    Args:
        doctype_name: Name of the DocType
        doctype_json: JSON definition of the DocType
        app_path: Path to the app
    
    Returns: List of file operations
    """
    operations = []
    
    # Convert doctype name to snake_case for directory
    dir_name = frappe.scrub(doctype_name)
    doctype_path = os.path.join(app_path, frappe.scrub(frappe.local.site.split('.')[0]), 
                                 "doctype", dir_name)
    
    # JSON file
    operations.append({
        'path': f"{dir_name}/{dir_name}.json",
        'content': json.dumps(doctype_json, indent=1),
        'operation': 'create'
    })
    
    # Python file
    python_content = f"""import frappe
from frappe.model.document import Document


class {doctype_name.replace(' ', '')}(Document):
    pass
"""
    
    operations.append({
        'path': f"{dir_name}/{dir_name}.py",
        'content': python_content,
        'operation': 'create'
    })
    
    # __init__.py
    operations.append({
        'path': f"{dir_name}/__init__.py",
        'content': "# Empty init file\n",
        'operation': 'create'
    })
    
    return operations


def validate_doctype_json(doctype_json):
    """
    Validate a DocType JSON definition
    
    Returns: Tuple (is_valid, error_message)
    """
    try:
        if not isinstance(doctype_json, dict):
            return False, "DocType definition must be a dictionary"
        
        required_fields = ['doctype', 'name', 'module']
        for field in required_fields:
            if field not in doctype_json:
                return False, f"Missing required field: {field}"
        
        if doctype_json.get('doctype') != 'DocType':
            return False, "The 'doctype' field must be 'DocType'"
        
        if 'fields' in doctype_json:
            if not isinstance(doctype_json['fields'], list):
                return False, "Fields must be a list"
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def get_app_info(app_name):
    """
    Get information about an app
    
    Returns: Dictionary with app information
    """
    bench_path = frappe.utils.get_bench_path()
    app_path = os.path.join(bench_path, "apps", app_name)
    
    if not os.path.exists(app_path):
        return None
    
    info = {
        'name': app_name,
        'path': app_path,
        'exists': True
    }
    
    # Try to read hooks.py for more info
    hooks_path = os.path.join(app_path, app_name, "hooks.py")
    if os.path.exists(hooks_path):
        try:
            with open(hooks_path, 'r') as f:
                hooks_content = f.read()
                
            # Extract app_title
            title_match = re.search(r'app_title\s*=\s*["\']([^"\']+)["\']', hooks_content)
            if title_match:
                info['title'] = title_match.group(1)
            
            # Extract app_description
            desc_match = re.search(r'app_description\s*=\s*["\']([^"\']+)["\']', hooks_content)
            if desc_match:
                info['description'] = desc_match.group(1)
                
        except Exception:
            pass
    
    return info


def format_file_path(file_path, app_name):
    """
    Format a file path to be relative to the app
    
    Args:
        file_path: The file path (can be absolute or relative)
        app_name: Name of the app
    
    Returns: Formatted relative path
    """
    # Remove leading slashes
    file_path = file_path.lstrip('/')
    
    # If path doesn't start with app name, prepend it
    if not file_path.startswith(app_name):
        file_path = f"{app_name}/{file_path}"
    
    return file_path


def safe_write_file(file_path, content, app_path):
    """
    Safely write content to a file, creating directories as needed
    
    Args:
        file_path: Relative path within the app
        content: Content to write
        app_path: Base app path
    
    Returns: Tuple (success, message)
    """
    try:
        full_path = os.path.join(app_path, file_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"Successfully wrote to {file_path}"
        
    except Exception as e:
        return False, f"Error writing to {file_path}: {str(e)}"


def check_file_exists(file_path, app_path):
    """
    Check if a file exists in the app
    
    Args:
        file_path: Relative path within the app
        app_path: Base app path
    
    Returns: Boolean
    """
    full_path = os.path.join(app_path, file_path)
    return os.path.exists(full_path)
