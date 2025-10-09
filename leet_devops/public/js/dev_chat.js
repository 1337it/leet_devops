frappe.provide('leet_devops');

leet_devops.DevChat = class {
    constructor(wrapper, session_id) {
        this.wrapper = wrapper;
        this.session_id = session_id;
        this.messages = [];
        this.make();
        this.load_messages();
    }
    
    make() {
        this.$wrapper = $(this.wrapper);
        this.$wrapper.html(`
            
                
                    Leet DevOps Assistant
                    
                        New Session
                    
                
                
                
                    
                    
                         Send
                    
                
            
        `);
        
        this.bind_events();
    }
    
    bind_events() {
        const me = this;
        
        $('#send-btn').on('click', () => {
            me.send_message();
        });
        
        $('#chat-input').on('keydown', (e) => {
            if (e.ctrlKey && e.keyCode === 13) {
                me.send_message();
            }
        });
        
        $('#new-session-btn').on('click', () => {
            me.create_new_session();
        });
    }
    
    send_message() {
        const message = $('#chat-input').val().trim();
        if (!message) return;
        
        // Clear input
        $('#chat-input').val('');
        
        // Show user message immediately
        this.add_message('User', message);
        
        // Show loading indicator
        const $loading = this.add_loading_message();
        
        // Call API
        frappe.call({
            method: 'leet_devops.api.chat.send_message',
            args: {
                session_id: this.session_id,
                message: message
            },
            callback: (r) => {
                $loading.remove();
                
                if (r.message.success) {
                    this.add_message('Assistant', r.message.message, r.message.code_changes);
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
    
    add_message(type, message, code_changes = []) {
        const $messages = $('#chat-messages');
        const timestamp = frappe.datetime.now_datetime();
        
        const $message = $(`
            
                
                    ${type}
                    ${frappe.datetime.prettyDate(timestamp)}
                
                ${this.format_message(message)}
            
        `);
        
        // Add code changes if any
        if (code_changes && code_changes.length > 0) {
            const $changes = $('');
            code_changes.forEach(change => {
                $changes.append(this.render_code_change(change));
            });
            $message.append($changes);
        }
        
        $messages.append($message);
        $messages.scrollTop($messages[0].scrollHeight);
        
        return $message;
    }
    
    add_loading_message() {
        const $messages = $('#chat-messages');
        const $loading = $(`
            
                
                    Assistant
                
                
                     Thinking...
                
            
        `);
        $messages.append($loading);
        $messages.scrollTop($messages[0].scrollHeight);
        return $loading;
    }
    
    format_message(message) {
        // Convert markdown-style code blocks to HTML
        message = message.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `${this.escape_html(code)}`;
        });
        
        // Convert inline code
        message = message.replace(/`([^`]+)`/g, '$1');
        
        // Convert line breaks
        message = message.replace(/\n/g, '');
        
        return message;
    }
    
    escape_html(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    render_code_change(change) {
        return $(`
            
                
                    ${change.change_type}
                    ${change.file_path}
                    ${change.status}
                
                ${this.escape_html(change.modified_code)}
                ${change.status === 'Pending' ? `
                    
                        
                             Apply
                        
                        
                             Reject
                        
                    
                ` : ''}
            
        `);
    }
    
    get_status_color(status) {
        const colors = {
            'Pending': 'warning',
            'Applied': 'success',
            'Rejected': 'danger',
            'Reverted': 'secondary'
        };
        return colors[status] || 'secondary';
    }
    
    load_messages() {
        frappe.call({
            method: 'leet_devops.api.chat.get_messages',
            args: {
                session_id: this.session_id
            },
            callback: (r) => {
                if (r.message) {
                    r.message.forEach(msg => {
                        this.add_message(
                            msg.message_type,
                            msg.message,
                            msg.code_changes || []
                        );
                    });
                }
            }
        });
    }
    
    create_new_session() {
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
        ], (values) => {
            frappe.call({
                method: 'leet_devops.api.chat.create_session',
                args: values,
                callback: (r) => {
                    if (r.message.success) {
                        frappe.set_route('dev-chat', r.message.session_id);
                    } else {
                        frappe.msgprint('Error creating session: ' + r.message.error);
                    }
                }
            });
        }, 'Create New Session', 'Create');
    }
};

// Page script
frappe.pages['dev-chat'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Dev Chat',
        single_column: true
    });
    
    const session_id = frappe.get_route()[1];
    
    if (!session_id) {
        // Create first session
        frappe.call({
            method: 'leet_devops.api.chat.create_session',
            args: {
                session_name: 'Default Session',
                description: 'Initial development chat'
            },
            callback: (r) => {
                if (r.message.success) {
                    frappe.set_route('dev-chat', r.message.session_id);
                }
            }
        });
        return;
    }
    
    new leet_devops.DevChat(page.body, session_id);
};
