# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class AppDevelopmentSession(Document):
	def validate(self):
		if not self.app_title:
			self.app_title = self.app_name.replace("_", " ").title()
	
	def before_save(self):
		# Parse conversation history if it's a string
		if isinstance(self.conversation_history, str) and self.conversation_history:
			try:
				json.loads(self.conversation_history)
			except json.JSONDecodeError:
				pass  # It's plain text, keep as is
	
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
		self.save()
	
	def get_conversation_history(self):
		"""Get parsed conversation history"""
		try:
			return json.loads(self.conversation_history) if self.conversation_history else []
		except json.JSONDecodeError:
			return []
