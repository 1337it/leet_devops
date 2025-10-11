import frappe
import anthropic
from anthropic import Anthropic
import json
from leet_devops.api.code_inspector import get_app_structure, get_similar_doctype_example, get_doctype_info

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
        
        if not settings.target_app:
            return {
                'success': False,
                'error': 'Target app not configured. Please select a target app in Leet DevOps Settings.'
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
        
        # Get code context
        code_context = get_code_context_for_message(message, settings.target_app)
        
        # Create system prompt with context
        system_prompt = get_system_prompt(settings, code_context)
        
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

def get_code_context_for_message(message, target_app):
    """Analyze the message and gather relevant code context"""
    context = {
        'app_structure': get_app_structure(target_app),
        'example_doctype': None,
        'existing_doctype': None
    }
    
    # Get an example DocType from the app to show Claude the pattern
    example = get_similar_doctype_example(target_app)
    if example:
        context['example_doctype'] = example
    
    # Check if message mentions deleting/modifying a specific DocType
    import re
    
    # Look for DocType names in the message
    delete_pattern = r'delete.*?(doctype|dt).*?["\']?([A-Z][a-zA-Z\s]+)["\']?'
    modify_pattern = r'(modify|update|change|edit).*?(doctype|dt).*?["\']?([A-Z][a-zA-Z\s]+)["\']?'
    
    doctype_name = None
    
    delete_match = re.search(delete_pattern, message, re.IGNORECASE)
    if delete_match:
        doctype_name = delete_match.group(2).strip()
    
    if not doctype_name:
        modify_match = re.search(modify_pattern, message, re.IGNORECASE)
        if modify_match:
            doctype_name = modify_match.group(3).strip()
    
    # If we found a DocType name, get its info
    if doctype_name:
        doctype_info = get_doctype_info(doctype_name)
        if doctype_info:
            context['existing_doctype'] = doctype_info
    
    return context

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

def get_system_prompt(settings, code_context):
    """Get the system prompt for Claude with code context"""
    bench_path = frappe.utils.get_bench_path()
    target_app = settings.target_app
    
    app_structure = code_context.get('app_structure', {})
    existing_doctype = code_context.get('existing_doctype')
    example_doctype = code_context.get('example_doctype')
    
    # Build context about the app
    app_context = f"""
## Current App Context

**Target App:** {target_app}
**App Path:** apps/{target_app}/{target_app}/

**Existing Modules:**
{chr(10).join(f"  - {m}" for m in app_structure.get('modules', [])) if app_structure.get('modules') else "  (No modules yet)"}

**Existing DocTypes ({len(app_structure.get('doctypes', []))}):**
{chr(10).join(f"  - {dt['name']} (Module: {dt['module']})" for dt in app_structure.get('doctypes', [])[:10]) if app_structure.get('doctypes') else "  (No DocTypes yet)"}

**Existing Pages ({len(app_structure.get('pages', []))}):**
{chr(10).join(f"  - {p}" for p in app_structure.get('pages', [])) if app_structure.get('pages') else "  (No pages yet)"}
"""

    # Add example if available
    if example_doctype and example_doctype.get('py_structure'):
        app_context += f"""
**Example DocType Pattern from this app ({example_doctype['name']}):**
```python
{example_doctype['py_structure']}
```
"""

    # Add existing doctype info if user is modifying/deleting one
    if existing_doctype:
        app_context += f"""
**DocType Being Referenced: {existing_doctype['name']}**
  - Module: {existing_doctype['module']}
  - App: {existing_doctype['app']}
  - Type: {"Single" if existing_doctype['is_single'] else "Child Table" if existing_doctype['is_child'] else "Normal"}
  - Fields: {len(existing_doctype['fields'])}
  
**Field Structure:**
{chr(10).join(f"  - {f['fieldname']} ({f['fieldtype']}): {f['label']}" for f in existing_doctype['fields'][:10])}
"""

    return f"""You are an expert Frappe/ERPNext developer assistant. You help users develop and customize their Frappe applications.

{app_context}

## Your Responsibilities:

1. **ALWAYS use the target app: {target_app}** - Never use custom_app or any other app name
2. **Follow the existing code patterns** shown in the app structure above
3. **Check existing DocTypes** before creating new ones to avoid duplicates
4. When modifying or deleting, use the exact paths and structure from the app
5. Provide code that follows Frappe best practices

## Code Change Format:

When providing code changes, use this EXACT format:

```change
file_path: apps/{target_app}/{target_app}/doctype/[doctype_folder]/[filename]
change_type: create|modify|delete
---
[code content here]
```

## Important Path Rules:

- DocTypes go in: `apps/{target_app}/{target_app}/doctype/[snake_case_name]/`
- Pages go in: `apps/{target_app}/{target_app}/page/[snake_case_name]/`
- API files go in: `apps/{target_app}/{target_app}/api/`
- Public JS go in: `apps/{target_app}/public/js/`
- Public CSS go in: `apps/{target_app}/public/css/`

## Guidelines:

- Always use Frappe's built-in methods and utilities
- Follow Python PEP 8 style guide
- Use proper error handling
- Add appropriate permissions and validations
- **Match the coding style** of existing files in the app
- When deleting DocTypes, delete ALL related files (.json, .py, .js)

## Example Workflow:

When user asks to "Delete Customer Feedback DocType":
1. Check if it exists in {target_app}
2. Identify all files: customer_feedback.json, customer_feedback.py, customer_feedback.js
3. Create delete changes for each file
4. Remind user that migration will run automatically

When creating new DocTypes:
1. Follow the pattern from existing DocTypes in the app
2. Use the same module structure
3. Place files in the correct app directory
"""

def extract_code_changes(message, settings):
    """Extract code changes from assistant message"""
    changes = []
    target_app = settings.target_app
    
    # Look for code blocks with change markers
    import re
    pattern = r'```change\s+file_path:\s*(.+?)\s+change_type:\s*(create|modify|delete)\s*---\s*(.+?)```'
    matches = re.finditer(pattern, message, re.DOTALL)
    
    for match in matches:
        file_path = match.group(1).strip()
        change_type = match.group(2).strip().capitalize()
        code = match.group(3).strip()
        
        # Ensure file path uses the correct target app
        # Replace any mention of custom_app with the actual target app
        file_path = file_path.replace('custom_app', target_app)
        
        # Ensure it starts with apps/
        if not file_path.startswith('apps/'):
            # If it starts with the app name, add apps/ prefix
            if file_path.startswith(target_app):
                file_path = f'apps/{file_path}'
            else:
                # Otherwise assume it's a relative path within the app
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
