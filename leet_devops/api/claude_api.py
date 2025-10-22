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
def scan_and_create_doctype_sessions(session_name):
	"""
	Scan conversation history and create DocType sessions for all found definitions
	"""
	try:
		session = frappe.get_doc("App Development Session", session_name)
		
		# Get conversation history
		try:
			history = json.loads(session.conversation_history) if session.conversation_history else []
		except:
			history = []
		
		# Track existing DocType sessions
		existing_doctypes = [dt.doctype_name for dt in session.doctype_sessions]
		
		# Scan for DocType definitions in conversation
		found_doctypes = []
		created_count = 0
		
		for msg in history:
			if msg.get("role") == "assistant":
				content = msg.get("content", "")
				
				# Look for JSON code blocks
				import re
				json_blocks = re.findall(r'```json\s*([\s\S]*?)```', content)
				
				for json_str in json_blocks:
					try:
						definition = json.loads(json_str)
						
						# Check if it's a DocType definition
						if isinstance(definition, dict) and definition.get("doctype") == "DocType" and definition.get("name"):
							doctype_name = definition["name"]
							
							# Check if not already exists
							if doctype_name not in existing_doctypes and doctype_name not in found_doctypes:
								found_doctypes.append(doctype_name)
								
								# Create session
								session.append("doctype_sessions", {
									"doctype_name": doctype_name,
									"doctype_title": doctype_name.replace("_", " ").title(),
									"status": "Draft",
									"doctype_definition": json.dumps(definition, indent=2)
								})
								
								created_count += 1
					except:
						continue
		
		if created_count > 0:
			session.save()
			frappe.db.commit()
			
			return {
				"success": True,
				"created": created_count,
				"doctypes": found_doctypes,
				"message": f"Created {created_count} DocType session(s): {', '.join(found_doctypes)}"
			}
		else:
			return {
				"success": True,
				"created": 0,
				"message": "No new DocType definitions found in conversation history"
			}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Scan DocType Sessions Error")
		return {
			"error": str(e),
			"traceback": frappe.get_traceback()
		}


