frappe.ui.form.on('Code Change', {
    refresh: function(frm) {
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Apply Change'), function() {
                frappe.confirm(
                    'Are you sure you want to apply this change? Make sure you have a backup.',
                    () => {
                        frappe.call({
                            method: 'leet_devops.api.code_operations.apply_code_change',
                            args: {
                                change_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message.success) {
                                    frappe.show_alert({
                                        message: r.message.message,
                                        indicator: 'green'
                                    });
                                    
                                    if (r.message.migrated) {
                                        frappe.msgprint({
                                            title: __('Migration Complete'),
                                            message: __('Database has been migrated successfully'),
                                            indicator: 'green'
                                        });
                                    }
                                    
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: 'Error',
                                        message: r.message.error,
                                        indicator: 'red'
                                    });
                                }
                            }
                        });
                    }
                );
            });
            
            frm.add_custom_button(__('Reject'), function() {
                frm.set_value('status', 'Rejected');
                frm.save();
            });
        }
        
        if (frm.doc.status === 'Applied') {
            frm.add_custom_button(__('Revert'), function() {
                frappe.confirm(
                    'Are you sure you want to revert this change?',
                    () => {
                        frappe.call({
                            method: 'leet_devops.api.code_operations.revert_code_change',
                            args: {
                                change_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message.success) {
                                    frappe.show_alert({
                                        message: r.message.message,
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: 'Error',
                                        message: r.message.error,
                                        indicator: 'red'
                                    });
                                }
                            }
                        });
                    }
                );
            });
        }
        
        // Add view diff button
        if (frm.doc.diff) {
            frm.add_custom_button(__('View Diff'), function() {
                frappe.msgprint({
                    title: 'Code Diff',
                    message: '<pre>' + frm.doc.diff + '</pre>',
                    wide: true
                });
            });
        }
    }
});
