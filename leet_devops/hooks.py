# -*- coding: utf-8 -*-

app_name = "leet_devops"
app_title = "Leet DevOps"
app_publisher = "Leet IT Solutions"
app_description = "GitHub + SSH deploys and OpenAI Change Chat inside Frappe/ERPNext"
app_email = "dev@leetitsolutions.com"
app_license = "MIT"
app_version = "0.0.1"

# --------------------------------------------------------------------
# Assets (built from leet_devops/public/build.json by bench build)
# --------------------------------------------------------------------
app_include_js = ["/assets/leet_devops/js/leet_devops.bundle.js"]
app_include_css = ["/assets/leet_devops/css/leet_devops.bundle.css"]

# --------------------------------------------------------------------
# Desk Pages / Modules
# (Your desk pages live under leet_devops/pages/, no extra hooks needed)
# --------------------------------------------------------------------

# --------------------------------------------------------------------
# Website routes (GitHub webhook endpoint)
# /api/leet-devops/github/webhook -> leet_devops/www/github_webhook.py
# --------------------------------------------------------------------
website_route_rules = [
    {
        "from_route": "/api/leet-devops/github/webhook",
        "to_route": "leet_devops/www/github_webhook"
    }
]

# --------------------------------------------------------------------
# Background Jobs / Scheduler
# --------------------------------------------------------------------
scheduler_events = {
    # periodic reconciliation / status checks (lightweight placeholder)
    "all": ["leet_devops.api.devops.reconcile_pending_deployments"],
}

# --------------------------------------------------------------------
# Installation hooks (optional; keep minimal)
# --------------------------------------------------------------------
# def after_install():
#     pass

# def before_uninstall():
#     pass

# --------------------------------------------------------------------
# Doc Events / Permissions (add later if you enforce workflows)
# --------------------------------------------------------------------
# doc_events = {}
# permission_query_conditions = {}
# has_permission = {}