@frappe.whitelist()
def create_complete_app_structure(session_name):
	"""
	Create complete Frappe app structure with all necessary files
	"""
	try:
		settings = frappe.get_single("Claude API Settings")
		session = frappe.get_doc("App Development Session", session_name)
		
		if not settings.app_path:
			return {"error": "Apps path not configured in settings"}
		
		app_path = os.path.join(settings.app_path, session.app_name)
		app_module_path = os.path.join(app_path, session.app_name)
		
		results = []
		
		# Create base app directory
		os.makedirs(app_path, exist_ok=True)
		os.makedirs(app_module_path, exist_ok=True)
		
		# 1. Create __init__.py
		init_content = f"__version__ = '0.0.1'"
		init_file = os.path.join(app_module_path, "__init__.py")
		with open(init_file, 'w') as f:
			f.write(init_content)
		results.append({"file": "__init__.py", "status": "created"})
		
		# 2. Create hooks.py
		hooks_content = f"""from . import __version__ as app_version

app_name = "{session.app_name}"
app_title = "{session.app_title or session.app_name.replace('_', ' ').title()}"
app_publisher = "Your Company"
app_description = "{session.description or 'Custom Frappe Application'}"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "your@email.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/{session.app_name}/css/{session.app_name}.css"
# app_include_js = "/assets/{session.app_name}/js/{session.app_name}.js"

# include js, css files in header of web template
# web_include_css = "/assets/{session.app_name}/css/{session.app_name}.css"
# web_include_js = "/assets/{session.app_name}/js/{session.app_name}.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "{session.app_name}/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {{"doctype": "public/js/doctype.js"}}
# webform_include_css = {{"doctype": "public/css/doctype.css"}}

# include js in page
# page_js = {{"page" : "public/js/file.js"}}

# include js in doctype views
# doctype_js = {{"doctype" : "public/js/doctype.js"}}
# doctype_list_js = {{"doctype" : "public/js/doctype_list.js"}}
# doctype_tree_js = {{"doctype" : "public/js/doctype_tree.js"}}
# doctype_calendar_js = {{"doctype" : "public/js/doctype_calendar.js"}}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {{
#	"Role": "home_page"
# }}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {{
# 	"methods": "{session.app_name}.utils.jinja_methods",
# 	"filters": "{session.app_name}.utils.jinja_filters"
# }}

# Installation
# ------------

# before_install = "{session.app_name}.install.before_install"
# after_install = "{session.app_name}.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "{session.app_name}.uninstall.before_uninstall"
# after_uninstall = "{session.app_name}.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "{session.app_name}.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {{
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }}
#
# has_permission = {{
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {{
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {{
# 	"*": {{
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}}
# }}

# Scheduled Tasks
# ---------------

# scheduler_events = {{
# 	"all": [
# 		"{session.app_name}.tasks.all"
# 	],
# 	"daily": [
# 		"{session.app_name}.tasks.daily"
# 	],
# 	"hourly": [
# 		"{session.app_name}.tasks.hourly"
# 	],
# 	"weekly": [
# 		"{session.app_name}.tasks.weekly"
# 	]
# 	"monthly": [
# 		"{session.app_name}.tasks.monthly"
# 	]
# }}

# Testing
# -------

# before_tests = "{session.app_name}.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {{
# 	"frappe.desk.doctype.event.event.get_events": "{session.app_name}.event.get_events"
# }}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {{
# 	"Task": "{session.app_name}.task.get_dashboard_data"
# }}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]
"""
		hooks_file = os.path.join(app_module_path, "hooks.py")
		with open(hooks_file, 'w') as f:
			f.write(hooks_content)
		results.append({"file": "hooks.py", "status": "created"})
		
		# 3. Create modules.txt
		module_name = session.app_name.replace("_", " ").title()
		modules_file = os.path.join(app_module_path, "modules.txt")
		with open(modules_file, 'w') as f:
			f.write(module_name)
		results.append({"file": "modules.txt", "status": "created"})
		
		# 4. Create patches.txt
		patches_file = os.path.join(app_module_path, "patches.txt")
		with open(patches_file, 'w') as f:
			f.write("")
		results.append({"file": "patches.txt", "status": "created"})
		
		# 5. Create config directory structure
		config_dir = os.path.join(app_module_path, "config")
		os.makedirs(config_dir, exist_ok=True)
		
		# config/__init__.py
		with open(os.path.join(config_dir, "__init__.py"), 'w') as f:
			f.write("")
		
		# config/desktop.py
		desktop_content = f"""from frappe import _

def get_data():
	return [
		{{
			"module_name": "{module_name}",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("{module_name}")
		}}
	]
"""
		with open(os.path.join(config_dir, "desktop.py"), 'w') as f:
			f.write(desktop_content)
		
		# config/docs.py
		with open(os.path.join(config_dir, "docs.py"), 'w') as f:
			f.write("# Documentation Configuration\n")
		
		results.append({"file": "config/", "status": "created"})
		
		# 6. Create public directory structure
		public_dir = os.path.join(app_module_path, "public")
		os.makedirs(os.path.join(public_dir, "css"), exist_ok=True)
		os.makedirs(os.path.join(public_dir, "js"), exist_ok=True)
		os.makedirs(os.path.join(public_dir, "images"), exist_ok=True)
		
		# public/build.json
		with open(os.path.join(public_dir, "build.json"), 'w') as f:
			f.write("{}")
		
		# public/css/[app].css
		with open(os.path.join(public_dir, "css", f"{session.app_name}.css"), 'w') as f:
			f.write(f"/* {session.app_name} CSS */\n")
		
		# public/js/[app].js
		with open(os.path.join(public_dir, "js", f"{session.app_name}.js"), 'w') as f:
			f.write(f"// {session.app_name} JavaScript\n")
		
		results.append({"file": "public/", "status": "created"})
		
		# 7. Create templates directory structure
		templates_dir = os.path.join(app_module_path, "templates")
		os.makedirs(templates_dir, exist_ok=True)
		os.makedirs(os.path.join(templates_dir, "includes"), exist_ok=True)
		os.makedirs(os.path.join(templates_dir, "pages"), exist_ok=True)
		os.makedirs(os.path.join(templates_dir, "generators"), exist_ok=True)
		
		with open(os.path.join(templates_dir, "__init__.py"), 'w') as f:
			f.write("")
		
		results.append({"file": "templates/", "status": "created"})
		
		# 8. Create www directory
		www_dir = os.path.join(app_module_path, "www")
		os.makedirs(www_dir, exist_ok=True)
		
		index_content = """<!DOCTYPE html>
<html>
<head>
	<title>Welcome</title>
</head>
<body>
	<h1>Welcome to Your App</h1>
</body>
</html>
"""
		with open(os.path.join(www_dir, "index.html"), 'w') as f:
			f.write(index_content)
		
		results.append({"file": "www/", "status": "created"})
		
		# 9. Create translations directory
		translations_dir = os.path.join(app_module_path, "translations")
		os.makedirs(translations_dir, exist_ok=True)
		results.append({"file": "translations/", "status": "created"})
		
		# 10. Create module directory
		module_dir = os.path.join(app_module_path, module_name.lower().replace(" ", "_"))
		os.makedirs(module_dir, exist_ok=True)
		os.makedirs(os.path.join(module_dir, "doctype"), exist_ok=True)
		os.makedirs(os.path.join(module_dir, "page"), exist_ok=True)
		os.makedirs(os.path.join(module_dir, "report"), exist_ok=True)
		os.makedirs(os.path.join(module_dir, "web_form"), exist_ok=True)
		
		with open(os.path.join(module_dir, "__init__.py"), 'w') as f:
			f.write("")
		
		results.append({"file": f"{module_name.lower().replace(' ', '_')}/", "status": "created"})
		
		# 11. Create api directory
		api_dir = os.path.join(app_module_path, "api")
		os.makedirs(api_dir, exist_ok=True)
		
		with open(os.path.join(api_dir, "__init__.py"), 'w') as f:
			f.write("")
		
		results.append({"file": "api/", "status": "created"})
		
		# 12. Create tasks.py
		tasks_content = f"""# {session.app_name} background tasks

# Scheduled tasks
def all():
	pass

def daily():
	pass

def hourly():
	pass

def weekly():
	pass

def monthly():
	pass
"""
		with open(os.path.join(app_module_path, "tasks.py"), 'w') as f:
			f.write(tasks_content)
		results.append({"file": "tasks.py", "status": "created"})
		
		# 13. Create root level files
		
		# requirements.txt
		requirements = """frappe
"""
		with open(os.path.join(app_path, "requirements.txt"), 'w') as f:
			f.write(requirements)
		results.append({"file": "requirements.txt", "status": "created"})
		
		# setup.py
		setup_content = f"""from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\\n")

from {session.app_name} import __version__ as version

setup(
	name="{session.app_name}",
	version=version,
	description="{session.description or 'Custom Frappe Application'}",
	author="Your Company",
	author_email="your@email.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
"""
		with open(os.path.join(app_path, "setup.py"), 'w') as f:
			f.write(setup_content)
		results.append({"file": "setup.py", "status": "created"})
		
		# license.txt
		license_content = """MIT License

Copyright (c) 2025 Your Company

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
		with open(os.path.join(app_path, "license.txt"), 'w') as f:
			f.write(license_content)
		results.append({"file": "license.txt", "status": "created"})
		
		# README.md
		readme_content = f"""# {session.app_title or session.app_name}

