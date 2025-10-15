/**
 * leet_devops/leet_devops/public/js/chat.js
 * Frontend JavaScript for Claude Streaming + Multi-DocType Sessions
 */

frappe.provide('leet_devops.chat');

leet_devops.chat = {
    current_session: null,
    streaming_active: false,
    stream_buffer: '',
    
    init: function(session_id) {
        this.current_session = session_id;
        this.setup_streaming_listener();
        this.load_messages();
    },
    
    setup_streaming_listener: function() {
        frappe.realtime.on('claude_stream', (data) => {
            this.handle_stream_event(data);
        });
    },
    
    handle_stream_event: function(data) {
        if (data.session_id !== this.current_session) {
            return;
        }
        
        if (data.status === 'started') {
            this.on_stream_start();
        }
        else if (data.error) {
            this.on_stream_error(data.error);
        }
        else if (data.done) {
            this.on_stream_complete(data);
        }
        else if (data.chunk) {
            this.on_stream_chunk(data.chunk);
        }
    },
    
    on_stream_start: function() {
        this.streaming_active = true;
        this.stream_buffer = '';
        
        let messages_area = $('.chat-messages');
        messages_area.append(`
            <div class="message assistant-message streaming" id="streaming-message">
                <div class="message-avatar">
                    <span class="avatar avatar-small">
                        <span class="avatar-frame" style="background-color: #4CAF50">
                            <span>AI</span>
                        </span>
                    </span>
                </div>
                <div class="message-content">
                    <div class="message-text"></div>
                    <div class="streaming-indicator">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            </div>
        `);
        
        messages_area.scrollTop(messages_area[0].scrollHeight);
        $('.send-message-btn').prop('disabled', true);
    },
    
    on_stream_chunk: function(chunk) {
        if (!this.streaming_active) return;
        
        this.stream_buffer += chunk;
        
        let message_text = $('#streaming-message .message-text');
        message_text.html(this.format_message(this.stream_buffer));
        
        let messages_area = $('.chat-messages');
        messages_area.scrollTop(messages_area[0].scrollHeight);
    },
    
    on_stream_complete: function(data) {
        this.streaming_active = false;
        
        $('#streaming-message .streaming-indicator').remove();
        $('#streaming-message').removeClass('streaming');
        $('#streaming-message').removeAttr('id');
        
        $('.message.assistant-message:last .message-text').html(
            this.format_message(this.stream_buffer)
        );
        
        if (data.code_changes && data.code_changes.length > 0) {
            this.display_code_changes(data.code_changes);
        }
        
        if (data.created_sessions) {
            this.display_child_sessions(data.created_sessions);
        }
        
        $('.send-message-btn').prop('disabled', false);
        this.stream_buffer = '';
    },
    
    on_stream_error: function(error) {
        this.streaming_active = false;
        
        $('#streaming-message .streaming-indicator').remove();
        
        $('#streaming-message .message-text').html(`
            <div class="alert alert-danger">
                <strong>Error:</strong> ${error}
            </div>
        `);
        
        $('#streaming-message').removeClass('streaming');
        $('#streaming-message').removeAttr('id');
        
        $('.send-message-btn').prop('disabled', false);
    },
    
    send_message: function(message) {
        if (!message || this.streaming_active) return;
        
        this.append_user_message(message);
        $('.chat-input').val('');
        
        frappe.call({
            method: 'leet_devops.api.chat.send_message',
            args: {
                session_id: this.current_session,
                message: message,
                auto_detect_doctypes: true
            },
            callback: (r) => {
                if (!r.message.success) {
                    frappe.msgprint({
                        title: 'Error',
                        message: r.message.error,
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    append_user_message: function(message) {
        let messages_area = $('.chat-messages');
        let user_initial = frappe.user_info(frappe.session.user).fullname.charAt(0).toUpperCase();
        
        messages_area.append(`
            <div class="message user-message">
                <div class="message-avatar">
                    <span class="avatar avatar-small">
                        <span class="avatar-frame">
                            <span>${user_initial}</span>
                        </span>
                    </span>
                </div>
                <div class="message-content">
                    <div class="message-text">${frappe.utils.escape_html(message)}</div>
                </div>
            </div>
        `);
        messages_area.scrollTop(messages_area[0].scrollHeight);
    },
    
    format_message: function(text) {
        // Code blocks
        text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
            return `<pre><code class="language-${lang || 'text'}">${frappe.utils.escape_html(code)}</code></pre>`;
        });
        
        // Inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Lists
        text = text.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    },
    
    display_code_changes: function(changes) {
        let container = $('.message.assistant-message:last .message-content');
        
        let html = '<div class="code-changes-container">';
        html += '<h4>Code Changes</h4>';
        
        changes.forEach((change, index) => {
            if (change.is_command) {
                html += `
                    <div class="code-change command">
                        <div class="change-header">
                            <span class="badge badge-info">${change.command_type}</span>
                            <span class="change-description">${change.command_description}</span>
                        </div>
                        <pre><code>${frappe.utils.escape_html(change.command_code)}</code></pre>
                        <button class="btn btn-sm btn-primary execute-command" 
                                data-index="${index}">
                            Execute
                        </button>
                    </div>
                `;
            } else {
                html += `
                    <div class="code-change">
                        <div class="change-header">
                            <span class="badge ${this.get_change_badge_class(change.change_type)}">
                                ${change.change_type}
                            </span>
                            <span class="file-path">${change.file_path}</span>
                        </div>
                        <pre><code>${frappe.utils.escape_html(change.modified_code)}</code></pre>
                        <button class="btn btn-sm btn-success apply-change" 
                                data-index="${index}">
                            Apply Change
                        </button>
                    </div>
                `;
            }
        });
        
        html += '</div>';
        container.append(html);
        
        this.attach_code_change_handlers();
    },
    
    display_child_sessions: function(sessions) {
        let container = $('.message.assistant-message:last .message-content');
        
        let html = '<div class="child-sessions-container">';
        html += '<h4>Created Sessions</h4>';
        html += '<div class="sessions-grid">';
        
        sessions.forEach(session => {
            html += `
                <div class="session-card">
                    <div class="session-icon">📋</div>
                    <div class="session-info">
                        <strong>${session.doctype_name}</strong>
                        <small>${session.action}</small>
                    </div>
                    <button class="btn btn-xs btn-default open-session" 
                            data-session="${session.session_id}">
                        Open
                    </button>
                </div>
            `;
        });
        
        html += '</div></div>';
        container.append(html);
        
        $('.open-session').on('click', function() {
            let session_id = $(this).data('session');
            frappe.set_route('Form', 'Dev Chat Session', session_id);
        });
    },
    
    get_change_badge_class: function(type) {
        const classes = {
            'Create': 'badge-success',
            'Modify': 'badge-warning',
            'Delete': 'badge-danger'
        };
        return classes[type] || 'badge-secondary';
    },
    
    attach_code_change_handlers: function() {
        $('.apply-change').on('click', function() {
            frappe.msgprint('Apply change functionality - implement your logic here');
        });
        
        $('.execute-command').on('click', function() {
            frappe.msgprint('Execute command functionality - implement your logic here');
        });
    },
    
    load_messages: function() {
        frappe.call({
            method: 'leet_devops.api.chat.get_messages',
            args: {
                session_id: this.current_session
            },
            callback: (r) => {
                if (r.message) {
                    this.render_messages(r.message);
                }
            }
        });
    },
    
    render_messages: function(messages) {
        let container = $('.chat-messages');
        container.empty();
        
        messages.forEach(msg => {
            if (msg.message_type === 'System') return;
            
            let is_user = msg.message_type === 'User';
            let user_initial = frappe.user_info(frappe.session.user).fullname.charAt(0).toUpperCase();
            
            let html = `
                <div class="message ${is_user ? 'user-message' : 'assistant-message'}">
                    <div class="message-avatar">
                        <span class="avatar avatar-small">
                            <span class="avatar-frame" ${!is_user ? 'style="background-color: #4CAF50"' : ''}>
                                <span>${is_user ? user_initial : 'AI'}</span>
                            </span>
                        </span>
                    </div>
                    <div class="message-content">
                        <div class="message-text">${this.format_message(msg.message)}</div>
                    </div>
                </div>
            `;
            container.append(html);
            
            if (msg.code_changes && msg.code_changes.length > 0) {
                this.display_code_changes(msg.code_changes);
            }
        });
        
        container.scrollTop(container[0].scrollHeight);
    }
};

// Initialize on page load
$(document).ready(function() {
    $('.send-message-btn').on('click', function() {
        let message = $('.chat-input').val().trim();
        if (message) {
            leet_devops.chat.send_message(message);
        }
    });
    
    $('.chat-input').on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            let message = $(this).val().trim();
            if (message) {
                leet_devops.chat.send_message(message);
            }
        }
    });
});
