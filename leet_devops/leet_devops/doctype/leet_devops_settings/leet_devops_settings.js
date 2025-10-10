frappe.ui.form.on('Leet DevOps Settings', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Test Claude API'), function() {
            test_claude_api(frm);
        });
        
        if (frm.doc.enable_github_integration) {
            frm.add_custom_button(__('Test GitHub Connection'), function() {
                test_github_connection(frm);
            });
            
            frm.add_custom_button(__('Load Repositories'), function() {
                load_github_repos(frm);
            });
        }
        
        // Load available apps
        load_available_apps(frm);
    },
    
    enable_github_integration: function(frm) {
        if (frm.doc.enable_github_integration) {
            load_github_repos(frm);
        }
    },
    
    onload: function(frm) {
        // Set field options dynamically
        load_available_apps(frm);
    }
});

function test_claude_api(frm) {
    if (!frm.doc.claude_api_key) {
        frappe.msgprint(__('Please enter Claude API key first'));
        return;
    }
    
    frappe.show_alert({
        message: __('Testing Claude API connection...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'leet_devops.api.chat.test_api_connection',
        args: {
            api_key: frm.doc.claude_api_key,
            model: frm.doc.claude_model
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Claude API connection successful!'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Failed'),
                    message: r.message.error || __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function test_github_connection(frm) {
    frappe.call({
        method: 'leet_devops.leet_devops.doctype.leet_devops_settings.leet_devops_settings.test_github_connection',
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('GitHub Connected'),
                    message: __('Connected as: {0}', [r.message.user]),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Failed'),
                    message: r.message.message || __('Failed to connect to GitHub'),
                    indicator: 'red'
                });
            }
        }
    });
}

function load_available_apps(frm) {
    frappe.call({
        method: 'leet_devops.leet_devops.doctype.leet_devops_settings.leet_devops_settings.get_available_apps',
        callback: function(r) {
            if (r.message) {
                let options = r.message.map(app => app.value).join('\n');
                frm.set_df_property('target_app', 'options', options);
                frm.refresh_field('target_app');
            }
        }
    });
}

function load_github_repos(frm) {
    frappe.call({
        method: 'leet_devops.leet_devops.doctype.leet_devops_settings.leet_devops_settings.get_github_repos',
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let options = r.message.map(repo => repo.value).join('\n');
                frm.set_df_property('github_repo', 'options', options);
                frm.refresh_field('github_repo');
                
                frappe.show_alert({
                    message: __('Loaded {0} repositories', [r.message.length]),
                    indicator: 'green'
                });
            }
        }
    });
}