{session.description or 'Custom Frappe Application'}

## Installation

```bash
bench get-app {session.app_name}
bench --site [site-name] install-app {session.app_name}
```

## License

MIT
"""
		with open(os.path.join(app_path, "README.md"), 'w') as f:
			f.write(readme_content)
		results.append({"file": "README.md", "status": "created"})
		
		# .gitignore
		gitignore_content = """*.pyc
*.egg-info
*.swp
*.swo
.DS_Store
__pycache__
*.db
*.sqlite3
node_modules/
dist/
build/
"""
		with open(os.path.join(app_path, ".gitignore"), 'w') as f:
			f.write(gitignore_content)
		results.append({"file": ".gitignore", "status": "created"})
		
		# MANIFEST.in
		manifest_content = f"""include MANIFEST.in
include requirements.txt
include *.json
include *.md
include *.py
include *.txt
recursive-include {session.app_name} *.css
recursive-include {session.app_name} *.csv
recursive-include {session.app_name} *.html
recursive-include {session.app_name} *.ico
recursive-include {session.app_name} *.js
recursive-include {session.app_name} *.json
recursive-include {session.app_name} *.md
recursive-include {session.app_name} *.png
recursive-include {session.app_name} *.py
recursive-include {session.app_name} *.svg
recursive-include {session.app_name} *.txt
recursive-exclude {session.app_name} *.pyc
"""
		with open(os.path.join(app_path, "MANIFEST.in"), 'w') as f:
			f.write(manifest_content)
		results.append({"file": "MANIFEST.in", "status": "created"})
		
		return {
			"success": True,
			"message": f"Complete app structure created for {session.app_name}",
			"results": results,
			"total_files": len(results)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create App Structure Error")
		return {
			"error": str(e),
			"traceback": frappe.get_traceback()
		}


@frappe.whitelist()
def create_app_structure(session_name):
	"""
	Create complete Frappe app structure with all necessary files
	"""
	try:
		settings = frappe.get_single("Claude API Settings")
		session = frappe.get_doc("App Development Session", session_name)
		
		if not settings.app_path:
			return {"error": "Apps path not configured in settings"}
		
		app_path = os.path.join(settings.app_path, session.app_name)
		app_module_path = os.path.join(app_path, session.app_name)
		
		results = []
		
		# Create main app directory
		os.makedirs(app_path, exist_ok=True)
		
		# Create main module directory
		os.makedirs(app_module_path, exist_ok=True)
		
		# 1. Create __init__.py
		init_content = f"__version__ = '0.0.1'\n"
		create_file_with_log(session_name, session.app_name, 
			os.path.join(app_module_path, "__init__.py"), init_content, results)
		
		# 2. Create hooks.py
		hooks_content = f"""from . import __version__ as app_version

