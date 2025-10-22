# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import os
import subprocess
from frappe import _

@frappe.whitelist()
def send_message_to_claude(session_name, message, doctype_session_name=None):
	"""
	Send a message to Claude API and get response
	
	Args:
		session_name: Name of the App Development Session
		message: User's message
		doctype_session_name: Optional - specific DocType Session to chat with
	"""
	try:
		# Get API settings
		settings = frappe.get_single("Claude API Settings")
		if not settings.api_key:
			return {"error": "Claude API Key not configured"}
		
		# Get session
		session = frappe.get_doc("App Development Session", session_name)
		
		# Build conversation history for Claude
		history = session.get_conversation_history()
		
		# Prepare system prompt based on context
		if doctype_session_name:
			# Get specific DocType session
			doctype_session = None
			for dt_sess in session.doctype_sessions:
				if dt_sess.doctype_name == doctype_session_name:
					doctype_session = dt_sess
					break
			
			if not doctype_session:
				return {"error": f"DocType Session {doctype_session_name} not found"}
			
			system_prompt = f"""You are a Frappe framework expert helping to develop the DocType: {doctype_session.doctype_name}.

Current DocType Definition:
{doctype_session.doctype_definition or 'Not yet defined'}

Previous conversation about this DocType:
{doctype_session.conversation_history or 'No previous conversation'}

Your role:
1. Help modify and improve this specific DocType
2. Provide the complete updated JSON definition when changes are requested
3. Explain your changes clearly
4. Consider Frappe best practices for field types, naming, and structure

Always respond with valid Frappe DocType JSON when providing definitions."""
		else:
			# Main session - app level conversation
			system_prompt = f"""You are a Frappe framework expert helping to develop a custom app called: {session.app_name}

App Description:
{session.description or 'No description yet'}

Current DocTypes in this app:
{', '.join([dt.doctype_name for dt in session.doctype_sessions]) if session.doctype_sessions else 'None yet'}

Your role:
1. Help design and architect the Frappe application
2. Create DocType definitions when requested
3. Suggest improvements and best practices
4. For each DocType, provide:
   - Complete JSON definition following Frappe standards
   - Clear explanation of the structure
   - Suggestions for related DocTypes if needed

When creating a new DocType, always provide the complete JSON definition in this format:
```json
{{
  "doctype": "DocType",
  "name": "Your DocType Name",
  "module": "Leet Devops",
  "fields": [
    // field definitions
  ],
  // other properties
}}
```

Remember:
- Use proper Frappe field types (Data, Text, Link, Select, etc.)
- Include appropriate field properties (reqd, in_list_view, etc.)
- Follow naming conventions (snake_case for fieldnames)
- Consider relationships between DocTypes"""
		
		# Prepare messages for Claude API
		messages = []
		for msg in history[-10:]:  # Last 10 messages for context
			messages.append({
				"role": msg["role"],
				"content": msg["content"]
			})
		
		# Add current message
		messages.append({
			"role": "user",
			"content": message
		})
		
		# Call Claude API
		headers = {
			"x-api-key": settings.get_password("api_key"),
			"anthropic-version": "2023-06-01",
			"content-type": "application/json"
		}
		
		payload = {
			"model": settings.model,
			"max_tokens": settings.max_tokens,
			"temperature": settings.temperature,
			"system": system_prompt,
			"messages": messages
		}
		
		# Retry logic with increased timeout
		max_retries = 3
		retry_count = 0
		last_error = None
		
		# Get timeout from settings, default to 180 seconds (3 minutes)
		api_timeout = settings.timeout if hasattr(settings, 'timeout') and settings.timeout else 180
		
		while retry_count < max_retries:
			try:
				response = requests.post(
					settings.api_endpoint,
					headers=headers,
					json=payload,
					timeout=api_timeout
				)
				
				if response.status_code != 200:
					return {
						"error": f"API Error: {response.status_code}",
						"details": response.text
					}
				
				result = response.json()
				assistant_message = result["content"][0]["text"]
				
				# Save messages to conversation history
				if doctype_session_name:
					# Update specific DocType session
					for dt_sess in session.doctype_sessions:
						if dt_sess.doctype_name == doctype_session_name:
							dt_sess.add_message("user", message)
							dt_sess.add_message("assistant", assistant_message)
							break
				else:
					# Update main session
					session.add_message("user", message)
					session.add_message("assistant", assistant_message)
				
				session.save()
				frappe.db.commit()
				
				return {
					"success": True,
					"message": assistant_message,
					"usage": result.get("usage", {})
				}
				
			except requests.exceptions.Timeout:
				retry_count += 1
				last_error = f"Request timeout (attempt {retry_count}/{max_retries})"
				frappe.log_error(f"Claude API Timeout - Attempt {retry_count}", "Claude API Timeout")
				
				if retry_count < max_retries:
					# Wait before retrying (exponential backoff)
					import time
					time.sleep(2 ** retry_count)  # 2, 4, 8 seconds
					continue
				else:
					return {
						"error": "Request timed out after multiple attempts. The API might be slow or overloaded. Please try again.",
						"details": last_error
					}
					
			except requests.exceptions.ConnectionError as e:
				return {
					"error": "Connection error. Please check your internet connection.",
					"details": str(e)
				}
				
			except requests.exceptions.RequestException as e:
				return {
					"error": "Network error occurred.",
					"details": str(e)
				}
		
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Claude API Error")
		return {
			"error": str(e),
			"traceback": frappe.get_traceback()
		}


