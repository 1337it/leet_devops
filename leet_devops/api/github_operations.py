import frappe
import os
import subprocess
from datetime import datetime

@frappe.whitelist()
def create_commit_from_changes(change_ids, commit_message=None):
    """Create a Code Commit document from applied Code Changes"""
    try:
        if isinstance(change_ids, str):
            import json
            change_ids = json.loads(change_ids)
        
        settings = frappe.get_single('Leet DevOps Settings')
        
        if not commit_message:
            commit_message = f"Changes via Leet DevOps - {frappe.utils.now()}"
        
        # Create commit document
        commit_doc = frappe.get_doc({
            'doctype': 'Code Commit',
            'commit_message': commit_message,
            'branch': settings.branch_name or 'main',
            'status': 'Pending'
        })
        
        # Add changes
        for change_id in change_ids:
            change = frappe.get_doc('Code Change', change_id)
            commit_doc.append('changes_included', {
                'code_change': change.name,
                'file_path': change.file_path,
                'change_type': change.change_type,
                'applied_at': change.applied_at,
                'git_status': 'Not Staged'
            })
        
        commit_doc.insert()
        
        # If auto-commit is enabled, commit immediately
        if settings.enable_github_integration and settings.auto_commit:
            result = commit_to_github(commit_doc.name)
            return result
        
        return {
            'success': True,
            'commit_id': commit_doc.name,
            'message': 'Commit created. Click "Commit to GitHub" to push changes.'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating commit: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def commit_to_github(commit_id):
    """Commit and push changes to GitHub"""
    try:
        commit_doc = frappe.get_doc('Code Commit', commit_id)
        settings = frappe.get_single('Leet DevOps Settings')
        
        if not settings.enable_github_integration:
            return {
                'success': False,
                'error': 'GitHub integration is not enabled'
            }
        
        if not settings.target_app:
            return {
                'success': False,
                'error': 'Target app not configured'
            }
        
        # Update status
        commit_doc.status = 'Committing'
        commit_doc.save()
        
        bench_path = frappe.utils.get_bench_path()
        app_path = os.path.join(bench_path, 'apps', settings.target_app)
        
        # Stage files
        files_to_commit = []
        for change in commit_doc.changes_included:
            file_path = change.file_path
            # Make path relative to app directory
            if file_path.startswith('apps/'):
                file_path = file_path.replace(f'apps/{settings.target_app}/', '')
            
            files_to_commit.append(file_path)
            
            # Stage the file
            result = subprocess.run(
                ['git', 'add', file_path],
                cwd=app_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                change.git_status = 'Staged'
        
        commit_doc.save()
        
        # Commit
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_doc.commit_message],
            cwd=app_path,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode != 0:
            commit_doc.status = 'Failed'
            commit_doc.error_log = commit_result.stderr
            commit_doc.save()
            return {
                'success': False,
                'error': f'Git commit failed: {commit_result.stderr}'
            }
        
        # Get commit SHA
        sha_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=app_path,
            capture_output=True,
            text=True
        )
        commit_sha = sha_result.stdout.strip()
        
        # Update all changes to committed
        for change in commit_doc.changes_included:
            change.git_status = 'Committed'
        
        commit_doc.github_commit_sha = commit_sha
        commit_doc.status = 'Committed'
        commit_doc.committed_at = frappe.utils.now()
        commit_doc.save()
        
        # Push to GitHub
        if settings.github_token and settings.github_repo:
            push_result = push_to_github(commit_doc, settings, app_path)
            if push_result.get('success'):
                commit_doc.status = 'Pushed'
                commit_doc.github_url = push_result.get('url')
                commit_doc.save()
        
        return {
            'success': True,
            'sha': commit_sha,
            'message': 'Changes committed successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error committing to GitHub: {str(e)}")
        commit_doc.status = 'Failed'
        commit_doc.error_log = str(e)
        commit_doc.save()
        return {
            'success': False,
            'error': str(e)
        }

def push_to_github(commit_doc, settings, app_path):
    """Push commits to GitHub"""
    try:
        # Set up remote if needed
        remote_check = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=app_path,
            capture_output=True,
            text=True
        )
        
        if remote_check.returncode != 0:
            # Add remote
            repo_url = f"https://{settings.github_username}:{settings.get_password('github_token')}@github.com/{settings.github_repo}.git"
            subprocess.run(
                ['git', 'remote', 'add', 'origin', repo_url],
                cwd=app_path,
                capture_output=True,
                text=True
            )
        
        # Push
        push_result = subprocess.run(
            ['git', 'push', 'origin', commit_doc.branch],
            cwd=app_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            return {
                'success': False,
                'error': push_result.stderr
            }
        
        # Generate GitHub URL
        url = f"https://github.com/{settings.github_repo}/commit/{commit_doc.github_commit_sha}"
        
        return {
            'success': True,
            'url': url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_uncommitted_changes():
    """Get list of applied changes that haven't been committed"""
    settings = frappe.get_single('Leet DevOps Settings')
    
    # Get all applied changes
    applied_changes = frappe.get_all(
        'Code Change',
        filters={'status': 'Applied'},
        fields=['name', 'file_path', 'change_type', 'applied_at', 'applied_by'],
        order_by='applied_at desc'
    )
    
    # Get changes that are already in commits
    committed_changes = frappe.get_all(
        'Code Commit Change',
        filters={'git_status': ['in', ['Staged', 'Committed']]},
        pluck='code_change'
    )
    
    # Filter out committed changes
    uncommitted = [
        change for change in applied_changes
        if change.name not in committed_changes
    ]
    
    return uncommitted

@frappe.whitelist()
def get_commit_history(limit=50):
    """Get commit history"""
    commits = frappe.get_all(
        'Code Commit',
        fields=['name', 'commit_message', 'status', 'committed_at', 'github_url', 'github_commit_sha'],
        order_by='committed_at desc',
        limit=limit
    )
    
    return commits
