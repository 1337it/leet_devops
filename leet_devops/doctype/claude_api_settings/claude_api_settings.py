# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ClaudeAPISettings(Document):
	def validate(self):
		if not self.api_key:
			frappe.throw("Claude API Key is required")
		
		if not self.app_path:
			frappe.msgprint("Please set the Apps Path for proper file operations")
