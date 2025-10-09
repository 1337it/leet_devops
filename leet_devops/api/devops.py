from __future__ import annotations
import frappe, json, datetime
from frappe import _
from .github_client import GitHub
from .ssh_client import ssh_exec

@frappe.whitelist()
def create_change_request(repository: str, title: str, description: str, files_json: str, target_branch: str = None):
    doc = frappe.get_doc({
        "doctype": "LD Change Request",
        "repository": repository,
        "title": title,
        "description": description,
        "files_json": files_json,
        "target_branch": target_branch or frappe.db.get_value("LD Repository", repository, "default_branch"),
    }).insert()
    return doc.name

@f