app_name = "{session.app_name}"
app_title = "{session.app_title or session.app_name.replace('_', ' ').title()}"
app_publisher = "Your Company"
app_description = "{session.description or 'Custom Frappe Application'}"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "your@email.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/{session.app_name}/css/{session.app_name}.css"
# app_include_js = "/assets/{session.app_name}/js/{session.app_name}.js"

# include js, css files in header of web template
# web_include_css = "/assets/{session.app_name}/css/{session.app_name}.css"
# web_include_js = "/assets/{session.app_name}/js/{session.app_name}.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "{session.app_name}/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {{"doctype": "public/js/doctype.js"}}
# webform_include_css = {{"doctype": "public/css/doctype.css"}}

# include js in page
# page_js = {{"page" : "public/js/file.js"}}

# include js in doctype views
# doctype_js = {{"doctype" : "public/js/doctype.js"}}
# doctype_list_js = {{"doctype" : "public/js/doctype_list.js"}}
# doctype_tree_js = {{"doctype" : "public/js/doctype_tree.js"}}
# doctype_calendar_js = {{"doctype" : "public/js/doctype_calendar.js"}}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {{
#	"Role": "home_page"
# }}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "{session.app_name}.install.before_install"
# after_install = "{session.app_name}.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "{session.app_name}.uninstall.before_uninstall"
# after_uninstall = "{session.app_name}.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "{session.app_name}.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {{
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }}
#
# has_permission = {{
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {{
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {{
# 	"*": {{
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}}
# }}

# Scheduled Tasks
# ---------------

# scheduler_events = {{
# 	"all": [
# 		"{session.app_name}.tasks.all"
# 	],
# 	"daily": [
# 		"{session.app_name}.tasks.daily"
# 	],
# 	"hourly": [
# 		"{session.app_name}.tasks.hourly"
# 	],
# 	"weekly": [
# 		"{session.app_name}.tasks.weekly"
# 	]
# 	"monthly": [
# 		"{session.app_name}.tasks.monthly"
# 	]
# }}

# Testing
# -------

# before_tests = "{session.app_name}.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {{
# 	"frappe.desk.doctype.event.event.get_events": "{session.app_name}.event.get_events"
# }}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {{
# 	"Task": "{session.app_name}.task.get_dashboard_data"
# }}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{{
		"doctype": "{{doctype_1}}",
		"filter_by": "{{filter_by}}",
		"redact_fields": ["{{field_1}}", "{{field_2}}"],
		"partial": 1,
	}},
	{{
		"doctype": "{{doctype_2}}",
		"filter_by": "{{filter_by}}",
		"partial": 1,
	}},
	{{
		"doctype": "{{doctype_3}}",
		"strict": False,
	}},
	{{
		"doctype": "{{doctype_4}}"
	}}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"{session.app_name}.auth.validate"