@frappe.whitelist()
def parse_doctype_from_response(response_text):
	"""
	Parse DocType JSON definition from Claude's response
	"""
	try:
		# Try to extract JSON from code blocks
		import re
		json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
		
		if json_match:
			json_str = json_match.group(1)
			doctype_def = json.loads(json_str)
			return {
				"success": True,
				"doctype_definition": doctype_def
			}
		
		# Try direct JSON parsing
		try:
			doctype_def = json.loads(response_text)
			return {
				"success": True,
				"doctype_definition": doctype_def
			}
		except:
			pass
		
		return {
			"success": False,
			"message": "No valid JSON definition found in response"
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def create_doctype_session(session_name, doctype_name, doctype_definition=None):
	"""
	Create a new DocType session
	"""
	try:
		session = frappe.get_doc("App Development Session", session_name)
		
		# Check if DocType session already exists
		for dt_sess in session.doctype_sessions:
			if dt_sess.doctype_name == doctype_name:
				return {
					"error": f"DocType session for {doctype_name} already exists"
				}
		
		# Add new DocType session
		session.append("doctype_sessions", {
			"doctype_name": doctype_name,
			"doctype_title": doctype_name.replace("_", " ").title(),
			"status": "Draft",
			"doctype_definition": json.dumps(doctype_definition, indent=2) if doctype_definition else None
		})
		
		session.save()
		frappe.db.commit()
		
		return {
			"success": True,
			"message": f"DocType session created for {doctype_name}"
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create DocType Session Error")
		return {
			"error": str(e)
		}


@frappe.whitelist()
def apply_changes(session_name):
	"""
	Apply pending changes - create/modify files
	"""
	try:
		settings = frappe.get_single("Claude API Settings")
		session = frappe.get_doc("App Development Session", session_name)
		
		if not settings.app_path:
			return {"error": "Apps path not configured in settings"}
		
		app_path = os.path.join(settings.app_path, session.app_name)
		results = []
		
		# Update session status
		session.status = "Applying Changes"
		session.save()
		frappe.db.commit()
		
		# Process each DocType session
		for dt_sess in session.doctype_sessions:
			if not dt_sess.doctype_definition:
				continue
			
			try:
				doctype_def = json.loads(dt_sess.doctype_definition)
				doctype_name = dt_sess.doctype_name
				
				# Create DocType directory
				doctype_path = os.path.join(
					app_path,
					session.app_name,
					"doctype",
					doctype_name.lower().replace(" ", "_")
				)
				os.makedirs(doctype_path, exist_ok=True)
				
				# Create JSON file
				json_file = os.path.join(doctype_path, f"{doctype_name.lower().replace(' ', '_')}.json")
				with open(json_file, 'w') as f:
					json.dump(doctype_def, f, indent=2)
				
				# Log file creation
				frappe.get_doc({
					"doctype": "File Change Log",
					"session_reference": session_name,
					"app_name": session.app_name,
					"operation_type": "Create",
					"file_path": json_file,
					"file_type": "JSON",
					"file_content": json.dumps(doctype_def, indent=2),
					"status": "Applied"
				}).insert()
				
				# Create Python file
				py_file = os.path.join(doctype_path, f"{doctype_name.lower().replace(' ', '_')}.py")
				py_content = f"""# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class {doctype_name.replace(' ', '')}(Document):
	pass
"""
				with open(py_file, 'w') as f:
					f.write(py_content)
				
				# Log Python file
				frappe.get_doc({
					"doctype": "File Change Log",
					"session_reference": session_name,
					"app_name": session.app_name,
					"operation_type": "Create",
					"file_path": py_file,
					"file_type": "Python",
					"file_content": py_content,
					"status": "Applied"
				}).insert()
				
				# Create __init__.py
				init_file = os.path.join(doctype_path, "__init__.py")
				with open(init_file, 'w') as f:
					f.write("")
				
				dt_sess.status = "Applied"
				results.append({
					"doctype": doctype_name,
					"status": "success",
					"files": [json_file, py_file, init_file]
				})
				
			except Exception as e:
				results.append({
					"doctype": dt_sess.doctype_name,
					"status": "error",
					"error": str(e)
				})
		
		# Run bench migrate
		try:
			migrate_result = run_migrate(session.app_name)
			results.append({
				"operation": "migrate",
				"status": "success" if migrate_result["success"] else "error",
				"output": migrate_result.get("output", "")
			})
		except Exception as e:
			results.append({
				"operation": "migrate",
				"status": "error",
				"error": str(e)
			})
		
		session.status = "Completed"
		session.pending_changes = json.dumps(results, indent=2)
		session.save()
		frappe.db.commit()
		
		return {
			"success": True,
			"results": results
		}
		
	except Exception as e:
		session.status = "Error"
		session.save()
		frappe.db.commit()
		frappe.log_error(frappe.get_traceback(), "Apply Changes Error")
		return {
			"error": str(e),
			"traceback": frappe.get_traceback()
		}


@frappe.whitelist()
def verify_files(session_name):
	"""
	Verify that all expected files were created
	"""
	try:
		settings = frappe.get_single("Claude API Settings")
		session = frappe.get_doc("App Development Session", session_name)
		
		if not settings.app_path:
			return {"error": "Apps path not configured"}
		
		app_path = os.path.join(settings.app_path, session.app_name)
		verification_results = []
		
		session.verification_status = "Verifying"
		session.save()
		frappe.db.commit()
		
		for dt_sess in session.doctype_sessions:
			doctype_name = dt_sess.doctype_name.lower().replace(" ", "_")
			doctype_path = os.path.join(app_path, session.app_name, "doctype", doctype_name)
			
			expected_files = [
				os.path.join(doctype_path, f"{doctype_name}.json"),
				os.path.join(doctype_path, f"{doctype_name}.py"),
				os.path.join(doctype_path, "__init__.py")
			]
			
			doctype_result = {
				"doctype": dt_sess.doctype_name,
				"files": []
			}
			
			for file_path in expected_files:
				exists = os.path.exists(file_path)
				doctype_result["files"].append({
					"path": file_path,
					"exists": exists,
					"size": os.path.getsize(file_path) if exists else 0
				})
			
			verification_results.append(doctype_result)
		
		all_verified = all(
			all(f["exists"] for f in dr["files"])
			for dr in verification_results
		)
		
		session.verification_status = "Verified" if all_verified else "Failed"
		session.verification_details = json.dumps(verification_results, indent=2)
		session.save()
		frappe.db.commit()
		
		return {
			"success": True,
			"verified": all_verified,
			"results": verification_results
		}
		
	except Exception as e:
		session.verification_status = "Failed"
		session.save()
		frappe.db.commit()
		frappe.log_error(frappe.get_traceback(), "Verification Error")
		return {
			"error": str(e)
		}


@frappe.whitelist()
def run_migrate(app_name=None):
	"""
	Run bench migrate for the app
	"""
	try:
		cmd = ["bench", "migrate"]
		if app_name:
			cmd.extend(["--app", app_name])
		
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			timeout=300
		)
		
		return {
			"success": result.returncode == 0,
			"output": result.stdout,
			"error": result.stderr
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_app_list():
	"""
	Get list of installed Frappe apps
	"""
	try:
		settings = frappe.get_single("Claude API Settings")
		if not settings.app_path:
			return {"error": "Apps path not configured"}
		
		apps = []
		app_path = settings.app_path
		
		if os.path.exists(app_path):
			for item in os.listdir(app_path):
				item_path = os.path.join(app_path, item)
				if os.path.isdir(item_path):
					# Check if it's a Frappe app (has hooks.py)
					hooks_file = os.path.join(item_path, item, "hooks.py")
					if os.path.exists(hooks_file):
						apps.append(item)
		
		return {
			"success": True,
			"apps": apps
		}
		
	except Exception as e:
		return {
			"error": str(e)
		}
