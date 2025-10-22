# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class DocTypeSession(Document):
	def validate(self):
		if not self.doctype_title:
			self.doctype_title = self.doctype_name.replace("_", " ").title()
		
		# Count fields if doctype_definition is available
		if self.doctype_definition:
			try:
				definition = json.loads(self.doctype_definition)
				self.fields_count = len(definition.get("fields", []))
			except json.JSONDecodeError:
				pass
	
	def add_message(self, role, content):
		"""Add a message to conversation history"""
		try:
			history = json.loads(self.conversation_history) if self.conversation_history else []
		except json.JSONDecodeError:
			history = []
		
		history.append({
			"role": role,
			"content": content,
			"timestamp": frappe.utils.now()
		})
		
		self.conversation_history = json.dumps(history, indent=2)
