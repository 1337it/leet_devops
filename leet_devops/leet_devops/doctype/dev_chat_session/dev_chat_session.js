frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add chat interface
            render_chat_interface(frm);
            
            // Add "Apply All Changes" button
            frm.add_custom_button(__('Apply All Pending Changes'), function() {
                frappe.confirm(
                    'This will apply all pending code changes from this session. Continue?',
                    () => {
                        frappe.show_alert({
                            message: __('Applying changes...'),
                            indicator: 'blue'
                        });
                        
                        frappe.call({
                            method: 'leet_devops.api.code_operations.apply_all_pending_changes',
                            args: {
                                session_id: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message.success) {
                                    let msg = r.message.message;
                                    if (r.message.migrated) {
                                        msg += '<br><br><b>✓ Database migrated successfully</b><br>Page will refresh in 3 seconds...';
                                    }
                                    
                                    frappe.msgprint({
                                        title: __('Changes Applied'),
                                        message: msg,
                                        indicator: 'green'
                                    });
                                    
                                    if (r.message.migrated) {
                                        setTimeout(() => {
                                            window.location.reload();
                                        }, 3000);
                                    }
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

function render_chat_interface(frm) {
    // Create chat section
    frm.fields_dict['description'].$wrapper.after(`
        <div class="chat-interface">
            <div class="chat-messages" id="chat-messages-${frm.doc.name}"></div>
            <div class="chat-input-container">
                <textarea 
                    class="form-control" 
                    id="chat-input-${frm.doc.name}" 
                    placeholder="Ask Claude anything about your development needs... (Ctrl+Enter to send)"
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
    
    let code_changes_html = '';
    if (msg.code_changes && msg.code_changes.length > 0) {
        code_changes_html = `
            <div class="code-changes-summary">
                <strong>📝 ${msg.code_changes.length} code change(s) suggested</strong>
                <ul>
                    ${msg.code_changes.map(c => `
                        <li>
                            <a href="/app/Form/Code%20Change/${c.name}" target="_blank">
                                ${c.change_type}: ${c.file_path}
                            </a>
                            <span class="badge badge-${get_status_color(c.status)}">${c.status}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    let html = `
        <div class="chat-message ${message_class}">
            <div class="message-header">
                <strong>${msg.message_type}</strong>
                <span class="text-muted">${frappe.datetime.str_to_user(msg.timestamp)}</span>
            </div>
            <div class="message-content">${format_message(msg.message)}</div>
            ${code_changes_html}
        </div>
    `;
    
    $container.append(html);
}

function get_status_color(status) {
    const colors = {
        'Pending': 'warning',
        'Applied': 'success',
        'Rejected': 'danger',
        'Reverted': 'secondary'
    };
    return colors[status] || 'secondary';
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

// Add "Preview Changes" button
frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Preview All Changes'), function() {
                show_execution_preview(frm);
            }, __('Actions'));
        }
    }
});

function show_execution_preview(frm) {
    // Get latest message
    frappe.call({
        method: 'leet_devops.api.chat.get_messages',
        args: {
            session_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let latest_msg = r.message[r.message.length - 1];
                
                if (latest_msg.code_changes && latest_msg.code_changes.length > 0) {
                    show_preview_dialog(latest_msg);
                } else {
                    frappe.msgprint('No changes to preview');
                }
            }
        }
    });
}

function show_preview_dialog(message) {
    let changes = message.code_changes;
    
    let html = '<div class="execution-preview">';
    html += '<h4>📋 Execution Plan</h4>';
    html += `<p><strong>Total Actions:</strong> ${changes.length}</p>`;
    html += '<hr>';
    
    // Group by type
    let file_changes = changes.filter(c => !c.is_command);
    let commands = changes.filter(c => c.is_command);
    
    if (file_changes.length > 0) {
        html += '<h5>📁 File Changes:</h5><ul>';
        file_changes.forEach(change => {
            let icon = change.change_type === 'Create' ? '➕' : 
                       change.change_type === 'Modify' ? '✏️' : '🗑️';
            let badge = `<span class="badge badge-${change.status === 'Pending' ? 'warning' : 'success'}">${change.status}</span>`;
            html += `<li>${icon} <strong>${change.change_type}</strong>: ${change.file_path} ${badge}</li>`;
        });
        html += '</ul>';
    }
    
    if (commands.length > 0) {
        html += '<h5>⚡ Commands to Execute:</h5><ul>';
        commands.forEach(cmd => {
            let badge = `<span class="badge badge-${cmd.status === 'Pending' ? 'warning' : 'success'}">${cmd.status}</span>`;
            html += `<li><strong>${cmd.command_type}</strong>: ${cmd.command_description || 'No description'} ${badge}</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    
    frappe.msgprint({
        title: 'Execution Preview',
        message: html,
        wide: true,
        primary_action: {
            label: 'Apply All',
            action: function() {
                apply_all_with_commands(message);
            }
        }
    });
}

function apply_all_with_commands(message) {
    frappe.confirm(
        'This will apply all file changes AND execute all commands. Continue?',
        () => {
            let changes = message.code_changes;
            let total = changes.length;
            let completed = 0;
            let errors = [];
            
            frappe.show_alert({
                message: `Processing ${total} changes...`,
                indicator: 'blue'
            });
            
            // Process each change
            changes.forEach((change, index) => {
                setTimeout(() => {
                    let method = change.is_command ? 
                        'leet_devops.api.command_executor.execute_command' : 
                        'leet_devops.api.code_operations.apply_code_change';
                    
                    frappe.call({
                        method: method,
                        args: {
                            change_name: change.name
                        },
                        callback: function(r) {
                            completed++;
                            
                            if (!r.message || !r.message.success) {
                                errors.push(`${change.name}: ${r.message ? r.message.error : 'Unknown error'}`);
                            }
                            
                            if (completed === total) {
                                // All done
                                if (errors.length === 0) {
                                    frappe.msgprint({
                                        title: 'Success',
                                        message: `All ${total} changes applied successfully! Page will refresh in 3 seconds...`,
                                        indicator: 'green'
                                    });
                                    
                                    setTimeout(() => {
                                        window.location.reload();
                                    }, 3000);
                                } else {
                                    frappe.msgprint({
                                        title: 'Completed with Errors',
                                        message: `Completed ${completed - errors.length} of ${total} successfully.<br><br>Errors:<br>${errors.join('<br>')}`,
                                        indicator: 'orange'
                                    });
                                }
                            } else {
                                frappe.show_progress('Applying changes', completed, total);
                            }
                        }
                    });
                }, index * 500); // Stagger by 500ms
            });
        }
    );
}
