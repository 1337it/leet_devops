app_name = "leet_devops"
app_title = "Leet DevOps"
app_publisher = "Leet IT Solutions"
app_version = "0.0.1"
app_email = "dev@leetitsolutions.com"
app_license = "MIT"

# Desk shortcuts
app_include_js = ["/assets/leet_devops/js/leet_devops.bundle.js"]

# Webhook endpoint (public)
website_route_rules = [
    {"from_route": "/api/leet-devops/github/webhook", "to_route": "leet_devops/www/github_webhook"}
]

# Background jobs (if needed)
scheduler_events = {
    "all": ["leet_devops.api.devops.reconcile_pending_deployments"],
}
