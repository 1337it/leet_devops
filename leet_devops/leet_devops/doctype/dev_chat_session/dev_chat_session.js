frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add chat interface
            render_chat_interface(frm);
        }
    }
});

function render_chat_interface(frm) {
    // Create chat section
    frm.fields_dict['description'].$wrapper.after(`
        <div class="chat-interface">
            <div class="chat-messages" id="chat-messages-${frm.doc.name}"></div>
            <div class="chat-input-container">
                <textarea 
                    class="form-control" 
                    id="chat-input-${frm.doc.name}" 
                    placeholder="Ask Claude anything about your development needs..."
                    rows="3"
                ></textarea>
                <button 
                    class="btn btn-primary btn-sm" 
                    id="send-btn-${frm.doc.name}"
                    style="margin-top: 10px;"
                >
                    <i class="fa fa-paper-plane"></i> Send Message
                </button>
            </div>
        </div>
    `);
    
    // Load existing messages
    load_messages(frm);
    
    // Bind send button
    $(`#send-btn-${frm.doc.name}`).off('click').on('click', function() {
        send_chat_message(frm);
    });
    
    // Ctrl+Enter to send
    $(`#chat-input-${frm.doc.name}`).off('keydown').on('keydown', function(e) {
        if (e.ctrlKey && e.keyCode === 13) {
            send_chat_message(frm);
        }
    });
}

function load_messages(frm) {
    frappe.call({
        method: 'leet_devops.api.chat.get_messages',
        args: {
            session_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let $container = $(`#chat-messages-${frm.doc.name}`);
                $container.empty();
                
                if (r.message.length === 0) {
                    $container.append(`
                        <div class="empty-chat">
                            <p>No messages yet. Start chatting with Claude!</p>
                        </div>
                    `);
                } else {
                    r.message.forEach(msg => {
                        append_message(frm, msg);
                    });
                    
                    // Scroll to bottom
                    $container.scrollTop($container[0].scrollHeight);
                }
            }
        }
    });
}

function append_message(frm, msg) {
    let $container = $(`#chat-messages-${frm.doc.name}`);
    let message_class = msg.message_type.toLowerCase() + '-message';
    
    let html = `
        <div class="chat-message ${message_class}">
            <div class="message-header">
                <strong>${msg.message_type}</strong>
                <span class="text-muted">${frappe.datetime.str_to_user(msg.timestamp)}</span>
            </div>
            <div class="message-content">${format_message(msg.message)}</div>
        </div>
    `;
    
    $container.append(html);
}

function format_message(message) {
    // Convert code blocks
    message = message.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre><code>${escapeHtml(code)}</code></pre>`;
    });
    
    // Convert inline code
    message = message.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert line breaks
    message = message.replace(/\n/g, '<br>');
    
    return message;
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function send_chat_message(frm) {
    let $input = $(`#chat-input-${frm.doc.name}`);
    let message = $input.val().trim();
    
    if (!message) {
        frappe.msgprint('Please enter a message');
        return;
    }
    
    // Clear input
    $input.val('');
    
    // Show loading
    let $container = $(`#chat-messages-${frm.doc.name}`);
    $container.append(`
        <div class="chat-message loading-message">
            <div class="message-content">
                <i class="fa fa-spinner fa-spin"></i> Thinking...
            </div>
        </div>
    `);
    $container.scrollTop($container[0].scrollHeight);
    
    // Send message
    frappe.call({
        method: 'leet_devops.api.chat.send_message',
        args: {
            session_id: frm.doc.name,
            message: message
        },
        callback: function(r) {
            // Remove loading
            $container.find('.loading-message').remove();
            
            if (r.message && r.message.success) {
                // Reload all messages to show both user and assistant messages
                load_messages(frm);
                
                // Show success
                frappe.show_alert({
                    message: 'Message sent!',
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: 'Error',
                    message: r.message.error || 'Failed to send message',
                    indicator: 'red'
                });
            }
        }
    });
}

// Add button to apply all pending changes in this session
frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Apply All Pending Changes'), function() {
                frappe.confirm(
                    'This will apply all pending code changes from this session. Continue?',
                    () => {
                        frappe.call({
                            method: 'leet_devops.api.code_operations.apply_all_pending_changes',
                            args: {
                                session_id: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message.success) {
                                    let msg = r.message.message;
                                    if (r.message.migrated) {
                                        msg += '<br><br><b>✓ Database migrated successfully</b>';
                                    }
                                    
                                    frappe.msgprint({
                                        title: __('Changes Applied'),
                                        message: msg,
                                        indicator: 'green'
                                    });
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
            }, __('Actions'));
        }
    }
});
