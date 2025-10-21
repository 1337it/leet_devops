// Copyright (c) 2025, Leet DevOps and contributors
// For license information, please see license.txt

frappe.ui.form.on('Generation Session', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            // Add Open Chat button
            frm.add_custom_button(__('Open Chat'), function() {
                frappe.set_route('chat-interface', frm.doc.name);
            }, __('Actions'));

            // Add View Child Sessions button
            frm.add_custom_button(__('View Child Sessions'), function() {
                show_child_sessions(frm);
            }, __('Actions'));

            // Add Archive button if active
            if (frm.doc.status === 'Active') {
                frm.add_custom_button(__('Archive Session'), function() {
                    frappe.confirm(
                        'Are you sure you want to archive this session?',
                        () => {
                            frm.set_value('status', 'Archived');
                            frm.save();
                        }
                    );
                }, __('Actions'));
            }

            // Add Complete button if active
            if (frm.doc.status === 'Active') {
                frm.add_custom_button(__('Mark Complete'), function() {
                    frm.set_value('status', 'Completed');
                    frm.save();
                }, __('Actions'));
            }

            // Show child session count in sidebar
            show_child_session_count(frm);
        }

        // Refresh indicators based on status
        if (frm.doc.status === 'Active') {
            frm.page.set_indicator('Active', 'green');
        } else if (frm.doc.status === 'Completed') {
            frm.page.set_indicator('Completed', 'blue');
        } else if (frm.doc.status === 'Archived') {
            frm.page.set_indicator('Archived', 'gray');
        }
    },

    session_type: function(frm) {
        // If session type changes, update context
        update_session_context(frm);
    },

    target_app: function(frm) {
        // Validate app exists
        if (frm.doc.target_app) {
            validate_app_exists(frm);
        }
    }
});

function show_child_sessions(frm) {
    frappe.call({
        method: 'leet_devops.api.claude_api.get_child_sessions',
        args: {
            parent_session_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                render_child_sessions_dialog(r.message);
            } else {
                frappe.msgprint(__('No child sessions found'));
            }
        }
    });
}

function render_child_sessions_dialog(sessions) {
    let html = '<div class="child-sessions-grid">';
    
    sessions.forEach(function(session) {
        let status_color = {
            'Active': 'green',
            'Completed': 'blue',
            'Archived': 'gray'
        }[session.status] || 'orange';

        html += `
            <div class="child-session-card" data-session="${session.name}">
                <div class="card-header">
                    <h4>${session.title}</h4>
                    <span class="indicator ${status_color}">${session.status}</span>
                </div>
                <div class="card-body">
                    <div class="badge">${session.session_type}</div>
                    <div class="text-muted small">
                        Modified: ${frappe.datetime.comment_when(session.modified)}
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm btn-primary open-session" 
                            data-session="${session.name}">
                        Open
                    </button>
                    <button class="btn btn-sm btn-default open-chat" 
                            data-session="${session.name}">
                        Chat
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';

    let d = new frappe.ui.Dialog({
        title: 'Child Sessions',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'sessions_html',
                options: html
            }
        ],
        size: 'large'
    });

    d.$wrapper.on('click', '.open-session', function() {
        let session_id = $(this).data('session');
        frappe.set_route('Form', 'Generation Session', session_id);
        d.hide();
    });

    d.$wrapper.on('click', '.open-chat', function() {
        let session_id = $(this).data('session');
        frappe.set_route('chat-interface', session_id);
        d.hide();
    });

    d.show();

    // Add custom CSS
    if (!$('#child-sessions-css').length) {
        $('head').append(`
            <style id="child-sessions-css">
                .child-sessions-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 15px;
                    max-height: 500px;
                    overflow-y: auto;
                }
                .child-session-card {
                    border: 1px solid #d1d8dd;
                    border-radius: 8px;
                    padding: 15px;
                    transition: all 0.2s;
                }
                .child-session-card:hover {
                    border-color: #2490ef;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .child-session-card .card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: start;
                    margin-bottom: 10px;
                }
                .child-session-card h4 {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                .child-session-card .card-body {
                    margin-bottom: 10px;
                }
                .child-session-card .card-footer {
                    display: flex;
                    gap: 8px;
                }
                .child-session-card .badge {
                    display: inline-block;
                    margin-bottom: 8px;
                }
            </style>
        `);
    }
}

function show_child_session_count(frm) {
    frappe.call({
        method: 'leet_devops.api.claude_api.get_child_sessions',
        args: {
            parent_session_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frm.dashboard.add_indicator(
                    __('Child Sessions: {0}', [r.message.length]),
                    'blue'
                );
            }
        }
    });
}

function update_session_context(frm) {
    if (!frm.doc.session_context) {
        let default_context = '';
        
        switch(frm.doc.session_type) {
            case 'DocType':
                default_context = 'This session is for generating a DocType with all necessary files.';
                break;
            case 'Function':
                default_context = 'This session is for creating API functions and utility methods.';
                break;
            case 'Report':
                default_context = 'This session is for building custom reports and analytics.';
                break;
            case 'Page':
                default_context = 'This session is for creating custom pages and interfaces.';
                break;
            default:
                default_context = 'This is a main planning and coordination session.';
        }
        
        frm.set_value('session_context', default_context);
    }
}

function validate_app_exists(frm) {
    // This would ideally check if the app exists in the system
    // For now, just a simple validation
    if (frm.doc.target_app && frm.doc.target_app.includes(' ')) {
        frappe.msgprint({
            title: __('Warning'),
            indicator: 'orange',
            message: __('App names should not contain spaces. Use underscores instead.')
        });
    }
}
