import frappe
from frappe.model.document import Document
import anthropic
import json
import os
import subprocess


class AppGenerationSession(Document):
    def before_save(self):
        """Update last modified timestamp"""
        self.last_modified = frappe.utils.now()
    
    def send_message_to_claude(self, message):
        """Send a message to Claude and get response"""
        settings = frappe.get_single("Claude AI Settings")
        
        if not settings.api_key:
            frappe.throw("Please configure Claude API Key in Claude AI Settings")
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=settings.get_api_key())
        
        # Add user message to chat history
        self.append("chat_messages", {
            "role": "user",
            "message": message,
            "timestamp": frappe.utils.now()
        })
        
        # Prepare conversation history
        messages = []
        for msg in self.chat_messages:
            messages.append({
                "role": msg.role,
                "content": msg.message
            })
        
        # System prompt for app generation
        system_prompt = f"""You are an expert Frappe framework developer. You are helping to create a Frappe app called '{self.app_name or settings.working_app_name}'.

Your role is to:
1. Understand the user's requirements for the Frappe app
2. Design appropriate DocTypes, fields, and relationships
3. Provide clear specifications for each DocType that needs to be created
4. Generate the necessary code and file structures
5. Explain your decisions clearly

When creating DocTypes, provide detailed specifications including:
- DocType name and description
- All fields with their types, labels, and properties
- Any child tables or relationships
- Permissions and other settings

Format your responses to clearly indicate:
- Which files need to be created
- Which files need to be modified
- The exact content for each file
- Any commands that need to be run (like bench migrate)

Use JSON format for file specifications when appropriate."""
        
        try:
            # Call Claude API
            response = client.messages.create(
                model=settings.model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Add Claude's response to chat history
            self.append("chat_messages", {
                "role": "assistant",
                "message": response_text,
                "timestamp": frappe.utils.now()
            })
            
            # Parse response for file operations and DocType specifications
            self.parse_claude_response(response_text)
            
            self.save()
            
            return response_text
            
        except Exception as e:
            frappe.log_error(f"Claude API Error: {str(e)}", "Claude API Error")
            frappe.throw(f"Error communicating with Claude API: {str(e)}")
    
    def parse_claude_response(self, response_text):
        """Parse Claude's response to identify file operations and DocTypes"""
        # This is a simplified parser - you might want to make it more sophisticated
        # Check if response mentions creating DocTypes
        if "doctype" in response_text.lower() or "create" in response_text.lower():
            self.has_pending_changes = 1
            self.pending_changes = response_text
            
            # Try to extract DocType names and create sessions
            # This is a basic implementation - enhance as needed
            lines = response_text.split('\n')
            for line in lines:
                if 'doctype' in line.lower() and ('create' in line.lower() or 'new' in line.lower()):
                    # Try to extract doctype name
                    # This is a simple heuristic - adjust based on Claude's response format
                    pass
    
    def create_doctype_session(self, doctype_name, specification):
        """Create a child session for a specific DocType"""
        # Check if session already exists
        existing = frappe.db.exists("DocType Generation Session", {
            "parent": self.name,
            "doctype_name": doctype_name
        })
        
        if not existing:
            self.append("doctype_sessions", {
                "doctype_name": doctype_name,
                "specification": specification,
                "status": "Pending"
            })
            self.save()
    
    @frappe.whitelist()
    def apply_changes(self):
        """Apply all pending changes to the file system"""
        if not self.has_pending_changes:
            frappe.throw("No pending changes to apply")
        
        settings = frappe.get_single("Claude AI Settings")
        app_path = settings.app_path
        
        if not app_path or not os.path.exists(app_path):
            frappe.throw(f"App path does not exist: {app_path}")
        
        results = []
        errors = []
        
        try:
            # Create files
            for file_op in self.files_to_create:
                try:
                    file_path = os.path.join(app_path, file_op.file_path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w') as f:
                        f.write(file_op.content)
                    
                    results.append(f"Created: {file_op.file_path}")
                    file_op.status = "Created"
                except Exception as e:
                    errors.append(f"Error creating {file_op.file_path}: {str(e)}")
                    file_op.status = "Failed"
            
            # Modify files
            for file_op in self.files_to_modify:
                try:
                    file_path = os.path.join(app_path, file_op.file_path)
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'w') as f:
                            f.write(file_op.content)
                        
                        results.append(f"Modified: {file_op.file_path}")
                        file_op.status = "Modified"
                    else:
                        errors.append(f"File not found: {file_op.file_path}")
                        file_op.status = "Failed"
                except Exception as e:
                    errors.append(f"Error modifying {file_op.file_path}: {str(e)}")
                    file_op.status = "Failed"
            
            # Run bench migrate if needed
            if results:
                try:
                    bench_path = frappe.utils.get_bench_path()
                    result = subprocess.run(
                        ["bench", "migrate"],
                        cwd=bench_path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        results.append("Migration completed successfully")
                    else:
                        errors.append(f"Migration error: {result.stderr}")
                except Exception as e:
                    errors.append(f"Error running migration: {str(e)}")
            
            # Update status
            if errors:
                self.status = "Failed"
                frappe.msgprint(f"Changes applied with errors:<br>{'<br>'.join(errors)}", indicator="orange")
            else:
                self.status = "Applied"
                self.has_pending_changes = 0
                frappe.msgprint(f"All changes applied successfully:<br>{'<br>'.join(results)}", indicator="green")
            
            self.save()
            
            return {
                "success": len(errors) == 0,
                "results": results,
                "errors": errors
            }
            
        except Exception as e:
            frappe.log_error(f"Error applying changes: {str(e)}", "Apply Changes Error")
            self.status = "Failed"
            self.save()
            frappe.throw(f"Error applying changes: {str(e)}")
    
    @frappe.whitelist()
    def verify_files(self):
        """Verify that all specified files have been created/modified"""
        settings = frappe.get_single("Claude AI Settings")
        app_path = settings.app_path
        
        verification_results = []
        
        # Check files to create
        for file_op in self.files_to_create:
            file_path = os.path.join(app_path, file_op.file_path)
            exists = os.path.exists(file_path)
            
            verification_results.append({
                "file_path": file_op.file_path,
                "operation": "Create",
                "exists": exists,
                "status": "✓" if exists else "✗"
            })
        
        # Check files to modify
        for file_op in self.files_to_modify:
            file_path = os.path.join(app_path, file_op.file_path)
            exists = os.path.exists(file_path)
            
            verification_results.append({
                "file_path": file_op.file_path,
                "operation": "Modify",
                "exists": exists,
                "status": "✓" if exists else "✗"
            })
        
        return verification_results


@frappe.whitelist()
def send_message(session_name, message):
    """Whitelisted method to send message to Claude"""
    doc = frappe.get_doc("App Generation Session", session_name)
    response = doc.send_message_to_claude(message)
    return {
        "success": True,
        "response": response
    }


@frappe.whitelist()
def create_new_session(title, app_name=None):
    """Create a new app generation session"""
    doc = frappe.get_doc({
        "doctype": "App Generation Session",
        "session_title": title,
        "app_name": app_name,
        "status": "Draft"
    })
    doc.insert()
    
    return doc.name
