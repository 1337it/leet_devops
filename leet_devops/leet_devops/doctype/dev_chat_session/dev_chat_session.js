/**
 * leet_devops/leet_devops/doctype/dev_chat_session/dev_chat_session.js
 * Client script for Dev Chat Session form
 * ADD THIS CODE to your existing dev_chat_session.js file
 */

frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        // Show child sessions if this is a parent session
        if (frm.doc.name) {
            load_child_sessions(frm);
        }
        
        // Add custom button to open chat interface
        if (!frm.is_new()) {
            frm.add_custom_button(__('Open Chat'), function() {
                // Implement your chat page route here
                // Example: frappe.set_route('chat', frm.doc.name);
                frappe.msgprint({
                    title: 'Chat Interface',
                    message: 'Implement your chat page route here',
                    indicator: 'blue'
                });
            });
        }
        
        // If this is a child session, add button to go to parent
        if (frm.doc.parent_session) {
            frm.add_custom_button(__('Go to Parent Session'), function() {
                frappe.set_route('Form', 'Dev Chat Session', frm.doc.parent_session);
            }, __('Actions'));
        }
        
        // Show target doctype info
        if (frm.doc.target_doctype) {
            frm.dashboard.add_indicator(
                __('Target: {0}', [frm.doc.target_doctype]),
                'blue'
            );
        }
        
        if (frm.doc.action_type) {
            frm.dashboard.add_indicator(
                __('Action: {0}', [frm.doc.action_type]),
                frm.doc.action_type === 'create' ? 'green' : 
                frm.doc.action_type === 'modify' ? 'orange' : 'red'
            );
        }
    }
});

function load_child_sessions(frm) {
    frappe.call({
        method: 'leet_devops.api.chat.get_child_sessions',
        args: {
            parent_session: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                render_child_sessions(frm, r.message);
            }
        }
    });
}

function render_child_sessions(frm, sessions) {
    let wrapper = frm.fields_dict.child_sessions_html.$wrapper;
    
    if (sessions.length === 0) {
        wrapper.html('<p class="text-muted">No child sessions</p>');
        return;
    }
    
    let html = '<div class="child-sessions-container">';
    html += '<h4 style="margin-bottom: 15px;">Child Sessions (' + sessions.length + ')</h4>';
    
    sessions.forEach(function(session) {
        let status_color = session.status === 'Active' ? '#4CAF50' : '#9E9E9E';
        let action_badge = get_action_badge(session.action_type);
        
        html += '<div class="child-session-card" style="border: 1px solid #d1d8dd; padding: 12px; margin: 8px 0; border-radius: 6px; background: #fff;">';
        html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
        html += '<div style="flex: 1;">';
        html += '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">';
        html += '<strong style="font-size: 14px;">' + session.target_doctype + '</strong>';
        html += action_badge;
        html += '</div>';
        html += '<small style="color: #6c757d; font-size: 12px;">Session: ' + session.name + '</small>';
        html += '</div>';
        html += '<div style="display: flex; gap: 8px;">';
        html += '<span class="indicator-pill ' + (session.status === 'Active' ? 'green' : 'gray') + '" style="margin-right: 8px;">';
        html += session.status + '</span>';
        html += '<button class="btn btn-xs btn-default" onclick="frappe.set_route(\'Form\', \'Dev Chat Session\', \'' + session.name + '\')">';
        html += '<i class="fa fa-external-link"></i> Open</button>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
    });
    
    html += '</div>';
    
    wrapper.html(html);
}

function get_action_badge(action) {
    const badges = {
        'create': '<span class="badge badge-success" style="font-size: 10px;">CREATE</span>',
        'modify': '<span class="badge badge-warning" style="font-size: 10px;">MODIFY</span>',
        'delete': '<span class="badge badge-danger" style="font-size: 10px;">DELETE</span>'
    };
    return badges[action] || '';
}