# ]
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_module_path, "hooks.py"), hooks_content, results)
		
		# 3. Create modules.txt
		module_name = session.app_title or session.app_name.replace("_", " ").title()
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_module_path, "modules.txt"), f"{module_name}\n", results)
		
		# 4. Create patches.txt
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_module_path, "patches.txt"), "", results)
		
		# 5. Create config directory
		config_path = os.path.join(app_module_path, "config")
		os.makedirs(config_path, exist_ok=True)
		create_file_with_log(session_name, session.app_name,
			os.path.join(config_path, "__init__.py"), "", results)
		
		# Create desktop.py
		desktop_content = f"""from frappe import _

def get_data():
	return [
		{{
			"module_name": "{module_name}",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("{module_name}")
		}}
	]
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(config_path, "desktop.py"), desktop_content, results)
		
		# 6. Create public directory structure
		public_path = os.path.join(app_module_path, "public")
		for subdir in ["css", "js", "images"]:
			os.makedirs(os.path.join(public_path, subdir), exist_ok=True)
			create_file_with_log(session_name, session.app_name,
				os.path.join(public_path, subdir, "__init__.py"), "", results)
		
		# Create build.json
		create_file_with_log(session_name, session.app_name,
			os.path.join(public_path, "build.json"), "{}", results)
		
		# Create main CSS file
		css_content = f"/* {session.app_title or session.app_name} CSS */\n"
		create_file_with_log(session_name, session.app_name,
			os.path.join(public_path, "css", f"{session.app_name}.css"), css_content, results)
		
		# Create main JS file
		js_content = f"// {session.app_title or session.app_name} JavaScript\n"
		create_file_with_log(session_name, session.app_name,
			os.path.join(public_path, "js", f"{session.app_name}.js"), js_content, results)
		
		# 7. Create templates directory
		templates_path = os.path.join(app_module_path, "templates")
		os.makedirs(templates_path, exist_ok=True)
		create_file_with_log(session_name, session.app_name,
			os.path.join(templates_path, "__init__.py"), "", results)
		
		for subdir in ["pages", "includes", "generators"]:
			os.makedirs(os.path.join(templates_path, subdir), exist_ok=True)
		
		# 8. Create www directory
		www_path = os.path.join(app_module_path, "www")
		os.makedirs(www_path, exist_ok=True)
		
		# 9. Create translations directory
		translations_path = os.path.join(app_module_path, "translations")
		os.makedirs(translations_path, exist_ok=True)
		
		# 10. Create module directory
		module_path = os.path.join(app_module_path, module_name.lower().replace(" ", "_"))
		os.makedirs(module_path, exist_ok=True)
		create_file_with_log(session_name, session.app_name,
			os.path.join(module_path, "__init__.py"), "", results)
		
		# Create subdirectories in module
		for subdir in ["doctype", "page", "report", "web_form"]:
			subdir_path = os.path.join(module_path, subdir)
			os.makedirs(subdir_path, exist_ok=True)
			create_file_with_log(session_name, session.app_name,
				os.path.join(subdir_path, "__init__.py"), "", results)
		
		# 11. Create api directory
		api_path = os.path.join(app_module_path, "api")
		os.makedirs(api_path, exist_ok=True)
		create_file_with_log(session_name, session.app_name,
			os.path.join(api_path, "__init__.py"), "", results)
		
		# 12. Create tasks.py
		tasks_content = f"""# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe

def all():
	# Runs every 5 minutes
	pass

def hourly():
	pass

def daily():
	pass

def weekly():
	pass

def monthly():
	pass
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_module_path, "tasks.py"), tasks_content, results)
		
		# 13. Create root level files
		# setup.py
		setup_content = f"""from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\\n")

from {session.app_name} import __version__ as version

setup(
	name="{session.app_name}",
	version=version,
	description="{session.description or 'Custom Frappe Application'}",
	author="Your Company",
	author_email="your@email.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, "setup.py"), setup_content, results)
		
		# requirements.txt
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, "requirements.txt"), "frappe\n", results)
		
		# README.md
		readme_content = f"""# {session.app_title or session.app_name}

