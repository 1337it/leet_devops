import frappe
from frappe import _
from frappe.model.document import Document
import os

class LeetDevOpsSettings(Document):
    def validate(self):
        # Validate Claude API key format
        if self.claude_api_key and not self.claude_api_key.startswith('sk-ant-'):
            frappe.throw(_("Invalid Claude API key format. Key should start with 'sk-ant-'"))
        
        # Validate temperature range
        if self.temperature and (self.temperature < 0 or self.temperature > 1):
            frappe.throw(_("Temperature must be between 0.0 and 1.0"))
    
    def get_github_client(self):
        """Get authenticated GitHub client"""
        if not self.enable_github_integration or not self.github_token:
            return None
        
        try:
            from github import Github
            return Github(self.get_password('github_token'))
        except ImportError:
            frappe.throw(_("PyGithub not installed. Run: pip install PyGithub"))
        except Exception as e:
            frappe.throw(_("Failed to authenticate with GitHub: {0}").format(str(e)))

@frappe.whitelist()
def get_settings():
    """Get Leet DevOps settings"""
    if not frappe.db.exists('Leet DevOps Settings', 'Leet DevOps Settings'):
        # Create default settings
        doc = frappe.get_doc({
            'doctype': 'Leet DevOps Settings',
            'claude_model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8096,
            'temperature': 0.7,
            'branch_name': 'main'
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    
    return frappe.get_single('Leet DevOps Settings')

@frappe.whitelist()
def get_available_apps():
    """Get list of available apps in the bench"""
    bench_path = frappe.utils.get_bench_path()
    apps_path = os.path.join(bench_path, 'apps')
    
    apps = []
    if os.path.exists(apps_path):
        for item in os.listdir(apps_path):
            app_path = os.path.join(apps_path, item)
            if os.path.isdir(app_path) and not item.startswith('.'):
                # Check if it's a valid Frappe app
                hooks_file = os.path.join(app_path, item, 'hooks.py')
                if os.path.exists(hooks_file):
                    apps.append(item)
    
    return sorted(apps)

@frappe.whitelist()
def test_github_connection():
    """Test GitHub connection"""
    settings = get_settings()
    
    if not settings.enable_github_integration:
        return {'success': False, 'message': 'GitHub integration is not enabled'}
    
    if not settings.github_token:
        return {'success': False, 'message': 'GitHub token is not configured'}
    
    try:
        from github import Github
        g = Github(settings.get_password('github_token'))
        user = g.get_user()
        
        return {
            'success': True,
            'message': f'Connected as {user.login}',
            'user': user.login,
            'name': user.name
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

@frappe.whitelist()
def get_github_repos():
    """Get list of user's GitHub repositories"""
    settings = get_settings()
    
    if not settings.enable_github_integration or not settings.github_token:
        return []
    
    try:
        from github import Github
        g = Github(settings.get_password('github_token'))
        user = g.get_user()
        
        repos = []
        for repo in user.get_repos():
            repos.append({
                'value': repo.full_name,
                'label': f"{repo.full_name} {'(private)' if repo.private else ''}"
            })
        
        return sorted(repos, key=lambda x: x['label'])
    except Exception as e:
        frappe.log_error(f"Failed to fetch GitHub repos: {str(e)}")
        return []
