import frappe
import os
import difflib
import subprocess
from pathlib import Path

@frappe.whitelist()
def apply_code_change(change_name):
    """Apply a pending code change"""
    try:
        change = frappe.get_doc('Code Change', change_name)
        
        if change.status != 'Pending':
            return {
                'success': False,
                'error': 'Change is not in pending status'
            }
        
        bench_path = frappe.utils.get_bench_path()
        file_path = os.path.join(bench_path, change.file_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if change.change_type == 'Create' or change.change_type == 'Modify':
            # Read original content if file exists
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    change.original_code = f.read()
            
            # Write new content
            with open(file_path, 'w') as f:
                f.write(change.modified_code)
            
            # Generate diff
            if change.original_code:
                diff = generate_diff(change.original_code, change.modified_code)
                change.diff = diff
        
        elif change.change_type == 'Delete':
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    change.original_code = f.read()
                os.remove(file_path)
        
        # Update status
        change.status = 'Applied'
        change.applied_at = frappe.utils.now()
        change.applied_by = frappe.session.user
        change.save()
        
        # Check if this is a DocType change and needs migration
        needs_migration = check_if_needs_migration(change.file_path)
        
        if needs_migration:
            # Run migration
            migration_result = run_migration()
            
            if migration_result['success']:
                return {
                    'success': True,
                    'message': f'Change applied successfully to {change.file_path}. Database migrated.',
                    'migrated': True
                }
            else:
                return {
                    'success': True,
                    'message': f'Change applied to {change.file_path} but migration failed: {migration_result.get("error")}',
                    'migrated': False,
                    'migration_error': migration_result.get('error')
                }
        
        return {
            'success': True,
            'message': f'Change applied successfully to {change.file_path}',
            'migrated': False
        }
        
    except Exception as e:
        frappe.log_error(f"Error applying code change: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def revert_code_change(change_name):
    """Revert an applied code change"""
    try:
        change = frappe.get_doc('Code Change', change_name)
        
        if change.status != 'Applied':
            return {
                'success': False,
                'error': 'Change is not in applied status'
            }
        
        bench_path = frappe.utils.get_bench_path()
        file_path = os.path.join(bench_path, change.file_path)
        
        if change.change_type == 'Create':
            # Delete the created file
            if os.path.exists(file_path):
                os.remove(file_path)
        
        elif change.change_type == 'Modify':
            # Restore original content
            if change.original_code:
                with open(file_path, 'w') as f:
                    f.write(change.original_code)
        
        elif change.change_type == 'Delete':
            # Restore deleted file
            if change.original_code:
                with open(file_path, 'w') as f:
                    f.write(change.original_code)
        
        # Update status
        change.status = 'Reverted'
        change.save()
        
        # Check if needs migration
        needs_migration = check_if_needs_migration(change.file_path)
        
        if needs_migration:
            migration_result = run_migration()
            
            if migration_result['success']:
                return {
                    'success': True,
                    'message': f'Change reverted successfully for {change.file_path}. Database migrated.',
                    'migrated': True
                }
        
        return {
            'success': True,
            'message': f'Change reverted successfully for {change.file_path}',
            'migrated': False
        }
        
    except Exception as e:
        frappe.log_error(f"Error reverting code change: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def check_if_needs_migration(file_path):
    """Check if the file change requires database migration"""
    # DocType JSON files need migration
    if file_path.endswith('.json') and '/doctype/' in file_path:
        return True
    
    # Page JSON files might need migration
    if file_path.endswith('.json') and '/page/' in file_path:
        return True
    
    # Report JSON files might need migration
    if file_path.endswith('.json') and '/report/' in file_path:
        return True
    
    return False

def run_migration():
    """Run bench migrate for the current site"""
    try:
        site = frappe.local.site
        bench_path = frappe.utils.get_bench_path()
        
        # Run migrate command
        result = subprocess.run(
            ['bench', '--site', site, 'migrate'],
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'error': result.stderr or result.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Migration timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def preview_change(file_path, original_code, modified_code):
    """Generate a preview diff for code changes"""
    try:
        diff = generate_diff(original_code, modified_code)
        return {
            'success': True,
            'diff': diff
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def generate_diff(original, modified):
    """Generate a unified diff between original and modified code"""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile='original',
        tofile='modified',
        lineterm=''
    )
    
    return ''.join(diff)

@frappe.whitelist()
def get_file_content(file_path):
    """Get the content of a file"""
    try:
        bench_path = frappe.utils.get_bench_path()
        full_path = os.path.join(bench_path, file_path)
        
        if not os.path.exists(full_path):
            return {
                'success': False,
                'error': 'File not found'
            }
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        return {
            'success': True,
            'content': content
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def list_app_files(app_name):
    """List all files in a custom app"""
    try:
        bench_path = frappe.utils.get_bench_path()
        app_path = os.path.join(bench_path, 'apps', app_name)
        
        if not os.path.exists(app_path):
            return {
                'success': False,
                'error': 'App not found'
            }
        
        files = []
        for root, dirs, filenames in os.walk(app_path):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for filename in filenames:
                if filename.endswith(('.py', '.js', '.json', '.html', '.css', '.md')):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, bench_path)
                    files.append(rel_path)
        
        return {
            'success': True,
            'files': files
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def apply_all_pending_changes(session_id=None):
    """Apply all pending code changes, optionally filtered by session"""
    try:
        filters = {'status': 'Pending'}
        
        if session_id:
            # Get all messages from the session
            messages = frappe.get_all('Dev Chat Message', 
                filters={'session': session_id},
                pluck='name'
            )
            
            if not messages:
                return {
                    'success': True,
                    'message': 'No changes found for this session',
                    'applied': 0
                }
            
            filters['parent'] = ['in', messages]
        
        changes = frappe.get_all('Code Change', filters=filters, pluck='name')
        
        if not changes:
            return {
                'success': True,
                'message': 'No pending changes to apply',
                'applied': 0
            }
        
        applied = 0
        failed = 0
        errors = []
        
        for change_name in changes:
            result = apply_code_change(change_name)
            if result.get('success'):
                applied += 1
            else:
                failed += 1
                errors.append(f"{change_name}: {result.get('error')}")
        
        # Run migration once at the end if any changes were applied
        migration_result = None
        if applied > 0:
            migration_result = run_migration()
        
        return {
            'success': True,
            'message': f'Applied {applied} changes, {failed} failed',
            'applied': applied,
            'failed': failed,
            'errors': errors,
            'migrated': migration_result.get('success') if migration_result else False
        }
        
    except Exception as e:
        frappe.log_error(f"Error applying changes: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
