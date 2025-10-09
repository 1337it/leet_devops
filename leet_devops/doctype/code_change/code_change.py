import frappe
from frappe.model.document import Document

class CodeChange(Document):
    pass
```

### leet_devops/leet_devops/doctype/code_change/code_change.js
```javascript
frappe.ui.form.on('Code Change', {
    refresh: function(frm) {
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Apply Change'), function() {
                frappe.call({
                    method: 'leet_devops.api.code_operations.apply_code_change',
                    args: {
                        change_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message.success) {
                            frappe.msgprint(__('Change applied successfully'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Error: ') + r.message.error);
                        }
                    }
                });
            });
            
            frm.add_custom_button(__('Reject'), function() {
                frm.set_value('status', 'Rejected');
                frm.save();
            });
        }
        
        if (frm.doc.status === 'Applied') {
            frm.add_custom_button(__('Revert'), function() {
                frappe.call({
                    method: 'leet_devops.api.code_operations.revert_code_change',
                    args: {
                        change_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message.success) {
                            frappe.msgprint(__('Change reverted successfully'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Error: ') + r.message.error);
                        }
                    }
                });
            });
        }
    }
});
