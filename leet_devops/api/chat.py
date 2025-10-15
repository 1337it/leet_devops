"""
leet_devops/leet_devops/api/chat.py
Complete replacement with streaming + multi-doctype support
"""

import frappe
from anthropic import Anthropic
import json
import re
from leet_devops.api.code_inspector import (
    get_app_structure, 
    get_similar_doctype_example, 
    get_doctype_info,
    get_doctype_files_from_db
)
from leet_devops.api.path_utils import correct_file_path, to_snake_case
from leet_devops.api.app_structure_detector import detect_app_structure

# ============================================
# MULTI-DOCTYPE DETECTION & SESSION CREATION
# ============================================

def detect_doctypes_in_message(message):
    """Detect all DocTypes mentioned in the message"""
    doctypes = []
    
    # Pattern 1: create doctype "Name" or create "Name" doctype
    pattern1 = r'create\s+(?:doctype\s+["\']([^"\']+)["\']|["\']([^"\']+)["\']\s+doctype)'
    matches1 = re.finditer(pattern1, message, re.IGNORECASE)
    for match in matches1:
        name = match.group(1) or match.group(2)
        if name:
            doctypes.append({
                'name': name.strip(),
                'action': 'create'
            })
    
    # Pattern 2: Multiple doctypes in list format
    pattern2 = r'create\s+([A-Z][a-zA-Z,\s]+(?:and\s+[A-Z][a-zA-Z\s]+)?)\s+doctype'
    matches2 = re.finditer(pattern2, message, re.IGNORECASE)
    for match in matches2:
        names_str = match.group(1)
        names = re.split(r',|\s+and\s+', names_str)
        for name in names:
            clean_name = name.strip()
            if clean_name and len(clean_name) > 1:
                doctypes.append({
                    'name': clean_name,
                    'action': 'create'
                })
    
    # Pattern 3: modify/update patterns
    pattern3 = r'(modify|update|edit)\s+(?:doctype\s+["\']([^"\']+)["\']|["\']([^"\']+)["\']\s+doctype)'
    matches3 = re.finditer(pattern3, message, re.IGNORECASE)
    for match in matches3:
        name = match.group(2) or match.group(3)
        if name:
            doctypes.append({
                'name': name.strip(),
                'action': 'modify'
            })
    
    # Remove duplicates
    unique_doctypes = []
    seen = set()
    for dt in doctypes:
        key = (dt['name'].lower(), dt['action'])
        if key not in seen:
            seen.add(key)
            unique_doctypes.append(dt)
    
    return unique_doctypes

def create_doctype_session(parent_session, doctype_name, action, target_app, original_message):
    """Create a session for a specific doctype"""
    session_name = f"{doctype_name} - {action.capitalize()}"
    description = f"Auto-created from multi-doctype request. Action: {action}"
    
    session = frappe.get_doc({
        'doctype': 'Dev Chat Session',
        'session_name': session_name,
        'description': description,
        'status': 'Active',
        'parent_session': parent_session,
        'target_doctype': doctype_name,
        'action_type': action
    })
    session.insert()
    
    context_message = generate_doctype_specific_prompt(
        doctype_name, 
        action, 
        target_app, 
        original_message
    )
    
    context_doc = frappe.get_doc({
        'doctype': 'Dev Chat Message',
        'session': session.name,
        'message_type': 'System',
        'message': context_message
    })
    context_doc.insert()
    
    return session.name

def generate_doctype_specific_prompt(doctype_name, action, target_app, original_message):
    """Generate a focused prompt for a specific doctype"""
    
    if action == 'create':
        prompt = f"""Focus: Create the "{doctype_name}" DocType

Original Request Context:
{original_message}

Your Task:
Create ONLY the "{doctype_name}" DocType with:
1. Proper JSON schema definition
2. Python controller with necessary methods
3. JavaScript client-side code
4. All required files following Frappe conventions

Requirements:
- Use snake_case for folder/file names: {doctype_name.lower().replace(' ', '_')}
- Follow the app structure for {target_app}
- Include proper naming series if applicable
- Add validation and permissions
- Create __init__.py file

Do not create any other DocTypes. Focus solely on "{doctype_name}".
"""
    
    elif action == 'modify':
        doctype_info = get_doctype_info(doctype_name)
        prompt = f"""Focus: Modify the "{doctype_name}" DocType

Original Request Context:
{original_message}

Existing DocType Info:
{json.dumps(doctype_info, indent=2) if doctype_info else "DocType not found - may need to create it"}

Your Task:
Modify ONLY the "{doctype_name}" DocType based on the requirements.

Requirements:
- Keep existing functionality unless explicitly asked to change
- Make minimal, focused changes
- Ensure backward compatibility where possible
- Update only necessary files

Do not modify any other DocTypes. Focus solely on "{doctype_name}".
"""
    
    else:
        prompt = f"""Focus: {action.capitalize()} the "{doctype_name}" DocType

Original Request: {original_message}

Work only on "{doctype_name}". Do not affect other DocTypes.
"""
    
    return prompt

