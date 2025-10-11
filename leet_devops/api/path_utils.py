import frappe
import os
import re

def to_snake_case(name):
    """Convert any string to snake_case"""
    # Remove special characters except spaces and underscores
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[-\s]+', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')
    return name

def validate_doctype_path(doctype_name, app_name):
    """Get the correct path for a DocType"""
    # Convert DocType name to folder name (snake_case)
    folder_name = to_snake_case(doctype_name)
    
    # Standard DocType path structure
    base_path = f"apps/{app_name}/{app_name}/doctype/{folder_name}"
    
    return {
        'folder_name': folder_name,
        'base_path': base_path,
        'json_file': f"{base_path}/{folder_name}.json",
        'py_file': f"{base_path}/{folder_name}.py",
        'js_file': f"{base_path}/{folder_name}.js",
        'init_file': f"{base_path}/__init__.py"
    }

def validate_page_path(page_name, app_name):
    """Get the correct path for a Page"""
    folder_name = to_snake_case(page_name)
    base_path = f"apps/{app_name}/{app_name}/page/{folder_name}"
    
    return {
        'folder_name': folder_name,
        'base_path': base_path,
        'json_file': f"{base_path}/{folder_name}.json",
        'py_file': f"{base_path}/{folder_name}.py",
        'js_file': f"{base_path}/{folder_name}.js",
        'init_file': f"{base_path}/__init__.py"
    }

def check_existing_path(file_path):
    """Check if a file exists and return the actual path with correct casing"""
    bench_path = frappe.utils.get_bench_path()
    full_path = os.path.join(bench_path, file_path)
    
    if os.path.exists(full_path):
        return {
            'exists': True,
            'path': file_path,
            'is_file': os.path.isfile(full_path),
            'is_dir': os.path.isdir(full_path)
        }
    
    # Try to find case-insensitive match
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    
    if os.path.exists(directory):
        for item in os.listdir(directory):
            if item.lower() == filename.lower():
                correct_path = file_path.replace(filename, item)
                return {
                    'exists': True,
                    'path': correct_path,
                    'is_file': os.path.isfile(os.path.join(directory, item)),
                    'is_dir': os.path.isdir(os.path.join(directory, item)),
                    'corrected': True,
                    'original': file_path
                }
    
    return {
        'exists': False,
        'path': file_path
    }

def get_doctype_files_from_db(doctype_name):
    """Get actual file paths for a DocType from the database"""
    if not frappe.db.exists('DocType', doctype_name):
        return None
    
    doctype = frappe.get_doc('DocType', doctype_name)
    module_name = doctype.module
    
    # Get app name from module
    app_name = frappe.db.get_value('Module Def', module_name, 'app_name')
    
    if not app_name:
        return None
    
    # Get the actual folder name from file system
    bench_path = frappe.utils.get_bench_path()
    doctype_path = os.path.join(bench_path, 'apps', app_name, app_name, 'doctype')
    
    if not os.path.exists(doctype_path):
        return None
    
    # Find the actual folder (case-sensitive)
    actual_folder = None
    for folder in os.listdir(doctype_path):
        folder_path = os.path.join(doctype_path, folder)
        if os.path.isdir(folder_path):
            json_file = os.path.join(folder_path, f'{folder}.json')
            if os.path.exists(json_file):
                # Read the JSON to check if it's the right DocType
                try:
                    import json
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if data.get('name') == doctype_name:
                            actual_folder = folder
                            break
                except:
                    pass
    
    if not actual_folder:
        # Fallback to snake_case
        actual_folder = to_snake_case(doctype_name)
    
    return {
        'app_name': app_name,
        'module': module_name,
        'folder_name': actual_folder,
        'base_path': f"apps/{app_name}/{app_name}/doctype/{actual_folder}",
        'json_file': f"apps/{app_name}/{app_name}/doctype/{actual_folder}/{actual_folder}.json",
        'py_file': f"apps/{app_name}/{app_name}/doctype/{actual_folder}/{actual_folder}.py",
        'js_file': f"apps/{app_name}/{app_name}/doctype/{actual_folder}/{actual_folder}.js",
        'init_file': f"apps/{app_name}/{app_name}/doctype/{actual_folder}/__init__.py"
    }

def correct_file_path(file_path, app_name):
    """Correct a file path to use proper casing and structure"""
    # Normalize the path
    file_path = file_path.strip()
    
    # Ensure it starts with apps/
    if not file_path.startswith('apps/'):
        if file_path.startswith(app_name):
            file_path = f'apps/{file_path}'
        else:
            file_path = f'apps/{app_name}/{file_path}'
    
    # Parse the path
    parts = file_path.split('/')
    
    if len(parts) < 3:
        return file_path  # Can't correct, too short
    
    # Fix app name casing
    if parts[1] != app_name:
        parts[1] = app_name
    
    # If it's a doctype/page/report path
    if 'doctype' in parts or 'page' in parts or 'report' in parts:
        # Find the type index
        type_index = None
        for i, part in enumerate(parts):
            if part in ['doctype', 'page', 'report']:
                type_index = i
                break
        
        if type_index and len(parts) > type_index + 1:
            # The folder name should be snake_case
            folder_name = parts[type_index + 1]
            corrected_folder = to_snake_case(folder_name)
            parts[type_index + 1] = corrected_folder
            
            # If there's a filename, correct it too
            if len(parts) > type_index + 2:
                filename = parts[-1]
                base_name = os.path.splitext(filename)[0]
                extension = os.path.splitext(filename)[1]
                corrected_base = to_snake_case(base_name)
                parts[-1] = f"{corrected_base}{extension}"
    
    return '/'.join(parts)

@frappe.whitelist()
def validate_paths(paths):
    """Validate and correct multiple paths"""
    import json
    if isinstance(paths, str):
        paths = json.loads(paths)
    
    results = []
    for path in paths:
        check_result = check_existing_path(path)
        results.append(check_result)
    
    return results
