import frappe
from frappe.model.document import Document

class DevChatSession(Document):
    def before_save(self):
        if not self.created_by:
            self.created_by = frappe.session.user
