import frappe
from frappe.model.document import Document
import anthropic
import json


class DocTypeGenerationSession(Document):
    def send_message_to_claude(self, message):
        """Send a message to Claude specific to this DocType"""
        settings = frappe.get_single("Claude AI Settings")
        
        if not settings.api_key:
            frappe.throw("Please configure Claude API Key in Claude AI Settings")
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=settings.get_api_key())
        
        # Load existing messages
        messages = json.loads(self.messages) if self.messages else []
        
        # Add user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # System prompt specific to this DocType
        system_prompt = f"""You are an expert Frappe framework developer. You are working on a specific DocType called '{self.doctype_name}'.

Context: {self.specification}

Your role is to:
1. Help modify and refine this specific DocType
2. Answer questions about this DocType's structure
3. Suggest improvements or additional fields
4. Help troubleshoot issues with this DocType
5. Generate the complete JSON definition for this DocType

When providing code or specifications, be precise and follow Frappe framework conventions.
Always provide complete, working code that can be directly used."""
        
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
            
            # Add Claude's response to messages
            messages.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Save messages
            self.messages = json.dumps(messages)
            self.status = "In Progress"
            self.save()
            
            return response_text
            
        except Exception as e:
            frappe.log_error(f"Claude API Error: {str(e)}", "Claude API Error - DocType Session")
            frappe.throw(f"Error communicating with Claude API: {str(e)}")


@frappe.whitelist()
def send_doctype_message(parent, doctype_name, message):
    """Send a message to Claude for a specific DocType session"""
    # Get the parent App Generation Session
    parent_doc = frappe.get_doc("App Generation Session", parent)
    
    # Find the specific DocType session
    doctype_session = None
    for session in parent_doc.doctype_sessions:
        if session.doctype_name == doctype_name:
            doctype_session = session
            break
    
    if not doctype_session:
        frappe.throw(f"DocType session not found: {doctype_name}")
    
    response = doctype_session.send_message_to_claude(message)
    
    return {
        "success": True,
        "response": response
    }
