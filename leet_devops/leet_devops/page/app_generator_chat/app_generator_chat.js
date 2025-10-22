frappe.pages['app-generator-chat'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'App Generator Chat',
        single_column: true
    });

    // Add primary action button for new session
    page.set_primary_action('New Session', () => {
        create_new_session(page);
    });

    // Add secondary action for settings
    page.add_menu_item('Settings', () => {
        frappe.set_route('Form', 'Claude AI Settings');
    });

    // Create the chat interface
    page.chat_interface = new AppGeneratorChat(page);
}

class AppGeneratorChat {
    constructor(page) {
        this.page = page;
        this.wrapper = $(page.body);
        this.current_session = null;
        this.current_doctype_session = null;
        
        this.setup();
    }

    setup() {
        // Clear any existing content
        this.wrapper.empty();

        // Create main container
        this.wrapper.append(`
            <div class="app-generator-container">
                <div class="row">
                    <div class="col-md-3 sessions-sidebar">
                        <div class="session-list-header">
                            <h5>Sessions</h5>
                        </div>
                        <div class="session-list"></div>
                    </div>
                    <div class="col-md-6 chat-main">
                        <div class="chat-header">
                            <h5 class="session-title">Select a session to start</h5>
                        </div>
                        <div class="chat-messages"></div>
                        <div class="chat-input-container">
                            <textarea class="form-control chat-input" 
                                placeholder="Type your message here..." 
                                rows="3"></textarea>
                            <button class="btn btn-primary btn-send-message">
                                <i class="fa fa-paper-plane"></i> Send
                            </button>
                        </div>
                    </div>
                    <div class="col-md-3 doctype-sidebar">
                        <div class="doctype-list-header">
                            <h5>DocType Sessions</h5>
                        </div>
                        <div class="doctype-list"></div>
                        <div class="pending-changes">
                            <h6>Pending Changes</h6>
                            <div class="changes-list"></div>
                            <button class="btn btn-success btn-apply-changes" 
                                style="display:none; width:100%; margin-top:10px;">
                                Apply Changes
                            </button>
                            <button class="btn btn-info btn-verify-files" 
                                style="display:none; width:100%; margin-top:5px;">
                                Verify Files
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `);

        // Add CSS
        this.add_styles();

        // Load sessions
        this.load_sessions();

        // Setup event handlers
        this.setup_event_handlers();
    }

    add_styles() {
        const style = `
            <style>
                .app-generator-container {
                    height: calc(100vh - 150px);
                    padding: 15px;
                }
                
                .sessions-sidebar, .doctype-sidebar {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    height: 100%;
                    overflow-y: auto;
                }
                
                .chat-main {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    padding: 0 15px;
                }
                
                .chat-header {
                    padding: 15px;
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 8px 8px 0 0;
                }
                
                .chat-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    background: #fff;
                    border-left: 1px solid #ddd;
                    border-right: 1px solid #ddd;
                }
                
                .chat-input-container {
                    padding: 15px;
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 0 0 8px 8px;
                }
                
                .chat-input {
                    margin-bottom: 10px;
                }
                
                .message {
                    margin-bottom: 20px;
                    padding: 12px;
                    border-radius: 8px;
                }
                
                .message.user {
                    background: #e3f2fd;
                    margin-left: 40px;
                }
                
                .message.assistant {
                    background: #f5f5f5;
                    margin-right: 40px;
                }
                
                .message-role {
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: #666;
                }
                
                .message-content {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                
                .session-item, .doctype-item {
                    padding: 10px;
                    margin-bottom: 8px;
                    background: #fff;
                    border-radius: 6px;
                    cursor: pointer;
                    border: 2px solid transparent;
                    transition: all 0.2s;
                }
                
                .session-item:hover, .doctype-item:hover {
                    border-color: #5e64ff;
                }
                
                .session-item.active, .doctype-item.active {
                    background: #5e64ff;
                    color: #fff;
                }
                
                .session-item-title {
                    font-weight: bold;
                    margin-bottom: 3px;
                }
                
                .session-item-status {
                    font-size: 12px;
                    color: #666;
                }
                
                .session-item.active .session-item-status,
                .doctype-item.active .doctype-item-status {
                    color: #fff;
                }
                
                .pending-changes {
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                }
                
                .file-item {
                    padding: 8px;
                    margin-bottom: 5px;
                    background: #fff;
                    border-radius: 4px;
                    font-size: 12px;
                }
            </style>
        `;
        
        if (!$('#app-generator-styles').length) {
            $('head').append(style);
        }
    }

    setup_event_handlers() {
        // Send message button
        this.wrapper.find('.btn-send-message').on('click', () => {
            this.send_message();
        });

        // Enter key to send
        this.wrapper.find('.chat-input').on('keydown', (e) => {
            if (e.ctrlKey && e.keyCode === 13) {
                this.send_message();
            }
        });

        // Apply changes button
        this.wrapper.find('.btn-apply-changes').on('click', () => {
            this.apply_changes();
        });

        // Verify files button
        this.wrapper.find('.btn-verify-files').on('click', () => {
            this.verify_files();
        });
    }

