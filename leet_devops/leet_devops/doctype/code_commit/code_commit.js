frappe.ui.form.on('Code Commit', {
    refresh: function(frm) {
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Commit to GitHub'), function() {
                frappe.confirm(
                    'This will commit and push the changes to GitHub. Continue?',
                    () => {
                        frappe.show_alert({
                            message: __('Committing to GitHub...'),
                            indicator: 'blue'
                        });
                        
                        frappe.call({
                            method: 'leet_devops.api.github_operations.commit_to_github',
                            args: {
                                commit_id: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        message: __('Changes committed successfully!<br>SHA: {0}', [r.message.sha]),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: __('Error'),
                                        message: r.message.error || __('Failed to commit'),
                                        indicator: 'red'
                                    });
                                }
                            }
                        });
                    }
                );
            }).addClass('btn-primary');
        }
        
        if (frm.doc.github_url) {
            frm.add_custom_button(__('View on GitHub'), function() {
                window.open(frm.doc.github_url, '_blank');
            });
        }
    }
});
