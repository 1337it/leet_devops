import frappe

def get_context(context):
    session_id = frappe.form_dict.get('session')
    if session_id:
        context.session = frappe.get_doc('Dev Chat Session', session_id)
    context.no_cache = 1
