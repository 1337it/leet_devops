frappe.pages['dev-chat'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Dev Chat',
        single_column: true
    });
    
    // Add primary action
    page.set_primary_action('New Session', function() {
        frappe.prompt([
            {
                fieldname: 'session_name',
                label: 'Session Name',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                fieldname: 'description',
                label: 'Description',
                fieldtype: 'Small Text'
            }
        ], function(values) {
            frappe.call({
                method: 'leet_devops.api.chat.create_session',
                args: values,
                callback: function(r) {
                    if (r.message.success) {
                        frappe.set_route('Form', 'Dev Chat Session', r.message.session_id);
                    }
                }
            });
        }, 'Create New Session', 'Create');
    });
    
    // Render session list
    render_sessions(page);
};

function render_sessions(page) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Dev Chat Session',
            filters: {
                status: 'Active'
            },
            fields: ['name', 'session_name', 'created_at', 'description'],
            order_by: 'modified desc',
            limit: 20
        },
        callback: function(r) {
            if (r.message) {
                let html = `
                    <div class="page-content">
                        <div class="session-list-container">
                            <h3>Your Chat Sessions</h3>
                            <div class="session-list">
                `;
                
                if (r.message.length === 0) {
                    html += `
                        <div class="empty-state">
                            <p>No chat sessions yet. Click "New Session" to start!</p>
                        </div>
                    `;
                } else {
                    r.message.forEach(session => {
                        html += `
                            <div class="session-card" onclick="frappe.set_route('Form', 'Dev Chat Session', '${session.name}')">
                                <div class="session-card-header">
                                    <strong>${session.session_name}</strong>
                                    <span class="text-muted">${frappe.datetime.prettyDate(session.created_at)}</span>
                                </div>
                                ${session.description ? `<p class="text-muted">${session.description}</p>` : ''}
                            </div>
                        `;
                    });
                }
                
                html += `
                            </div>
                        </div>
                    </div>
                `;
                
                $(page.body).html(html);
            }
        }
    });
}
