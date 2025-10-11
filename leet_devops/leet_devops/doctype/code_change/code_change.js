frappe.ui.form.on('Code Change', {
    refresh: function(frm) {
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Apply Change'), function() {
                frappe.confirm(
                    'Are you sure you want to apply this change? Make sure you have a backup.',
                    () => {
                        frappe.show_alert({
                            message: __('Applying changes...'),
                            indicator: 'blue'
                        });
                        
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
                                            message: __('Database has been migrated successfully. The page will refresh in 2 seconds...'),
                                            indicator: 'green'
                                        });
                                        
                                        setTimeout(() => {
                                            window.location.reload();
                                        }, 2000);
                                    } else {
                                        frm.reload_doc();
                                    }
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
            
            frm.add_custom_button(__('Apply & Commit'), function() {
                frappe.prompt([
                    {
                        fieldname: 'commit_message',
                        label: 'Commit Message',
                        fieldtype: 'Small Text',
                        reqd: 1,
                        default: `Applied ${frm.doc.change_type}: ${frm.doc.file_path}`
                    }
                ], function(values) {
                    frappe.call({
                        method: 'leet_devops.api.code_operations.apply_and_prepare_commit',
                        args: {
                            change_name: frm.doc.name,
                            commit_message: values.commit_message
                        },
                        callback: function(r) {
                            if (r.message.success) {
                                frappe.msgprint({
                                    title: __('Success'),
                                    message: __('Change applied and prepared for GitHub commit'),
                                    indicator: 'green'
                                });
                                
                                if (r.message.commit_result && r.message.commit_result.commit_id) {
                                    frappe.set_route('Form', 'Code Commit', r.message.commit_result.commit_id);
                                } else {
                                    frm.reload_doc();
                                }
                            }
                        }
                    });
                }, __('Apply and Prepare Commit'), __('Apply'));
            });
            
            frm.add_custom_button(__('Reject'), function() {
                frm.set_value('status', 'Rejected');
                frm.save();
            });
        }
        
        if (frm.doc.status === 'Applied') {
            frm.add_custom_button(__('Create Commit'), function() {
                frappe.prompt([
                    {
                        fieldname: 'commit_message',
                        label: 'Commit Message',
                        fieldtype: 'Small Text',
                        reqd: 1,
                        default: `Applied ${frm.doc.change_type}: ${frm.doc.file_path}`
                    }
                ], function(values) {
                    frappe.call({
                        method: 'leet_devops.api.github_operations.create_commit_from_changes',
                        args: {
                            change_ids: [frm.doc.name],
                            commit_message: values.commit_message
                        },
                        callback: function(r) {
                            if (r.message.success) {
                                frappe.set_route('Form', 'Code Commit', r.message.commit_id);
                            }
                        }
                    });
                }, __('Create Commit'), __('Create'));
            });
            
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
                                    
                                    if (r.message.migrated) {
                                        setTimeout(() => {
                                            window.location.reload();
                                        }, 2000);
                                    } else {
                                        frm.reload_doc();
                                    }
                                }
                            }
                        });
                    }
                );
            });
        }
        
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
