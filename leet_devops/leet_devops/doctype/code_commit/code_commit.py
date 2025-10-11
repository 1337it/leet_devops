import frappe
from frappe.model.document import Document

class CodeCommit(Document):
    def before_save(self):
        if not self.committed_by:
            self.committed_by = frappe.session.user
