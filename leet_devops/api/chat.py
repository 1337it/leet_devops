import frappe
import anthropic
from anthropic import Anthropic
import json

@frappe.whitelist()
def send_message(session_id, message):
    """Send a message to Claude and get a response"""
    try:
        # Get settings
        settings = frappe.get_single('Leet DevOps Settings')
        
        if not settings.claude_api_key:
            return {
                'success': False,
                'error': 'Claude API key not configured. Please configure in Leet DevOps Settings.'
            }
        
        # Create user message
        user_message = frappe.get_doc({
            'doctype': 'Dev Chat Message',
            'session': session_id,
            'message_type': 'User',
            'message': message
        })
        user_message.insert()
        
        # Get conversation history
        history = get_conversation_history(session_id)
        
        # Initialize Claude client
        api_key = settings.get_password('claude_api_key')
        client = Anthropic(api_key=api_key)
        
        # Create system prompt
        system_prompt = get_system_prompt(settings)
        
        # Call Claude API
        response = client.messages.create(
            model=settings.claude_model or "claude-sonnet-4-5-20250929",
            max_tokens=settings.max_tokens or 8096,
            temperature=settings.temperature or 0.7,
            system=system_prompt,
            messages=history
        )
        
        # Extract response
        assistant_message = response.content[0].text
        
        # Parse code changes if any
        code_changes = extract_code_changes(assistant_message, settings)
        
        # Save assistant message
        assistant_doc = frappe.get_doc({
            'doctype': 'Dev Chat Message',
            'session': session_id,
            'message_type': 'Assistant',
            'message': assistant_message
        })
        
        # Add code changes if any
        for change in code_changes:
            assistant_doc.append('code_changes', change)
        
        assistant_doc.insert()
        
        return {
            'success': True,
            'message': assistant_message,
            'message_id': assistant_doc.name,
            'code_changes': code_changes
        }
        
    except Exception as e:
        frappe.log_error(f"Chat API Error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_conversation_history(session_id):
    """Get conversation history for a session"""
    messages = frappe.get_all(
        'Dev Chat Message',
        filters={'session': session_id},
        fields=['message_type', 'message'],
        order_by='timestamp asc'
    )
    
    history = []
    for msg in messages:
        role = 'user' if msg.message_type == 'User' else 'assistant'
        history.append({
            'role': role,
            'content': msg.message
        })
    
    return history

def get_system_prompt(settings):
    """Get the system prompt for Claude"""
    bench_path = frappe.utils.get_bench_path()
    target_app = settings.target_app or 'custom_app'
    
    return f"""You are an expert Frappe/ERPNext developer assistant. You help users develop and customize their Frappe applications.

Current Context:
- Bench Path: {bench_path}
- Target App: {target_app}
- You can create, modify, and delete files in the target app
- You have access to Frappe framework documentation and best practices

Your responsibilities:
1. Help users create DocTypes, API endpoints, custom scripts, and other Frappe components
2. Provide code that follows Frappe best practices
3. When providing code changes, format them as:
   ```change
   file_path: apps/{target_app}/path/to/file.py
   change_type: create|modify|delete
   ---
   [code content here]
   ```

4. Explain your changes clearly
5. Consider security, performance, and maintainability

Guidelines:
- Always use Frappe's built-in methods and utilities
- Follow Python PEP 8 style guide
- Use proper error handling
- Add appropriate permissions and validations
- Test your suggestions mentally before providing them
- Place all code in the {target_app} app directory structure

When users ask you to make changes:
1. First explain what you'll do
2. Provide the code with proper formatting
3. Explain how to test the changes
4. Mention any dependencies or requirements
"""

def extract_code_changes(message, settings):
    """Extract code changes from assistant message"""
    changes = []
    target_app = settings.target_app or 'custom_app'
    
    # Look for code blocks with change markers
    import re
    pattern = r'```change\s+file_path:\s*(.+?)\s+change_type:\s*(create|modify|delete)\s*---\s*(.+?)```'
    matches = re.finditer(pattern, message, re.DOTALL)
    
    for match in matches:
        file_path = match.group(1).strip()
        change_type = match.group(2).strip().capitalize()
        code = match.group(3).strip()
        
        # Ensure file path uses the target app
        if not file_path.startswith('apps/'):
            file_path = f'apps/{target_app}/{file_path}'
        
        changes.append({
            'file_path': file_path,
            'change_type': change_type,
            'modified_code': code,
            'status': 'Pending'
        })
    
    return changes

@frappe.whitelist()
def test_api_connection(api_key, model):
    """Test Claude API connection"""
    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        
        return {
            'success': True,
            'message': 'Connection successful'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_messages(session_id):
    """Get all messages for a session"""
    messages = frappe.get_all(
        'Dev Chat Message',
        filters={'session': session_id},
        fields=['name', 'message_type', 'message', 'timestamp'],
        order_by='timestamp asc'
    )
    
    # Get code changes for each message separately
    for msg in messages:
        changes = frappe.get_all(
            'Code Change',
            filters={'parent': msg['name']},
            fields=['name', 'file_path', 'change_type', 'status', 'modified_code']
        )
        msg['code_changes'] = changes
    
    return messages

@frappe.whitelist()
def create_session(session_name, description=''):
    """Create a new chat session"""
    try:
        session = frappe.get_doc({
            'doctype': 'Dev Chat Session',
            'session_name': session_name,
            'description': description,
            'status': 'Active'
        })
        session.insert()
        
        return {
            'success': True,
            'session_id': session.name
        }
    except Exception as e:
        frappe.log_error(f"Error creating session: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
