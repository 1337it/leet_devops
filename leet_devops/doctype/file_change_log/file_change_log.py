# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import os

class FileChangeLog(Document):
	def validate(self):
		# Determine file type from extension if not set
		if not self.file_type and self.file_path:
			ext = os.path.splitext(self.file_path)[1].lower()
			type_map = {
				'.json': 'JSON',
				'.py': 'Python',
				'.js': 'JS',
				'.html': 'HTML',
				'.css': 'CSS',
				'.md': 'Markdown'
			}
			self.file_type = type_map.get(ext, 'Other')
