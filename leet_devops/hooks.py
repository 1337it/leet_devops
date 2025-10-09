from . import __version__ as app_version

app_name = "leet_devops"
app_title = "Leet DevOps"
app_publisher = "Your Company"
app_description = "AI-powered development assistant for Frappe"
app_icon = "octicon octicon-code"
app_color = "blue"
app_email = "your.email@example.com"
app_license = "MIT"

# Includes in 
app_include_css = "/assets/leet_devops/css/leet_devops.css"
app_include_js = "/assets/leet_devops/js/leet_devops.js"

# Home Pages
# ----------
# application_home_page = "leet_devops"
# role_home_page = {
#     "Role": "leet_devops"
# }

# Website user home page
# home_page = "login"

# Generators
# ----------
# automatically create page for each record of this doctype
# generators = []

# Includes in 
# ------------------
# include js, css files in header of desk.html
# app_include_css = "/assets/leet_devops/css/leet_devops.css"
# app_include_js = "/assets/leet_devops/js/leet_devops.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#     "Role": "home_page"
# }

# Permissions
# -----------
# Permissions evaluated in scripted ways
# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes
# override_doctype_class = {
#     "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# Scheduled Tasks
# ---------------
# scheduler_events = {
#     "all": [
#         "leet_devops.tasks.all"
#     ],
#     "daily": [
#         "leet_devops.tasks.daily"
#     ],
#     "hourly": [
#         "leet_devops.tasks.hourly"
#     ],
#     "weekly": [
#         "leet_devops.tasks.weekly"
#     ]
#     "monthly": [
#         "leet_devops.tasks.monthly"
#     ]
# }

# Testing
# -------
# before_tests = "leet_devops.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "leet_devops.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#     "Task": "leet_devops.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in", []]]
    }
]
