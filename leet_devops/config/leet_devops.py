from frappe import _

def get_data():
    return [
        {
            "label": _("Development"),
            "items": [
                {
                    "type": "doctype",
                    "name": "App Development Session",
                    "label": _("App Development Session"),
                    "description": _("Create and manage app development sessions")
                },
                {
                    "type": "doctype",
                    "name": "File Change Log",
                    "label": _("File Change Log"),
                    "description": _("Track file changes and operations")
                }
            ]
        },
        {
            "label": _("Settings"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Claude API Settings",
                    "label": _("Claude API Settings"),
                    "description": _("Configure Claude API and app settings")
                }
            ]
        },
        {
            "label": _("Tools"),
            "items": [
                {
                    "type": "page",
                    "name": "app-development-chat",
                    "label": _("App Development Chat"),
                    "description": _("Chat with Claude AI to develop apps")
                }
            ]
        }
    ]
