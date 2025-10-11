import frappe
import anthropic
from anthropic import Anthropic
import json
from leet_devops.api.code_inspector import get_app_structure, get_similar_doctype_example, get_doctype_info
from leet_devops.api.path_utils import correct_file_path, validate_doctype_path, get_doctype_files_from_db, to_snake_case

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
        
        # Parse commands if any
        commands = extract_commands_from_message(assistant_message)
        code_changes.extend(commands)
        
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
        'existing_doctype': None,
        'naming_examples': get_naming_examples(target_app)
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
    create_pattern = r'create.*?(doctype|dt).*?["\']?([A-Z][a-zA-Z\s]+)["\']?'
    
    doctype_name = None
    
    delete_match = re.search(delete_pattern, message, re.IGNORECASE)
    if delete_match:
        doctype_name = delete_match.group(2).strip()
    
    if not doctype_name:
        modify_match = re.search(modify_pattern, message, re.IGNORECASE)
        if modify_match:
            doctype_name = modify_match.group(3).strip()
    
    if not doctype_name:
        create_match = re.search(create_pattern, message, re.IGNORECASE)
        if create_match:
            doctype_name = create_match.group(2).strip()
    
    # If we found a DocType name, get its info
    if doctype_name:
        doctype_info = get_doctype_info(doctype_name)
        if doctype_info:
            context['existing_doctype'] = doctype_info
            # Get actual file paths
            file_paths = get_doctype_files_from_db(doctype_name)
            if file_paths:
                context['existing_files'] = file_paths
    
    return context

def get_naming_examples(target_app):
    """Get examples of proper naming from the app"""
    bench_path = frappe.utils.get_bench_path()
    import os
    
    examples = {
        'doctypes': [],
        'pages': [],
        'pattern': 'snake_case (all lowercase with underscores)'
    }
    
    # Get actual DocType folder names
    doctype_path = os.path.join(bench_path, 'apps', target_app, target_app, 'doctype')
    if os.path.exists(doctype_path):
        for folder in os.listdir(doctype_path)[:5]:  # First 5 as examples
            if os.path.isdir(os.path.join(doctype_path, folder)):
                examples['doctypes'].append(folder)
    
    # Get actual Page folder names
    page_path = os.path.join(bench_path, 'apps', target_app, target_app, 'page')
    if os.path.exists(page_path):
        for folder in os.listdir(page_path)[:5]:
            if os.path.isdir(os.path.join(page_path, folder)):
                examples['pages'].append(folder)
    
    return examples

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
    existing_files = code_context.get('existing_files')
    example_doctype = code_context.get('example_doctype')
    naming_examples = code_context.get('naming_examples', {})
    
    # Build naming examples
    naming_section = f"""
## CRITICAL: File Naming Convention

**All folder and file names MUST be in snake_case (lowercase with underscores)**

**Naming Rules:**
1. DocType "Customer Feedback" → folder: `customer_feedback`
2. Files: `customer_feedback.json`, `customer_feedback.py`, `customer_feedback.js`
3. Page "Sales Dashboard" → folder: `sales_dashboard`
4. Files: `sales_dashboard.json`, `sales_dashboard.py`, `sales_dashboard.js`

**Examples from {target_app} app:**
DocType folders: {', '.join(f"`{n}`" for n in naming_examples.get('doctypes', [])) if naming_examples.get('doctypes') else 'None yet'}
Page folders: {', '.join(f"`{n}`" for n in naming_examples.get('pages', [])) if naming_examples.get('pages') else 'None yet'}

**NEVER use:**
- PascalCase: `CustomerFeedback` ❌
- camelCase: `customerFeedback` ❌
- Spaces: `customer feedback` ❌
- Mixed case: `Customer_Feedback` ❌

**ALWAYS use:**
- snake_case: `customer_feedback` ✓
"""
    
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

    # Add existing doctype/files info if user is modifying/deleting one
    if existing_doctype:
        app_context += f"""
**DocType Being Referenced: {existing_doctype['name']}**
  - Module: {existing_doctype['module']}
  - App: {existing_doctype['app']}
  - Type: {"Single" if existing_doctype['is_single'] else "Child Table" if existing_doctype['is_child'] else "Normal"}
  - Fields: {len(existing_doctype['fields'])}
"""
        
        if existing_files:
            app_context += f"""
**ACTUAL FILE PATHS (USE THESE EXACT PATHS):**
  - Folder: `{existing_files['folder_name']}`
  - JSON: `{existing_files['json_file']}`
  - Python: `{existing_files['py_file']}`
  - JavaScript: `{existing_files['js_file']}`
  - Init: `{existing_files['init_file']}`
"""

    return f"""You are an expert Frappe/ERPNext developer assistant. You help users develop and customize their Frappe applications.

{naming_section}

{app_context}

## Your Responsibilities:

1. **ALWAYS use the target app: {target_app}** - Never use custom_app
2. **CRITICAL: Use exact snake_case naming** - all lowercase with underscores
3. **Use EXACT paths shown above** for existing DocTypes
4. **Follow the existing code patterns** from the app
5. When creating new DocTypes, convert names to snake_case

## Code Change Format:

**CRITICAL: File paths must use EXACT snake_case names**

```change
file_path: apps/{target_app}/{target_app}/doctype/[folder_in_snake_case]/[filename_in_snake_case.ext]
change_type: create|modify|delete
---
[code content here]
```

## Path Examples:

**Creating "Customer Feedback" DocType:**
```
apps/{target_app}/{target_app}/doctype/customer_feedback/customer_feedback.json
apps/{target_app}/{target_app}/doctype/customer_feedback/customer_feedback.py
apps/{target_app}/{target_app}/doctype/customer_feedback/__init__.py
```

**Creating "Sales Dashboard" Page:**
```
apps/{target_app}/{target_app}/page/sales_dashboard/sales_dashboard.json
apps/{target_app}/{target_app}/page/sales_dashboard/sales_dashboard.js
```

## Guidelines:

- Convert all names to snake_case immediately
- Match existing folder names exactly (case-sensitive)
- When deleting, use the EXACT paths shown above
- Add __init__.py for new folders
- Follow Python PEP 8 and Frappe conventions
"""

