"""
leet_devops/leet_devops/patches/add_session_fields.py
Migration script to add new fields to DocTypes
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add fields to Dev Chat Session and update Dev Chat Message"""
    
    # Custom fields for Dev Chat Session
    custom_fields = {
        'Dev Chat Session': [
            {
                'fieldname': 'parent_session',
                'label': 'Parent Session',
                'fieldtype': 'Link',
                'options': 'Dev Chat Session',
                'insert_after': 'status',
                'description': 'If this session was created from a multi-doctype request'
            },
            {
                'fieldname': 'target_doctype',
                'label': 'Target DocType',
                'fieldtype': 'Data',
                'insert_after': 'parent_session',
                'description': 'Specific DocType this session focuses on'
            },
            {
                'fieldname': 'action_type',
                'label': 'Action Type',
                'fieldtype': 'Select',
                'options': '\ncreate\nmodify\ndelete',
                'insert_after': 'target_doctype',
                'description': 'Type of action for this DocType'
            },
            {
                'fieldname': 'child_sessions_section',
                'label': 'Child Sessions',
                'fieldtype': 'Section Break',
                'insert_after': 'action_type'
            },
            {
                'fieldname': 'child_sessions_html',
                'label': 'Child Sessions',
                'fieldtype': 'HTML',
                'options': '<div id="child-sessions-list"></div>',
                'insert_after': 'child_sessions_section'
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    
    # Update message_type options in Dev Chat Message
    try:
        doc = frappe.get_doc('DocType', 'Dev Chat Message')
        for field in doc.fields:
            if field.fieldname == 'message_type':
                if 'System' not in field.options:
                    field.options = '\nUser\nAssistant\nSystem'
                    doc.save()
                    print("✅ Updated Dev Chat Message message_type field")
                break
    except Exception as e:
        print(f"⚠️ Error updating Dev Chat Message: {str(e)}")
    
    frappe.db.commit()
    print("✅ Migration completed successfully")
