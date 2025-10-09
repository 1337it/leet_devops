from frappe import _

def get_data():
    return [
        {
            "module_name": "Leet DevOps",
            "category": "Modules",
            "label": _("Leet DevOps"),
            "color": "grey",
            "icon": "octicon octicon-gear",
            "type": "module",
            "link": "devops_dashboard"
        },
        {
            "module_name": "Leet DevOps AI",
            "category": "Modules",
            "label": _("AI Change Chat"),
            "color": "blue",
            "icon": "octicon octicon-comment-discussion",
            "type": "page",
            "link": "ai_change_chat"
        }
    ]
