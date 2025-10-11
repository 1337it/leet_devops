import frappe
import os
import json

def get_app_structure(app_name):
    """Get the structure of an app to provide context to Claude"""
    bench_path = frappe.utils.get_bench_path()
    app_path = os.path.join(bench_path, 'apps', app_name)
    
    if not os.path.exists(app_path):
        return {
            'exists': False,
            'error': f'App {app_name} not found'
        }
    
    structure = {
        'exists': True,
        'app_name': app_name,
        'doctypes': [],
        'pages': [],
        'reports': [],
        'modules': [],
        'hooks': None
    }
    
    # Get modules
    modules_txt = os.path.join(app_path, app_name, 'modules.txt')
    if os.path.exists(modules_txt):
        with open(modules_txt, 'r') as f:
            structure['modules'] = [line.strip() for line in f if line.strip()]
    
    # Get hooks
    hooks_py = os.path.join(app_path, app_name, 'hooks.py')
    if os.path.exists(hooks_py):
        with open(hooks_py, 'r') as f:
            structure['hooks'] = f.read()[:500]  # First 500 chars
    
    # Get DocTypes
    doctype_path = os.path.join(app_path, app_name, app_name, 'doctype')
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
                                'is_single': doctype_data.get('issingle', 0),
                                'fields_count': len(doctype_data.get('fields', []))
                            })
                    except:
                        pass
    
    # Get Pages
    page_path = os.path.join(app_path, app_name, app_name, 'page')
    if os.path.exists(page_path):
        for item in os.listdir(page_path):
            item_path = os.path.join(page_path, item)
            if os.path.isdir(item_path):
                structure['pages'].append(item)
    
    # Get Reports
    report_path = os.path.join(app_path, app_name, app_name, 'report')
    if os.path.exists(report_path):
        for item in os.listdir(report_path):
            item_path = os.path.join(report_path, item)
            if os.path.isdir(item_path):
                structure['reports'].append(item)
    
    return structure

def get_similar_doctype_example(app_name):
    """Get an example of an existing DocType to show Claude the pattern"""
    structure = get_app_structure(app_name)
    
    if not structure['exists'] or not structure['doctypes']:
        return None
    
    # Get the first DocType as an example
    bench_path = frappe.utils.get_bench_path()
    app_path = os.path.join(bench_path, 'apps', app_name)
    
    for doctype in structure['doctypes'][:1]:  # Just get one example
        doctype_name = doctype['name']
        doctype_folder = doctype_name.lower().replace(' ', '_')
        json_file = os.path.join(app_path, app_name, app_name, 'doctype', doctype_folder, f'{doctype_folder}.json')
        py_file = os.path.join(app_path, app_name, app_name, 'doctype', doctype_folder, f'{doctype_folder}.py')
        
        example = {
            'name': doctype_name,
            'json_structure': None,
            'py_structure': None
        }
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    example['json_structure'] = f.read()[:1000]  # First 1000 chars
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
        return {
            'name': doctype.name,
            'module': doctype.module,
            'app': frappe.db.get_value('Module Def', doctype.module, 'app_name'),
            'is_single': doctype.issingle,
            'is_child': doctype.istable,
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
    
    # If asking about a specific DocType, get its info
    if query_type == 'doctype' and item_name:
        context['existing_doctype'] = get_doctype_info(item_name)
    
    return context
