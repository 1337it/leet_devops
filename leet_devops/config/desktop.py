from frappe import _

def get_data():
    return [
        {
            "module_name": "Leet DevOps",
            "color": "blue",
            "icon": "octicon octicon-code",
            "type": "module",
            "label": _("Leet DevOps"),
            "description": _("AI-powered development assistant"),
            "_doctype": "Dev Chat Session"
        }
    ]

def get_workspace():
    """Create workspace for Leet DevOps"""
    return {
        "name": "Leet DevOps",
        "title": "Leet DevOps",
        "icon": "octicon octicon-code",
        "links": [
            {
                "label": "Chat",
                "items": [
                    {
                        "type": "Link",
                        "name": "Dev Chat",
                        "label": "Open Chat",
                        "url": "/app/dev-chat",
                        "description": "Chat with AI assistant"
                    }
                ]
            },
            {
                "label": "Sessions",
                "items": [
                    {
                        "type": "DocType",
                        "name": "Dev Chat Session",
                        "label": "Chat Sessions",
                        "description": "Manage chat sessions"
                    }
                ]
            },
            {
                "label": "Code Changes",
                "items": [
                    {
                        "type": "Report",
                        "name": "Code Changes Report",
                        "label": "View All Changes",
                        "doctype": "Code Change",
                        "is_query_report": False
                    }
                ]
            }
        ]
    }
