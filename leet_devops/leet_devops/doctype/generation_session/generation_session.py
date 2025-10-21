# Copyright (c) 2025, Leet DevOps and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class GenerationSession(Document):
    def autoname(self):
        if not self.name:
            self.name = frappe.generate_hash(length=10)
    
    def after_insert(self):
        # If this is a child session, update parent context
        if self.parent_session:
            parent = frappe.get_doc("Generation Session", self.parent_session)
            parent.add_comment("Comment", f"Child session created: {self.title} ({self.session_type})")
