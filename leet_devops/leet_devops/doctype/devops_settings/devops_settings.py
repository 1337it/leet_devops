# Copyright (c) 2025, Leet DevOps and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DevOpsSettings(Document):
    def validate(self):
        if self.temperature:
            if self.temperature < 0 or self.temperature > 2:
                frappe.throw("Temperature must be between 0 and 2")
