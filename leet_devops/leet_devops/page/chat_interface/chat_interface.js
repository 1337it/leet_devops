frappe.pages['chat-interface'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Chat Interface',
        single_column: true
    });

    // Add New Session button
    page.add_inner_button('New Session', function() {
        create_new_session();
    });

    // Add Settings button
    page.add_menu_item('Settings', function() {
        frappe.set_route('Form', 'DevOps Settings', 'DevOps Settings');
    });

    // Initialize
    let session_id = frappe.get_route()[1];
    if (session_id) {
        load_chat_session(page, session_id);
    } else {
        show_session_selector(page);
    }
}

function create_new_session() {
    const d = new frappe.ui.Dialog({
        title: 'Create New Session',
        fields: [
            {
                label: 'Session Title',
                fieldname: 'title',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: 'Target App',
                fieldname: 'target_app',
                fieldtype: 'Data',
                reqd: 1,
                description: 'Name of the Frappe app to generate code for'
            },
            {
                label: 'Session Type',
                fieldname: 'session_type',
                fieldtype: 'Select',
                options: 'Main\nDocType\nFunction\nReport\nPage',
                default: 'Main'
            }
        ],
        primary_action_label: 'Create',
        primary_action(values) {
            frappe.call({
                method: 'leet_devops.api.claude_api.create_session',
                args: values,
                callback: (r) => {
                    if (r.message) {
                        frappe.set_route('chat-interface', r.message);
                        d.hide();
                    }
                }
            });
        }
    });

    // Get default app from settings
    frappe.call({
        method: 'frappe.client.get_single',
        args: { doctype: 'DevOps Settings' },
        callback: (r) => {
            if (r.message && r.message.target_app_name) {
                d.set_value('target_app', r.message.target_app_name);
            }
        }
    });

    d.show();
}

function load_chat_session(page, session_id) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Generation Session',
            name: session_id
        },
        callback: (r) => {
            if (r.message) {
                page.set_title(r.message.title);
                
                // Initialize chat interface
                const chat = new leet_devops.ChatInterface(
                    $(page.body),
                    session_id
                );
                
                // Update header with session info
                page.body.find('.session-title').text(r.message.title);
            }
        }
    });
}

function show_session_selector(page) {
    page.body.html(`
        <div class="session-selector">
            <div class="text-center" style="padding: 50px;">
                <h3>Welcome to Leet DevOps</h3>
                <p class="text-muted">AI-powered DocType and Function Generator</p>
                <button class="btn btn-primary btn-lg" onclick="create_new_session()">
                    <i class="fa fa-plus"></i> Create New Session
                </button>
                <div style="margin-top: 30px;">
                    <h4>Recent Sessions</h4>
                    <div class="recent-sessions"></div>
                </div>
            </div>
        </div>
    `);

    load_recent_sessions(page.body.find('.recent-sessions'));
}

function load_recent_sessions(container) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Generation Session',
            fields: ['name', 'title', 'target_app', 'session_type', 'modified'],
            filters: { session_type: 'Main' },
            order_by: 'modified desc',
            limit: 10
        },
        callback: (r) => {
            if (r.message && r.message.length) {
                let html = '<div class="list-group" style="max-width: 600px; margin: 0 auto;">';
                r.message.forEach(session => {
                    html += `
                        <a href="#chat-interface/${session.name}" class="list-group-item list-group-item-action">
                            <div class="d-flex w-100 justify-content-between">
                                <h5 class="mb-1">${session.title}</h5>
                                <small>${frappe.datetime.comment_when(session.modified)}</small>
                            </div>
                            <p class="mb-1">App: ${session.target_app}</p>
                            <small class="badge badge-primary">${session.session_type}</small>
                        </a>
                    `;
                });
                html += '</div>';
                container.html(html);
            } else {
                container.html('<p class="text-muted">No sessions yet. Create your first one!</p>');
            }
        }
    });
}
