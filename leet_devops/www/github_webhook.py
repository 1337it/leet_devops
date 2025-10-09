import frappe
import hmac
import hashlib
import json

def get_context(context):
    """Handle GitHub webhook events (e.g., PR merged, push)"""
    if frappe.request.method != "POST":
        frappe.throw("Invalid request method")

    payload = frappe.request.data
    signature = frappe.get_request_header("X-Hub-Signature-256")
    event = frappe.get_request_header("X-GitHub-Event")

    secret = (frappe.get_single("LD GitHub Settings").webhook_secret or "").encode()
    mac = hmac.new(secret, msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()

    if not hmac.compare_digest(signature or "", expected):
        frappe.local.response["http_status_code"] = 401
        return {"message": "Signature mismatch"}

    try:
        data = json.loads(payload.decode())
    except Exception:
        frappe.local.response["http_status_code"] = 400
        return {"message": "Invalid JSON"}

    # Basic logging for visibility
    frappe.logger("leet_devops").info(f"Received GitHub event: {event}")
    frappe.logger("leet_devops").debug(data)

    # Example: mark deployment as success if tag push event
    if event == "push" and data.get("ref", "").startswith("refs/tags/"):
        tag = data["ref"].split("/")[-1]
        frappe.logger("leet_devops").info(f"Tag pushed: {tag}")

    frappe.local.response["http_status_code"] = 200
    return {"message": f"Received {event} successfully"}
