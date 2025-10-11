import frappe
import os

def detect_app_structure(app_name):
    """Detect the actual internal structure of an app"""
    bench_path = frappe.utils.get_bench_path()
    app_path = os.path.join(bench_path, 'apps', app_name)
    
    if not os.path.exists(app_path):
        return None
    
    # Check for different possible structures
    structures = [
        # Triple nested: apps/leetrental/leetrental/leetrental/doctype
        os.path.join(app_path, app_name, app_name, 'doctype'),
        # Double nested: apps/leetrental/leetrental/doctype
        os.path.join(app_path, app_name, 'doctype'),
        # Flat: apps/leetrental/doctype (rare)
        os.path.join(app_path, 'doctype'),
    ]
    
    for doctype_path in structures:
        if os.path.exists(doctype_path):
            # Found the doctype directory
            relative_path = os.path.relpath(doctype_path, app_path)
            base_module_path = os.path.dirname(relative_path)
            
            return {
                'app_name': app_name,
                'app_path': f'apps/{app_name}',
                'base_module_path': base_module_path,
                'doctype_path': f'apps/{app_name}/{relative_path}',
                'page_path': f'apps/{app_name}/{base_module_path}/page' if base_module_path else f'apps/{app_name}/page',
                'report_path': f'apps/{app_name}/{base_module_path}/report' if base_module_path else f'apps/{app_name}/report',
                'api_path': f'apps/{app_name}/{base_module_path}/api' if base_module_path else f'apps/{app_name}/api',
                'structure_type': 'triple' if base_module_path == f'{app_name}/{app_name}' else 'double' if base_module_path == app_name else 'flat'
            }
    
    # Default to double nested (standard Frappe)
    return {
        'app_name': app_name,
        'app_path': f'apps/{app_name}',
        'base_module_path': app_name,
        'doctype_path': f'apps/{app_name}/{app_name}/doctype',
        'page_path': f'apps/{app_name}/{app_name}/page',
        'report_path': f'apps/{app_name}/{app_name}/report',
        'api_path': f'apps/{app_name}/{app_name}/api',
        'structure_type': 'double'
    }

def get_doctype_base_path(app_name, doctype_name=None):
    """Get the base path for DocTypes in an app"""
    structure = detect_app_structure(app_name)
    
    if doctype_name:
        from leet_devops.api.path_utils import to_snake_case
        folder_name = to_snake_case(doctype_name)
        return f"{structure['doctype_path']}/{folder_name}"
    
    return structure['doctype_path']

def get_page_base_path(app_name, page_name=None):
    """Get the base path for Pages in an app"""
    structure = detect_app_structure(app_name)
    
    if page_name:
        from leet_devops.api.path_utils import to_snake_case
        folder_name = to_snake_case(page_name)
        return f"{structure['page_path']}/{folder_name}"
    
    return structure['page_path']

@frappe.whitelist()
def get_app_structure_info(app_name):
    """Get detailed structure information for an app"""
    structure = detect_app_structure(app_name)
    
    if not structure:
        return {
            'success': False,
            'error': f'App {app_name} not found'
        }
    
    # Find some example DocTypes to confirm
    bench_path = frappe.utils.get_bench_path()
    doctype_path = os.path.join(bench_path, structure['doctype_path'].replace('apps/', ''))
    
    examples = []
    if os.path.exists(doctype_path):
        for item in os.listdir(doctype_path)[:3]:
            item_path = os.path.join(doctype_path, item)
            if os.path.isdir(item_path):
                examples.append(f"{structure['doctype_path']}/{item}")
    
    structure['example_paths'] = examples
    structure['success'] = True
    
    return structure

@frappe.whitelist()
def verify_app_paths(app_name):
    """Verify and display all paths for an app"""
    structure = detect_app_structure(app_name)
    bench_path = frappe.utils.get_bench_path()
    
    verification = {
        'app_name': app_name,
        'structure_type': structure['structure_type'],
        'paths': {},
        'verification': {}
    }
    
    # Check each path
    paths_to_check = {
        'DocTypes': structure['doctype_path'],
        'Pages': structure['page_path'],
        'Reports': structure['report_path'],
        'API': structure['api_path']
    }
    
    for name, path in paths_to_check.items():
        full_path = os.path.join(bench_path, path.replace('apps/', ''))
        exists = os.path.exists(full_path)
        
        verification['paths'][name] = path
        verification['verification'][name] = {
            'exists': exists,
            'full_path': full_path
        }
        
        if exists and name == 'DocTypes':
            # Count DocTypes
            count = len([d for d in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, d))])
            verification['verification'][name]['count'] = count
    
    return verification
