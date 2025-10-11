import frappe
import subprocess
import time
import json

@frappe.whitelist()
def execute_command(change_name):
    """Execute a command-type Code Change"""
    try:
        change = frappe.get_doc('Code Change', change_name)
        
        if not change.is_command:
            return {
                'success': False,
                'error': 'This is not a command change'
            }
        
        if change.status != 'Pending':
            return {
                'success': False,
                'error': f'Command status is {change.status}, not Pending'
            }
        
        # Mark as executing
        change.status = 'Applied'
        change.save()
        
        start_time = time.time()
        
        if change.command_type == 'Bench Console':
            result = execute_bench_console(change.command_code)
        elif change.command_type == 'Shell Command':
            result = execute_shell_command(change.command_code)
        elif change.command_type == 'SQL Query':
            result = execute_sql_query(change.command_code)
        elif change.command_type == 'Python Script':
            result = execute_python_script(change.command_code)
        else:
            result = {
                'success': False,
                'error': 'Unknown command type'
            }
        
        execution_time = time.time() - start_time
        
        # Update change with results
        change.execution_time = execution_time
        change.command_output = result.get('output', '')
        change.command_error = result.get('error', '')
        
        if not result.get('success'):
            change.status = 'Failed'
        
        change.applied_at = frappe.utils.now()
        change.applied_by = frappe.session.user
        change.save()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Command execution error: {str(e)}")
        change.status = 'Failed'
        change.command_error = str(e)
        change.save()
        return {
            'success': False,
            'error': str(e)
        }

def execute_bench_console(code):
    """Execute code in bench console"""
    try:
        site = frappe.local.site
        bench_path = frappe.utils.get_bench_path()
        
        # Create a temporary Python file with the code
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute using bench console
            result = subprocess.run(
                ['bench', '--site', site, 'console'],
                stdin=open(temp_file, 'r'),
                cwd=bench_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            error = result.stderr
            
            return {
                'success': result.returncode == 0,
                'output': output,
                'error': error if result.returncode != 0 else None
            }
        finally:
            os.unlink(temp_file)
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 60 seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def execute_shell_command(command):
    """Execute a shell command"""
    try:
        bench_path = frappe.utils.get_bench_path()
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def execute_sql_query(query):
    """Execute a SQL query"""
    try:
        result = frappe.db.sql(query, as_dict=True)
        
        return {
            'success': True,
            'output': json.dumps(result, indent=2, default=str)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def execute_python_script(code):
    """Execute Python code in current context"""
    try:
        import io
        import sys
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # Execute the code
            exec(code, {'frappe': frappe})
            output = sys.stdout.getvalue()
            
            return {
                'success': True,
                'output': output
            }
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def preview_execution_plan(message_id):
    """Generate a preview of what will be executed"""
    try:
        message = frappe.get_doc('Dev Chat Message', message_id)
        
        changes = frappe.get_all(
            'Code Change',
            filters={'parent': message_id},
            fields=['name', 'change_type', 'is_command', 'file_path', 
                    'command_description', 'status', 'command_type'],
            order_by='idx'
        )
        
        plan = {
            'file_changes': [],
            'commands': [],
            'summary': {
                'total': len(changes),
                'files': 0,
                'commands': 0,
                'creates': 0,
                'modifies': 0,
                'deletes': 0
            }
        }
        
        for change in changes:
            if change.is_command:
                plan['commands'].append({
                    'name': change.name,
                    'type': change.command_type,
                    'description': change.command_description,
                    'status': change.status
                })
                plan['summary']['commands'] += 1
            else:
                plan['file_changes'].append({
                    'name': change.name,
                    'type': change.change_type,
                    'path': change.file_path,
                    'status': change.status
                })
                plan['summary']['files'] += 1
                
                if change.change_type == 'Create':
                    plan['summary']['creates'] += 1
                elif change.change_type == 'Modify':
                    plan['summary']['modifies'] += 1
                elif change.change_type == 'Delete':
                    plan['summary']['deletes'] += 1
        
        return plan
        
    except Exception as e:
        frappe.log_error(f"Preview error: {str(e)}")
        return {
            'error': str(e)
        }