{session.description or 'Custom Frappe Application'}

## Installation

```bash
bench get-app {session.app_name}
bench --site your-site install-app {session.app_name}
```

## License

MIT
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, "README.md"), readme_content, results)
		
		# license.txt
		license_content = """MIT License

Copyright (c) 2025 Your Company

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, "license.txt"), license_content, results)
		
		# .gitignore
		gitignore_content = """.DS_Store
*.pyc
*.egg-info
*.swp
*.swo
.vscode
__pycache__
*.py[cod]
dist
build
*.egg
.tox
*.mo
node_modules
*.compiled
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, ".gitignore"), gitignore_content, results)
		
		# MANIFEST.in
		manifest_content = f"""include MANIFEST.in
include requirements.txt
include *.json
include *.md
include *.py
include *.txt
recursive-include {session.app_name} *.css
recursive-include {session.app_name} *.csv
recursive-include {session.app_name} *.html
recursive-include {session.app_name} *.ico
recursive-include {session.app_name} *.js
recursive-include {session.app_name} *.json
recursive-include {session.app_name} *.md
recursive-include {session.app_name} *.png
recursive-include {session.app_name} *.py
recursive-include {session.app_name} *.svg
recursive-include {session.app_name} *.txt
recursive-exclude {session.app_name} *.pyc
"""
		create_file_with_log(session_name, session.app_name,
			os.path.join(app_path, "MANIFEST.in"), manifest_content, results)
		
		return {
			"success": True,
			"message": f"Created complete app structure with {len(results)} files",
			"results": results
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create App Structure Error")
		return {
			"error": str(e),
			"traceback": frappe.get_traceback()
		}


def create_file_with_log(session_name, app_name, file_path, content, results_list):
	"""Helper function to create file and log it"""
	try:
		with open(file_path, 'w') as f:
			f.write(content)
		
		# Log file creation
		frappe.get_doc({
			"doctype": "File Change Log",
			"session_reference": session_name,
			"app_name": app_name,
			"operation_type": "Create",
			"file_path": file_path,
			"file_content": content[:1000],  # Store first 1000 chars
			"status": "Applied"
		}).insert(ignore_permissions=True)
		
		results_list.append({
			"file": file_path,
			"status": "created"
		})
		
	except Exception as e:
		results_list.append({
			"file": file_path,
			"status": "error",
			"error": str(e)
		})


@frappe.whitelist()
def apply_changes(session_name):
	"""
	Apply pending changes - create/modify files
	First creates complete app structure, then creates DocTypes
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
		
		# Step 1: Create complete app structure if it doesn't exist
		if not os.path.exists(app_path):
			frappe.msgprint("Creating complete app structure...")
			structure_result = create_app_structure(session_name)
			if structure_result.get("error"):
				session.status = "Error"
				session.save()
				frappe.db.commit()
				return structure_result
			
			results.extend(structure_result.get("results", []))
			results.append({
				"operation": "app_structure",
				"status": "success",
				"message": "Complete app structure created"
			})
		
		# Step 2: Process each DocType session
		module_name = (session.app_title or session.app_name.replace("_", " ").title()).lower().replace(" ", "_")
		
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
					module_name,
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
					"file_content": json.dumps(doctype_def, indent=2)[:1000],
					"status": "Applied"
				}).insert(ignore_permissions=True)
				
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
				}).insert(ignore_permissions=True)
				
				# Create __init__.py
				init_file = os.path.join(doctype_path, "__init__.py")
				with open(init_file, 'w') as f:
					f.write("")
				
				# Create test file
				test_file = os.path.join(doctype_path, f"test_{doctype_name.lower().replace(' ', '_')}.py")
				test_content = f"""# Copyright (c) 2025, Your Company and Contributors
# See license.txt

import frappe
import unittest

class Test{doctype_name.replace(' ', '')}(unittest.TestCase):
	pass
"""
				with open(test_file, 'w') as f:
					f.write(test_content)
				
				dt_sess.status = "Applied"
				results.append({
					"doctype": doctype_name,
					"status": "success",
					"files": [json_file, py_file, init_file, test_file]
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