# ============================================
# STREAMING IMPLEMENTATION
# ============================================

@frappe.whitelist()
def send_message(session_id, message, auto_detect_doctypes=True):
    """Send message with streaming and auto multi-doctype detection"""
    try:
        settings = frappe.get_single('Leet DevOps Settings')
        
        if not settings.claude_api_key:
            return {'success': False, 'error': 'Claude API key not configured'}
        
        if not settings.target_app:
            return {'success': False, 'error': 'Target app not configured'}
        
        # Detect multiple doctypes
        if auto_detect_doctypes:
            doctypes = detect_doctypes_in_message(message)
            
            if len(doctypes) > 1:
                return handle_multi_doctype_request(
                    session_id, 
                    message, 
                    doctypes, 
                    settings
                )
        
        return send_single_message_stream(session_id, message, settings)
        
    except Exception as e:
        frappe.log_error(f"Chat API Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def handle_multi_doctype_request(parent_session, message, doctypes, settings):
    """Handle request with multiple doctypes"""
    created_sessions = []
    
    user_message = frappe.get_doc({
        'doctype': 'Dev Chat Message',
        'session': parent_session,
        'message_type': 'User',
        'message': message
    })
    user_message.insert()
    
    for dt_info in doctypes:
        session_id = create_doctype_session(
            parent_session,
            dt_info['name'],
            dt_info['action'],
            settings.target_app,
            message
        )
        
        created_sessions.append({
            'session_id': session_id,
            'doctype_name': dt_info['name'],
            'action': dt_info['action']
        })
        
        frappe.enqueue(
            'leet_devops.api.chat.process_doctype_session',
            session_id=session_id,
            settings=settings,
            queue='default',
            timeout=300
        )
    
    summary = f"""Detected {len(doctypes)} DocTypes. Created separate sessions:

{chr(10).join(f"• {dt['name']} ({dt['action']}) - Processing..." for dt in doctypes)}

Each DocType will be processed in its dedicated session. Check individual sessions for progress.
"""
    
    summary_doc = frappe.get_doc({
        'doctype': 'Dev Chat Message',
        'session': parent_session,
        'message_type': 'Assistant',
        'message': summary
    })
    summary_doc.insert()
    
    return {
        'success': True,
        'multi_doctype': True,
        'message': summary,
        'created_sessions': created_sessions
    }

def process_doctype_session(session_id, settings):
    """Background job to process a doctype session"""
    try:
        messages = frappe.get_all(
            'Dev Chat Message',
            filters={'session': session_id},
            fields=['message_type', 'message'],
            order_by='timestamp asc'
        )
        
        history = []
        system_prompt = None
        
        for msg in messages:
            if msg.message_type == 'System':
                system_prompt = msg.message
            else:
                role = 'user' if msg.message_type == 'User' else 'assistant'
                history.append({'role': role, 'content': msg.message})
        
        session = frappe.get_doc('Dev Chat Session', session_id)
        
        api_key = settings.get_password('claude_api_key')
        client = Anthropic(api_key=api_key)
        
        code_context = get_code_context_for_message(
            session.target_doctype, 
            settings.target_app
        )
        
        if not system_prompt:
            system_prompt = get_system_prompt(settings, code_context)
        
        focused_prompt = f"{system_prompt}\n\n**CRITICAL: Focus ONLY on {session.target_doctype} DocType. Do not create or modify any other DocTypes.**"
        
        stream_response(
            client,
            settings,
            focused_prompt,
            history,
            session_id
        )
        
    except Exception as e:
        frappe.log_error(f"Doctype Session Error: {str(e)}")
        frappe.publish_realtime(
            event='claude_stream',
            message={
                'session_id': session_id,
                'error': str(e),
                'done': True
            }
        )

def send_single_message_stream(session_id, message, settings):
    """Send single message with streaming"""
    user_message = frappe.get_doc({
        'doctype': 'Dev Chat Message',
        'session': session_id,
        'message_type': 'User',
        'message': message
    })
    user_message.insert()
    
    history = get_conversation_history(session_id)
    api_key = settings.get_password('claude_api_key')
    client = Anthropic(api_key=api_key)
    
    code_context = get_code_context_for_message(message, settings.target_app)
    system_prompt = get_system_prompt(settings, code_context)
    
    return stream_response(
        client,
        settings,
        system_prompt,
        history,
        session_id
    )

def stream_response(client, settings, system_prompt, history, session_id):
    """Core streaming implementation"""
    try:
        full_response = ""
        
        frappe.publish_realtime(
            event='claude_stream',
            message={
                'session_id': session_id,
                'status': 'started',
                'done': False
            },
            user=frappe.session.user
        )
        
        with client.messages.stream(
            model=settings.claude_model or "claude-sonnet-4-5-20250929",
            max_tokens=settings.max_tokens or 8096,
            temperature=settings.temperature or 0.7,
            system=system_prompt,
            messages=history
        ) as stream:
            
            for text in stream.text_stream:
                full_response += text
                
                frappe.publish_realtime(
                    event='claude_stream',
                    message={
                        'session_id': session_id,
                        'chunk': text,
                        'done': False
                    },
                    user=frappe.session.user
                )
        
        code_changes = extract_code_changes(full_response, settings)
        commands = extract_commands_from_message(full_response)
        
        for cmd in commands:
            if cmd.get('command_code') and cmd.get('command_description'):
                code_changes.append(cmd)
        
        assistant_doc = frappe.get_doc({
            'doctype': 'Dev Chat Message',
            'session': session_id,
            'message_type': 'Assistant',
            'message': full_response
        })
        
        for change in code_changes:
            assistant_doc.append('code_changes', change)
        
        assistant_doc.insert()
        
        frappe.publish_realtime(
            event='claude_stream',
            message={
                'session_id': session_id,
                'done': True,
                'message_id': assistant_doc.name,
                'code_changes': code_changes
            },
            user=frappe.session.user
        )
        
        return {
            'success': True,
            'message': full_response,
            'message_id': assistant_doc.name,
            'code_changes': code_changes,
            'streaming': True
        }
        
    except Exception as e:
        frappe.log_error(f"Streaming Error: {str(e)}")
        frappe.publish_realtime(
            event='claude_stream',
            message={
                'session_id': session_id,
                'error': str(e),
                'done': True
            },
            user=frappe.session.user
        )
        raise

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_conversation_history(session_id):
    """Get conversation history"""
    messages = frappe.get_all(
        'Dev Chat Message',
        filters={
            'session': session_id,
            'message_type': ['in', ['User', 'Assistant']]
        },
        fields=['message_type', 'message'],
        order_by='timestamp asc'
    )
    
    history = []
    for msg in messages:
        role = 'user' if msg.message_type == 'User' else 'assistant'
        history.append({'role': role, 'content': msg.message})
    
    return history

def get_code_context_for_message(message, target_app):
    """Analyze the message and gather relevant code context"""
    context = {
        'app_structure': get_app_structure(target_app),
        'example_doctype': None,
        'existing_doctype': None,
        'naming_examples': get_naming_examples(target_app)
    }
    
    example = get_similar_doctype_example(target_app)
    if example:
        context['example_doctype'] = example
    
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
    
    if doctype_name:
        doctype_info = get_doctype_info(doctype_name)
        if doctype_info:
            context['existing_doctype'] = doctype_info
            context['existing_files'] = doctype_info
    
    return context

def get_naming_examples(target_app):
    """Get examples of proper naming from the app"""
    import os
    
    bench_path = frappe.utils.get_bench_path()
    structure = detect_app_structure(target_app)
    
    examples = {
        'doctypes': [],
        'pages': [],
        'pattern': 'snake_case (all lowercase with underscores)'
    }
    
    doctype_path = os.path.join(bench_path, structure['doctype_path'].replace('apps/', ''))
    if os.path.exists(doctype_path):
        for folder in os.listdir(doctype_path)[:5]:
            if os.path.isdir(os.path.join(doctype_path, folder)):
                examples['doctypes'].append(folder)
    
    page_path = os.path.join(bench_path, structure['page_path'].replace('apps/', ''))
    if os.path.exists(page_path):
        for folder in os.listdir(page_path)[:5]:
            if os.path.isdir(os.path.join(page_path, folder)):
                examples['pages'].append(folder)
    
    return examples

def get_system_prompt(settings, code_context):
    """Get the system prompt for Claude with code context"""
    target_app = settings.target_app
    
    app_structure = code_context.get('app_structure', {})
    existing_doctype = code_context.get('existing_doctype')
    example_doctype = code_context.get('example_doctype')
    naming_examples = code_context.get('naming_examples', {})
    
    structure_type = app_structure.get('structure_type', 'double')
    doctype_base = app_structure.get('doctype_path', f'apps/{target_app}/{target_app}/doctype')
    page_base = app_structure.get('page_path', f'apps/{target_app}/{target_app}/page')
    
    naming_section = f"""
## CRITICAL: File Path Rules

**Structure Type: {structure_type}**

**EXACT PATH FORMAT:**
- DocTypes: `{doctype_base}/[folder_name]/[file]`
- Pages: `{page_base}/[folder_name]/[file]`

**Example for "Pricing Plan" DocType:**
```
{doctype_base}/pricing_plan/pricing_plan.json
{doctype_base}/pricing_plan/pricing_plan.py
{doctype_base}/pricing_plan/pricing_plan.js
{doctype_base}/pricing_plan/__init__.py
```

**NEVER add extra folders! NO {target_app}/ after doctype/**

**Examples from {target_app}:**
{chr(10).join(f"  ✓ {dt['path']}" for dt in app_structure.get('doctypes', [])[:3]) if app_structure.get('doctypes') else '  (No examples yet)'}

**snake_case only:** pricing_plan ✓ | Pricing_Plan ✗
"""
    
    app_context = f"""
## App Context

**Target: {target_app}**
**Type: {structure_type}**

**Existing DocTypes ({len(app_structure.get('doctypes', []))}):**
{chr(10).join(f"  - {dt['name']} → {dt.get('folder', 'N/A')}" for dt in app_structure.get('doctypes', [])[:8]) if app_structure.get('doctypes') else "  (None)"}
"""

    if example_doctype and example_doctype.get('py_structure'):
        app_context += f"""
**Example ({example_doctype['name']}):**
Path: {example_doctype.get('base_path', 'N/A')}
```python
{example_doctype['py_structure'][:300]}...
```
"""

    if existing_doctype:
        app_context += f"""
**Referenced DocType: {existing_doctype['name']}**
Files:
  - {existing_doctype.get('json_file', 'N/A')}
  - {existing_doctype.get('py_file', 'N/A')}
  - {existing_doctype.get('js_file', 'N/A')}
"""

    return f"""Expert Frappe developer assistant.

{naming_section}

{app_context}

## Code Change Format:

```change
file_path: {doctype_base}/[folder]/[file]
change_type: create|modify|delete
---
[content]
```

## Command Format (Optional):

```command
type: bench console
description: Clear explanation of what this does
---
import frappe
# code here
```

Types: bench console, shell, sql, python

## Rules:
1. Use EXACT paths shown above
2. NO extra {target_app}/ after doctype
3. snake_case for all names
4. Follow existing patterns
"""

def extract_code_changes(message, settings):
    """Extract code changes from assistant message"""
    changes = []
    target_app = settings.target_app
    
    pattern = r'```change\s+file_path:\s*(.+?)\s+change_type:\s*(create|modify|delete)\s*---\s*(.+?)```'
    matches = re.finditer(pattern, message, re.DOTALL)
    
    for match in matches:
        file_path = match.group(1).strip()
        change_type = match.group(2).strip().capitalize()
        code = match.group(3).strip()
        
        file_path = correct_file_path(file_path, target_app)
        
        changes.append({
            'file_path': file_path,
            'change_type': change_type,
            'modified_code': code,
            'status': 'Pending'
        })
    
    return changes

def extract_commands_from_message(message):
    """Extract command blocks from assistant message"""
    commands = []
    
    pattern = r'```command\s+type:\s*(.+?)\s+description:\s*(.+?)\s*---\s*(.+?)```'
    matches = re.finditer(pattern, message, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        command_type = match.group(1).strip()
        description = match.group(2).strip()
        code = match.group(3).strip()
        
        if not code or not description:
            continue
        
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

# ============================================
# API ENDPOINTS
# ============================================

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
    
    for msg in messages:
        changes = frappe.get_all(
            'Code Change',
            filters={'parent': msg['name']},
            fields=['name', 'file_path', 'change_type', 'status', 'modified_code', 
                    'is_command', 'command_type', 'command_description']
        )
        msg['code_changes'] = changes
    
    return messages

@frappe.whitelist()
def get_child_sessions(parent_session):
    """Get all child sessions created from multi-doctype request"""
    sessions = frappe.get_all(
        'Dev Chat Session',
        filters={'parent_session': parent_session},
        fields=['name', 'session_name', 'target_doctype', 'action_type', 'status'],
        order_by='creation asc'
    )
    return sessions

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
