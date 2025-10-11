import frappe
import os
import json
from leet_devops.api.app_structure_detector import detect_app_structure, get_doctype_base_path

def get_app_structure(app_name):
    """Get the structure of an app to provide context to Claude"""
    bench_path = frappe.utils.get_bench_path()
    structure_info = detect_app_structure(app_name)
    
    if not structure_info:
        return {
            'exists': False,
            'error': f'App {app_name} not found'
        }
    
    structure = {
        'exists': True,
        'app_name': app_name,
        'structure_type': structure_info['structure_type'],
        'base_module_path': structure_info['base_module_path'],
        'doctype_path': structure_info['doctype_path'],
        'page_path': structure_info['page_path'],
        'doctypes': [],
        'pages': [],
        'reports': [],
        'modules': [],
        'hooks': None
    }
    
    app_path = os.path.join(bench_path, 'apps', app_name)
    
    # Get modules
    modules_txt = os.path.join(app_path, structure_info['base_module_path'], 'modules.txt')
    if os.path.exists(modules_txt):
        with open(modules_txt, 'r') as f:
            structure['modules'] = [line.strip() for line in f if line.strip()]
    
    # Get hooks
    hooks_py = os.path.join(app_path, structure_info['base_module_path'], 'hooks.py')
    if os.path.exists(hooks_py):
        with open(hooks_py, 'r') as f:
            structure['hooks'] = f.read()[:500]
    
    # Get DocTypes
    doctype_path = os.path.join(bench_path, structure_info['doctype_path'].replace('apps/', ''))
    if os.path.exists(doctype_path):
        for item in os.listdir(doctype_path):
            item_path = os.path.join(doctype_path, item)
            if os.path.isdir(item_path):
                json_file = os.path.join(item_path, f'{item}.json')
                if os.path.exists(json_file):
                    try:
                        with open(json_file, 'r') as f:
                            doctype_data = json.load(f)
                            structure['doctypes'].append({
                                'name': doctype_data.get('name'),
                                'module': doctype_data.get('module'),
                                'folder': item,
                                'path': f"{structure_info['doctype_path']}/{item}",
                                'is_single': doctype_data.get('issingle', 0),
                                'fields_count': len(doctype_data.get('fields', []))
                            })
                    except:
                        pass
    
    # Get Pages
    page_path_full = os.path.join(bench_path, structure_info['page_path'].replace('apps/', ''))
    if os.path.exists(page_path_full):
        for item in os.listdir(page_path_full):
            item_path = os.path.join(page_path_full, item)
            if os.path.isdir(item_path):
                structure['pages'].append({
                    'name': item,
                    'path': f"{structure_info['page_path']}/{item}"
                })
    
    return structure

def get_similar_doctype_example(app_name):
    """Get an example of an existing DocType to show Claude the pattern"""
    structure = get_app_structure(app_name)
    
    if not structure['exists'] or not structure['doctypes']:
        return None
    
    # Get the first DocType as an example
    bench_path = frappe.utils.get_bench_path()
    
    for doctype in structure['doctypes'][:1]:
        doctype_folder = doctype['folder']
        doctype_base = doctype['path']
        
        json_file = os.path.join(bench_path, f"{doctype_base}/{doctype_folder}.json".replace('apps/', ''))
        py_file = os.path.join(bench_path, f"{doctype_base}/{doctype_folder}.py".replace('apps/', ''))
        
        example = {
            'name': doctype['name'],
            'folder': doctype_folder,
            'base_path': doctype_base,
            'json_structure': None,
            'py_structure': None
        }
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    example['json_structure'] = f.read()[:1000]
            except:
                pass
        
        if os.path.exists(py_file):
            try:
                with open(py_file, 'r') as f:
                    example['py_structure'] = f.read()
            except:
                pass
        
        return example
    
    return None

def check_doctype_exists(doctype_name):
    """Check if a DocType exists in the database"""
    return frappe.db.exists('DocType', doctype_name)

def get_doctype_info(doctype_name):
    """Get information about an existing DocType"""
    if not check_doctype_exists(doctype_name):
        return None
    
    try:
        doctype = frappe.get_doc('DocType', doctype_name)
        app_name = frappe.db.get_value('Module Def', doctype.module, 'app_name')
        
        # Get actual file location
        structure = detect_app_structure(app_name)
        from leet_devops.api.path_utils import to_snake_case
        folder_name = to_snake_case(doctype_name)
        
        doctype_base = f"{structure['doctype_path']}/{folder_name}"
        
        return {
            'name': doctype.name,
            'module': doctype.module,
            'app': app_name,
            'is_single': doctype.issingle,
            'is_child': doctype.istable,
            'folder_name': folder_name,
            'base_path': doctype_base,
            'json_file': f"{doctype_base}/{folder_name}.json",
            'py_file': f"{doctype_base}/{folder_name}.py",
            'js_file': f"{doctype_base}/{folder_name}.js",
            'init_file': f"{doctype_base}/__init__.py",
            'fields': [
                {
                    'fieldname': f.fieldname,
                    'fieldtype': f.fieldtype,
                    'label': f.label
                } for f in doctype.fields
            ]
        }
    except:
        return None

def get_doctype_files_from_db(doctype_name):
    """Get actual file paths for a DocType from the database"""
    return get_doctype_info(doctype_name)

@frappe.whitelist()
def get_code_context(query_type='general', item_name=None):
    """Get code context for Claude based on query type"""
    settings = frappe.get_single('Leet DevOps Settings')
    target_app = settings.target_app or 'custom_app'
    
    context = {
        'target_app': target_app,
        'app_structure': get_app_structure(target_app),
        'example_doctype': get_similar_doctype_example(target_app)
    }
    
    if query_type == 'doctype' and item_name:
        context['existing_doctype'] = get_doctype_info(item_name)
    
    return context
