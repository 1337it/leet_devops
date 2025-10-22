import frappe

no_cache = 1

def get_context(context):
	context.no_cache = 1
	
	# Get session name from query parameter
	session_name = frappe.form_dict.get('session')
	
	if session_name:
		try:
			session = frappe.get_doc("App Development Session", session_name)
			context.session = session
		except frappe.DoesNotExist:
			frappe.throw("Session not found")
	else:
		frappe.throw("Session parameter is required")
	
	return context