def extract_code_changes(message, settings):
    """Extract code changes from assistant message and validate paths"""
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
        
        # Correct the file path
        file_path = correct_file_path(file_path, target_app)
        
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

def extract_commands_from_message(message):
    """Extract command blocks from assistant message"""
    commands = []
    
    import re
    
    # Look for command blocks
    # Format: ```command type: [type] description: [desc] --- [code] ```
    pattern = r'```command\s+type:\s*(.+?)\s+description:\s*(.+?)\s*---\s*(.+?)```'
    matches = re.finditer(pattern, message, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        command_type = match.group(1).strip()
        description = match.group(2).strip()
        code = match.group(3).strip()
        
        # Map command types
        type_mapping = {
            'console': 'Bench Console',
            'bench console': 'Bench Console',
            'shell': 'Shell Command',
            'bash': 'Shell Command',
            'sql': 'SQL Query',
            'python': 'Python Script'
        }
        
        mapped_type = type_mapping.get(command_type.lower(), 'Python Script')
        
        commands.append({
            'change_type': 'Command',
            'is_command': 1,
            'command_type': mapped_type,
            'command_code': code,
            'command_description': description,
            'status': 'Pending'
        })
    
    return commands

# Update the send_message function to also extract commands
# (Modify existing function to include commands)

# Add this to the system prompt documentation:
"""
## Command Execution Format:

For database updates, migrations, or verification commands, use:

```command
type: bench console
description: Update all DocTypes to use correct module name
---
import frappe
frappe.connect()

# Your code here
doctypes = frappe.get_all("DocType", filters={"module": "Leetrental"})
for dt in doctypes:
    doc = frappe.get_doc("DocType", dt.name)
    doc.module = "leetrental"
    doc.save()
    
frappe.db.commit()
print(f"Updated {len(doctypes)} DocTypes")
```

Command types:
- `bench console` - Python code in Frappe context
- `shell` - Shell commands (bench migrate, etc.)
- `sql` - Direct SQL queries
- `python` - Python scripts

Commands will be executed when user clicks "Apply All Changes"
"""