    load_sessions() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'App Generation Session',
                fields: ['name', 'session_title', 'status', 'app_name'],
                order_by: 'modified desc',
                limit_page_length: 20
            },
            callback: (r) => {
                const sessions_list = this.wrapper.find('.session-list');
                sessions_list.empty();

                if (r.message && r.message.length > 0) {
                    r.message.forEach(session => {
                        sessions_list.append(`
                            <div class="session-item" data-name="${session.name}">
                                <div class="session-item-title">${session.session_title}</div>
                                <div class="session-item-status">
                                    ${session.app_name || 'No app'} - ${session.status}
                                </div>
                            </div>
                        `);
                    });

                    // Add click handlers
                    sessions_list.find('.session-item').on('click', (e) => {
                        const session_name = $(e.currentTarget).data('name');
                        this.load_session(session_name);
                    });
                } else {
                    sessions_list.append('<p class="text-muted">No sessions yet</p>');
                }
            }
        });
    }

    load_session(session_name) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'App Generation Session',
                name: session_name
            },
            callback: (r) => {
                if (r.message) {
                    this.current_session = r.message;
                    this.current_doctype_session = null;
                    
                    // Update UI
                    this.wrapper.find('.session-item').removeClass('active');
                    this.wrapper.find(`.session-item[data-name="${session_name}"]`).addClass('active');
                    
                    this.wrapper.find('.session-title').text(r.message.session_title);
                    
                    // Load chat messages
                    this.display_messages(r.message.chat_messages || []);
                    
                    // Load DocType sessions
                    this.display_doctype_sessions(r.message.doctype_sessions || []);
                    
                    // Show pending changes
                    this.display_pending_changes(r.message);
                }
            }
        });
    }

    display_messages(messages) {
        const chat_messages = this.wrapper.find('.chat-messages');
        chat_messages.empty();

        messages.forEach(msg => {
            chat_messages.append(`
                <div class="message ${msg.role}">
                    <div class="message-role">${msg.role === 'user' ? 'You' : 'Claude'}</div>
                    <div class="message-content">${frappe.utils.escape_html(msg.message)}</div>
                </div>
            `);
        });

        // Scroll to bottom
        chat_messages.scrollTop(chat_messages[0].scrollHeight);
    }

    display_doctype_sessions(sessions) {
        const doctype_list = this.wrapper.find('.doctype-list');
        doctype_list.empty();

        if (sessions && sessions.length > 0) {
            sessions.forEach(session => {
                doctype_list.append(`
                    <div class="doctype-item" data-doctype="${session.doctype_name}">
                        <div class="session-item-title">${session.doctype_name}</div>
                        <div class="doctype-item-status">${session.status}</div>
                    </div>
                `);
            });

            // Add click handlers
            doctype_list.find('.doctype-item').on('click', (e) => {
                const doctype_name = $(e.currentTarget).data('doctype');
                this.load_doctype_session(doctype_name);
            });
        } else {
            doctype_list.append('<p class="text-muted">No DocTypes yet</p>');
        }
    }

    load_doctype_session(doctype_name) {
        // Find the DocType session
        const session = this.current_session.doctype_sessions.find(s => s.doctype_name === doctype_name);
        
        if (session) {
            this.current_doctype_session = session;
            
            // Update UI
            this.wrapper.find('.doctype-item').removeClass('active');
            this.wrapper.find(`.doctype-item[data-doctype="${doctype_name}"]`).addClass('active');
            
            this.wrapper.find('.session-title').text(`${this.current_session.session_title} - ${doctype_name}`);
            
            // Load DocType messages
            if (session.messages) {
                const messages = JSON.parse(session.messages);
                this.display_doctype_messages(messages);
            } else {
                this.wrapper.find('.chat-messages').empty();
            }
        }
    }

    display_doctype_messages(messages) {
        const chat_messages = this.wrapper.find('.chat-messages');
        chat_messages.empty();

        messages.forEach(msg => {
            chat_messages.append(`
                <div class="message ${msg.role}">
                    <div class="message-role">${msg.role === 'user' ? 'You' : 'Claude'}</div>
                    <div class="message-content">${frappe.utils.escape_html(msg.content)}</div>
                </div>
            `);
        });

        // Scroll to bottom
        chat_messages.scrollTop(chat_messages[0].scrollHeight);
    }

    display_pending_changes(session) {
        const changes_list = this.wrapper.find('.changes-list');
        changes_list.empty();

        if (session.has_pending_changes) {
            if (session.files_to_create && session.files_to_create.length > 0) {
                changes_list.append('<div style="margin-bottom:10px;"><strong>Files to Create:</strong></div>');
                session.files_to_create.forEach(file => {
                    changes_list.append(`
                        <div class="file-item">
                            📄 ${file.file_path}
                            ${file.related_doctype ? `<br><small>DocType: ${file.related_doctype}</small>` : ''}
                        </div>
                    `);
                });
            }

            if (session.files_to_modify && session.files_to_modify.length > 0) {
                changes_list.append('<div style="margin-bottom:10px; margin-top:10px;"><strong>Files to Modify:</strong></div>');
                session.files_to_modify.forEach(file => {
                    changes_list.append(`
                        <div class="file-item">
                            ✏️ ${file.file_path}
                        </div>
                    `);
                });
            }

            this.wrapper.find('.btn-apply-changes').show();
            this.wrapper.find('.btn-verify-files').show();
        } else {
            changes_list.append('<p class="text-muted">No pending changes</p>');
            this.wrapper.find('.btn-apply-changes').hide();
            this.wrapper.find('.btn-verify-files').hide();
        }
    }

    send_message() {
        const input = this.wrapper.find('.chat-input');
        const message = input.val().trim();

        if (!message) {
            frappe.msgprint('Please enter a message');
            return;
        }

        if (!this.current_session) {
            frappe.msgprint('Please select or create a session first');
            return;
        }

        // Disable input
        input.prop('disabled', true);
        this.wrapper.find('.btn-send-message').prop('disabled', true);

        // Determine which API to call based on context
        let method, args;
        
        if (this.current_doctype_session) {
            // Sending to DocType session
            method = 'leet_devops.leet_devops.doctype.doctype_generation_session.doctype_generation_session.send_doctype_message';
            args = {
                parent: this.current_session.name,
                doctype_name: this.current_doctype_session.doctype_name,
                message: message
            };
        } else {
            // Sending to main session
            method = 'leet_devops.leet_devops.doctype.app_generation_session.app_generation_session.send_message';
            args = {
                session_name: this.current_session.name,
                message: message
            };
        }

        frappe.call({
            method: method,
            args: args,
            callback: (r) => {
                if (r.message && r.message.success) {
                    // Clear input
                    input.val('');
                    
                    // Reload session to show new messages
                    this.load_session(this.current_session.name);
                    
                    // Re-select doctype session if needed
                    if (this.current_doctype_session) {
                        setTimeout(() => {
                            this.load_doctype_session(this.current_doctype_session.doctype_name);
                        }, 500);
                    }
                }
            },
            always: () => {
                // Re-enable input
                input.prop('disabled', false);
                this.wrapper.find('.btn-send-message').prop('disabled', false);
                input.focus();
            }
        });
    }

    apply_changes() {
        if (!this.current_session) {
            return;
        }

        frappe.confirm(
            'Are you sure you want to apply all pending changes? This will create/modify files in your app.',
            () => {
                frappe.call({
                    method: 'leet_devops.leet_devops.doctype.app_generation_session.app_generation_session.apply_changes',
                    args: {
                        name: this.current_session.name
                    },
                    callback: (r) => {
                        if (r.message) {
                            if (r.message.success) {
                                frappe.msgprint({
                                    title: 'Changes Applied',
                                    message: 'All changes have been applied successfully',
                                    indicator: 'green'
                                });
                            }
                            
                            // Reload session
                            this.load_session(this.current_session.name);
                        }
                    }
                });
            }
        );
    }

    verify_files() {
        if (!this.current_session) {
            return;
        }

        frappe.call({
            method: 'leet_devops.leet_devops.doctype.app_generation_session.app_generation_session.verify_files',
            args: {
                name: this.current_session.name
            },
            callback: (r) => {
                if (r.message) {
                    // Create a dialog to show verification results
                    const d = new frappe.ui.Dialog({
                        title: 'File Verification Results',
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'results_html'
                            }
                        ]
                    });

                    let html = '<table class="table table-bordered"><thead><tr><th>File</th><th>Operation</th><th>Status</th></tr></thead><tbody>';
                    
                    r.message.forEach(result => {
                        const status_class = result.exists ? 'text-success' : 'text-danger';
                        html += `<tr>
                            <td>${result.file_path}</td>
                            <td>${result.operation}</td>
                            <td class="${status_class}">${result.status}</td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    
                    d.fields_dict.results_html.$wrapper.html(html);
                    d.show();
                }
            }
        });
    }
}

function create_new_session(page) {
    const d = new frappe.ui.Dialog({
        title: 'Create New Session',
        fields: [
            {
                label: 'Session Title',
                fieldname: 'session_title',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: 'App Name (optional)',
                fieldname: 'app_name',
                fieldtype: 'Data',
                description: 'Leave blank to use the app from settings'
            }
        ],
        primary_action_label: 'Create',
        primary_action: (values) => {
            frappe.call({
                method: 'leet_devops.leet_devops.doctype.app_generation_session.app_generation_session.create_new_session',
                args: {
                    title: values.session_title,
                    app_name: values.app_name
                },
                callback: (r) => {
                    if (r.message) {
                        d.hide();
                        frappe.msgprint('Session created successfully');
                        
                        // Reload sessions
                        page.chat_interface.load_sessions();
                        
                        // Load the new session
                        page.chat_interface.load_session(r.message);
                    }
                }
            });
        }
    });

    d.show();
}
