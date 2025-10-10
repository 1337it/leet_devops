import frappe

@frappe.whitelist()
def get_page_info():
    """Get page information"""
    return {
        'title': 'Dev Chat',
        'description': 'AI-powered development assistant'
    }
