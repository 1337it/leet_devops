import frappe
import os
import re
from leet_devops.api.app_structure_detector import detect_app_structure

def to_snake_case(name):
    """Convert any string to snake_case"""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    name = name.lower()
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

def validate_doctype_path(doctype_name, app_name):
    """Get the correct path for a DocType using actual app structure"""
    structure = detect_app_structure(app_name)
    folder_name = to_snake_case(doctype_name)
    
    base_path = f"{structure['doctype_path']}/{folder_name}"
    
    return {
        'folder_name': folder_name,
        'base_path': base_path,
        'json_file': f"{base_path}/{folder_name}.json",
        'py_file': f"{base_path}/{folder_name}.py",
        'js_file': f"{base_path}/{folder_name}.js",
        'init_file': f"{base_path}/__init__.py"
    }

def validate_page_path(page_name, app_name):
    """Get the correct path for a Page using actual app structure"""
    structure = detect_app_structure(app_name)
    folder_name = to_snake_case(page_name)
    
    base_path = f"{structure['page_path']}/{folder_name}"
    
    return {
        'folder_name': folder_name,
        'base_path': base_path,
        'json_file': f"{base_path}/{folder_name}.json",
        'py_file': f"{base_path}/{folder_name}.py",
        'js_file': f"{base_path}/{folder_name}.js",
        'init_file': f"{base_path}/__init__.py"
    }

def correct_file_path(file_path, app_name):
    """Correct a file path to use proper app structure"""
    structure = detect_app_structure(app_name)
    
    file_path = file_path.strip()
    
    # Remove any duplicate app names in the path
    # e.g. apps/leetrental/leetrental/leetrental/doctype/leetrental/pricing_plan
    # should be apps/leetrental/leetrental/leetrental/doctype/pricing_plan
    
    # Split the path
    parts = file_path.split('/')
    
    # Remove duplicate app name after doctype/page/report
    cleaned_parts = []
    skip_next = False
    
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
            
        # If this is doctype/page/report and next part is app name, skip the app name
        if part in ['doctype', 'page', 'report', 'api']:
            cleaned_parts.append(part)
            # Check if next part is the app name
            if i + 1 < len(parts) and parts[i + 1] == app_name:
                skip_next = True  # Skip the duplicate app name
        else:
            cleaned_parts.append(part)
    
    file_path = '/'.join(cleaned_parts)
    
    # Now ensure it has the correct structure base path
    if not file_path.startswith('apps/'):
        file_path = f'apps/{file_path}'
    
    # If it contains /doctype/ but doesn't start with the correct base, fix it
    if '/doctype/' in file_path:
        # Extract the part after doctype
        after_doctype = file_path.split('/doctype/')[-1]
        # Rebuild with correct structure
        file_path = f"{structure['doctype_path']}/{after_doctype}"
    elif '/page/' in file_path:
        after_page = file_path.split('/page/')[-1]
        file_path = f"{structure['page_path']}/{after_page}"
    elif '/report/' in file_path:
        after_report = file_path.split('/report/')[-1]
        file_path = f"{structure['report_path']}/{after_report}"
    
    return file_path

def check_existing_path(file_path):
    """Check if a file exists"""
    bench_path = frappe.utils.get_bench_path()
    full_path = os.path.join(bench_path, file_path.replace('apps/', ''))
    
    if os.path.exists(full_path):
        return {
            'exists': True,
            'path': file_path,
            'is_file': os.path.isfile(full_path),
            'is_dir': os.path.isdir(full_path)
        }
    
    return {
        'exists': False,
        'path': file_path
    }

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
