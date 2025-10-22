import frappe
from frappe.model.document import Document
import os


class ClaudeAISettings(Document):
    def validate(self):
        """Validate and set app path"""
        if self.working_app_name:
            # Get the bench path
            bench_path = frappe.utils.get_bench_path()
            app_path = os.path.join(bench_path, "apps", self.working_app_name)
            self.app_path = app_path
            
    def get_api_key(self):
        """Get decrypted API key"""
        return self.get_password("api_key")
