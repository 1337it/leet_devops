import frappe
import json
from anthropic import Anthropic

@frappe.whitelist()
def send_message(session_id, message, stream=True):
    """
    Send a message to Claude and get streaming response
    """
    try:
        # Get settings
        settings = frappe.get_single("DevOps Settings")
        if not settings.claude_api_key:
            frappe.throw("Claude API Key not configured")
        
        # Get session
        session = frappe.get_doc("Generation Session", session_id)
        
        # Create user message
        user_msg = frappe.get_doc({
            "doctype": "Chat Message",
            "session": session_id,
            "message_type": "User",
            "sender": frappe.session.user,
            "message_content": message
        })
        user_msg.insert(ignore_permissions=True)
        
        # Get conversation history
        messages = get_conversation_history(session_id)
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Initialize Anthropic client
        client = Anthropic(api_key=settings.get_password("claude_api_key"))
        
        # Prepare system prompt with context
        system_prompt = prepare_system_prompt(session)
        
        if stream:
            return stream_claude_response(client, messages, system_prompt, settings, session_id)
        else:
            return get_claude_response(client, messages, system_prompt, settings, session_id)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Claude API Error")
        frappe.throw(str(e))


def stream_claude_response(client, messages, system_prompt, settings, session_id):
    """
    Stream response from Claude
    """
    try:
        # Create assistant message placeholder
        assistant_msg = frappe.get_doc({
            "doctype": "Chat Message",
            "session": session_id,
            "message_type": "Assistant",
            "sender": "Claude",
            "message_content": "",
            "model_used": settings.model
        })
        assistant_msg.insert(ignore_permissions=True)
        
        full_response = ""
        
        # Stream the response
        with client.messages.stream(
            model=settings.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                # Yield for real-time streaming
                frappe.publish_realtime(
                    event="claude_response",
                    message={
                        "session_id": session_id,
                        "message_id": assistant_msg.name,
                        "content": text,
                        "done": False
                    },
                    user=frappe.session.user
                )
        
        # Update the message with full response
        assistant_msg.message_content = full_response
        assistant_msg.save(ignore_permissions=True)
        
        # Send completion signal
        frappe.publish_realtime(
            event="claude_response",
            message={
                "session_id": session_id,
                "message_id": assistant_msg.name,
                "content": full_response,
                "done": True
            },
            user=frappe.session.user
        )
        
        # Analyze response for artifacts
        analyze_and_create_child_sessions(session_id, full_response)
        
        return {"success": True, "message_id": assistant_msg.name}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Claude Streaming Error")
        raise


def get_claude_response(client, messages, system_prompt, settings, session_id):
    """
    Get non-streaming response from Claude
    """
    try:
        response = client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system_prompt,
            messages=messages
        )
        
        content = response.content[0].text
        
        # Create assistant message
        assistant_msg = frappe.get_doc({
            "doctype": "Chat Message",
            "session": session_id,
            "message_type": "Assistant",
            "sender": "Claude",
            "message_content": content,
            "model_used": settings.model,
            "token_count": response.usage.output_tokens
        })
        assistant_msg.insert(ignore_permissions=True)
        
        # Analyze response for artifacts
        analyze_and_create_child_sessions(session_id, content)
        
        return {
            "success": True,
            "message_id": assistant_msg.name,
            "content": content
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Claude API Error")
        raise


def get_conversation_history(session_id):
    """
    Get conversation history for a session
    """
    messages = frappe.get_all(
        "Chat Message",
        filters={"session": session_id},
        fields=["message_type", "message_content"],
        order_by="timestamp asc"
    )
    
    conversation = []
    for msg in messages:
        role = "user" if msg.message_type == "User" else "assistant"
        conversation.append({
            "role": role,
            "content": msg.message_content
        })
    
    return conversation


def prepare_system_prompt(session):
    """
    Prepare system prompt with session context
    """
    base_prompt = f"""You are an expert Frappe framework developer helping to generate DocTypes, functions, and other artifacts for Frappe applications.

Target App: {session.target_app}
Session Type: {session.session_type}
"""
    
    if session.session_context:
        base_prompt += f"\n\nSession Context:\n{session.session_context}"
    
    if session.parent_session:
        parent = frappe.get_doc("Generation Session", session.parent_session)
        base_prompt += f"\n\nParent Session Context:\n{parent.session_context}"
    
    base_prompt += """

When generating code:
1. Follow Frappe framework best practices
2. Generate complete, production-ready code
3. Include proper error handling
4. Add helpful comments
5. Use appropriate naming conventions

For DocTypes:
- Generate complete JSON definition
- Include Python controller
- Add JavaScript client-side code if needed
- Include validation logic

For Functions/API:
- Use @frappe.whitelist() decorator for API endpoints
- Include proper error handling
- Add docstrings
- Consider permissions

Always provide complete file paths and clear instructions for implementation.
"""
    
    return base_prompt


def analyze_and_create_child_sessions(session_id, response_content):
    """
    Analyze Claude's response and automatically create child sessions for doctypes/functions mentioned
    """
    session = frappe.get_doc("Generation Session", session_id)
    
    # Only create child sessions for main sessions
    if session.session_type != "Main":
        return
    
    # Simple keyword detection for now
    # In a production system, you might want to use more sophisticated NLP
    keywords = {
        "DocType": ["doctype", "document type", "create doctype"],
        "Function": ["function", "api endpoint", "method"],
        "Report": ["report", "create report"],
        "Page": ["page", "custom page"]
    }
    
    response_lower = response_content.lower()
    
    for session_type, triggers in keywords.items():
        for trigger in triggers:
            if trigger in response_lower:
                # Extract potential names (simplified)
                # This is a basic implementation - enhance as needed
                create_child_session_if_needed(session_id, session_type, session.target_app)
                break


def create_child_session_if_needed(parent_session_id, session_type, target_app):
    """
    Create a child session for a specific artifact type
    """
    # Check if similar child session already exists
    existing = frappe.get_all(
        "Generation Session",
        filters={
            "parent_session": parent_session_id,
            "session_type": session_type,
            "status": "Active"
        },
        limit=1
    )
    
    if not existing:
        child_session = frappe.get_doc({
            "doctype": "Generation Session",
            "title": f"{session_type} Generation",
            "target_app": target_app,
            "session_type": session_type,
            "parent_session": parent_session_id,
            "status": "Active",
            "session_context": f"This session is for generating {session_type} artifacts."
        })
        child_session.insert(ignore_permissions=True)
        frappe.db.commit()


@frappe.whitelist()
def get_session_messages(session_id):
    """
    Get all messages for a session
    """
    messages = frappe.get_all(
        "Chat Message",
        filters={"session": session_id},
        fields=["name", "message_type", "sender", "message_content", "timestamp"],
        order_by="timestamp asc"
    )
    
    return messages


@frappe.whitelist()
def create_session(title, target_app, session_type="Main", parent_session=None):
    """
    Create a new generation session
    """
    session = frappe.get_doc({
        "doctype": "Generation Session",
        "title": title,
        "target_app": target_app,
        "session_type": session_type,
        "parent_session": parent_session,
        "status": "Active"
    })
    session.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return session.name


@frappe.whitelist()
def get_child_sessions(parent_session_id):
    """
    Get all child sessions for a parent session
    """
    children = frappe.get_all(
        "Generation Session",
        filters={"parent_session": parent_session_id},
        fields=["name", "title", "session_type", "status", "modified"],
        order_by="creation asc"
    )
    
    return children
