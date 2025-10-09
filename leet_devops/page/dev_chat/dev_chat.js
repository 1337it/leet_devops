frappe.pages['dev-chat'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Dev Chat',
        single_column: true
    });
    
    // Add primary action button
    page.set_primary_action('New Session', function() {
        create_new_session(page);
    }, 'octicon octicon-plus');
    
    // Add secondary action for session list
    page.add_menu_item('View All Sessions', function() {
        frappe.set_route('List', 'Dev Chat Session');
    }, true);
    
    // Add help menu
    page.add_menu_item('Help', function() {
        show_help_dialog();
    }, true);
    
    // Get session ID from route
    const session_id = frappe.get_route()[1];
    
    if (!session_id) {
        // Show session selector or create new
        show_session_selector(page);
    } else {
        // Load chat interface
        load_chat_interface(page, session_id);
    }
};

function show_session_selector(page) {
    // Get recent sessions
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Dev Chat Session',
            filters: {
                status: 'Active'
            },
            fields: ['name', 'session_name', 'created_at', 'description'],
            order_by: 'modified desc',
            limit: 10
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Show session list
                render_session_list(page, r.message);
            } else {
                // Create first session automatically
                create_default_session(page);
            }
        }
    });
}

function render_session_list(page, sessions) {
    const html = `
        
            
                Select a Chat Session
                Choose an existing session or create a new one
            
            
                ${sessions.map(session => `
                    
                        
                            ${session.session_name}
                            ${frappe.datetime.prettyDate(session.created_at)}
                        
                        ${session.description ? `${session.description}` : ''}
                    
                `).join('')}
            
        
    `;
    
    $(page.body).html(html);
    
    // Bind click events
    $('.session-item').on('click', function() {
        const session_id = $(this).data('session-id');
        frappe.set_route('dev-chat', session_id);
    });
}

function create_default_session(page) {
    frappe.call({
        method: 'leet_devops.api.chat.create_session',
        args: {
            session_name: 'Default Session',
            description: 'Initial development chat session'
        },
        callback: function(r) {
            if (r.message.success) {
                frappe.set_route('dev-chat', r.message.session_id);
            } else {
                frappe.msgprint('Error creating session: ' + r.message.error);
            }
        }
    });
}

function load_chat_interface(page, session_id) {
    // Verify session exists
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Dev Chat Session',
            name: session_id
        },
        callback: function(r) {
            if (r.message) {
                page.set_title('Dev Chat - ' + r.message.session_name);
                
                // Initialize chat interface
                new leet_devops.DevChat(page.body, session_id);
            } else {
                frappe.msgprint('Session not found');
                frappe.set_route('dev-chat');
            }
        }
    });
}

function create_new_session(page) {
    frappe.prompt([
        {
            fieldname: 'session_name',
            label: 'Session Name',
            fieldtype: 'Data',
            reqd: 1,
            default: 'New Development Session'
        },
        {
            fieldname: 'description',
            label: 'Description',
            fieldtype: 'Small Text',
            description: 'What are you working on?'
        }
    ], function(values) {
        frappe.call({
            method: 'leet_devops.api.chat.create_session',
            args: values,
            callback: function(r) {
                if (r.message.success) {
                    frappe.set_route('dev-chat', r.message.session_id);
                    frappe.show_alert({
                        message: 'Session created successfully',
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint('Error creating session: ' + r.message.error);
                }
            }
        });
    }, 'Create New Session', 'Create');
}

function show_help_dialog() {
    const help_html = `
        
            How to use Dev Chat
            
                Start a conversation: Type your question or request in the input box
                Get AI assistance: Claude will help you with Frappe development tasks
                Review changes: Any code changes will appear with Apply/Reject buttons
                Apply changes: Test changes locally before confirming
                Revert if needed: You can always revert applied changes
            
            
            Example prompts:
            
                "Create a new DocType for managing customer feedback"
                "Add a custom API endpoint to export sales data"
                "Create a client script to validate phone numbers"
                "Help me create a dashboard for project tracking"
            
            
            Tips:
            
                Be specific about what you want to create or modify
                Mention field types, validations, and requirements clearly
                Always test changes in a development environment first
                Use Ctrl+Enter to send messages quickly
            
        
    `;
    
    frappe.msgprint({
        title: 'Help - Dev Chat',
        message: help_html,
        wide: true
    });
}
