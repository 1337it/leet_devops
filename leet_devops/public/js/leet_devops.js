// Main Leet DevOps JavaScript

frappe.provide('leet_devops');

leet_devops.ChatInterface = class {
    constructor(wrapper, session_id) {
        this.wrapper = wrapper;
        this.session_id = session_id;
        this.messages = [];
        this.init();
    }

    init() {
        this.setup_layout();
        this.load_messages();
        this.setup_realtime();
    }

    setup_layout() {
        this.wrapper.html(`
            <div class="leet-devops-chat">
                <div class="chat-header">
                    <h3 class="session-title"></h3>
                    <div class="session-actions">
                        <button class="btn btn-sm btn-secondary child-sessions-btn">
                            Child Sessions
                        </button>
                    </div>
                </div>
                <div class="chat-messages"></div>
                <div class="chat-input-wrapper">
                    <textarea class="form-control chat-input" 
                              placeholder="Type your message here..." 
                              rows="3"></textarea>
                    <button class="btn btn-primary btn-send">
                        <i class="fa fa-paper-plane"></i> Send
                    </button>
                </div>
            </div>
        `);

        this.messages_container = this.wrapper.find('.chat-messages');
        this.input = this.wrapper.find('.chat-input');
        this.send_btn = this.wrapper.find('.btn-send');
        this.child_sessions_btn = this.wrapper.find('.child-sessions-btn');

        this.setup_events();
    }

    setup_events() {
        const me = this;

        this.send_btn.on('click', () => {
            me.send_message();
        });

        this.input.on('keydown', (e) => {
            if (e.ctrlKey && e.keyCode === 13) { // Ctrl + Enter
                me.send_message();
            }
        });

        this.child_sessions_btn.on('click', () => {
            me.show_child_sessions();
        });
    }

    setup_realtime() {
        const me = this;
        
        frappe.realtime.on('claude_response', (data) => {
            if (data.session_id === me.session_id) {
                if (data.done) {
                    me.finalize_message(data.message_id);
                } else {
                    me.append_streaming_content(data.content);
                }
            }
        });
    }

    send_message() {
        const message = this.input.val().trim();
        if (!message) return;

        this.add_message('User', message, 'user');
        this.input.val('');
        this.send_btn.prop('disabled', true);

        // Create placeholder for assistant response
        this.create_streaming_placeholder();

        frappe.call({
            method: 'leet_devops.api.claude_api.send_message',
            args: {
                session_id: this.session_id,
                message: message,
                stream: true
            },
            callback: (r) => {
                this.send_btn.prop('disabled', false);
                this.input.focus();
            },
            error: () => {
                this.send_btn.prop('disabled', false);
                this.remove_streaming_placeholder();
                frappe.msgprint('Failed to send message');
            }
        });
    }

    create_streaming_placeholder() {
        const msg_html = `
            <div class="message assistant streaming" data-streaming="true">
                <div class="message-header">
                    <strong>Claude</strong>
                    <span class="message-time">${frappe.datetime.now_time()}</span>
                </div>
                <div class="message-content streaming-content">
                    <span class="typing-indicator">●●●</span>
                </div>
            </div>
        `;
        this.messages_container.append(msg_html);
        this.scroll_to_bottom();
    }

    append_streaming_content(content) {
        const streaming_msg = this.messages_container.find('.message.streaming[data-streaming="true"]');
        if (streaming_msg.length) {
            let content_div = streaming_msg.find('.streaming-content');
            let current_content = content_div.text().replace('●●●', '');
            content_div.html(current_content + content);
            this.scroll_to_bottom();
        }
    }

    finalize_message(message_id) {
        const streaming_msg = this.messages_container.find('.message.streaming[data-streaming="true"]');
        if (streaming_msg.length) {
            streaming_msg.removeClass('streaming');
            streaming_msg.removeAttr('data-streaming');
            streaming_msg.find('.streaming-content').removeClass('streaming-content');
        }
        
        // Reload child sessions in case new ones were created
        this.load_child_sessions_badge();
    }

    remove_streaming_placeholder() {
        this.messages_container.find('.message.streaming[data-streaming="true"]').remove();
    }

    add_message(sender, content, type) {
        const msg_html = `
            <div class="message ${type}">
                <div class="message-header">
                    <strong>${sender}</strong>
                    <span class="message-time">${frappe.datetime.now_time()}</span>
                </div>
                <div class="message-content">${this.format_content(content)}</div>
            </div>
        `;
        this.messages_container.append(msg_html);
        this.scroll_to_bottom();
    }

    format_content(content) {
        // Basic markdown-like formatting
        // Enhance this as needed
        return content
            .replace(/\n/g, '<br>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');
    }

    scroll_to_bottom() {
        this.messages_container.scrollTop(this.messages_container[0].scrollHeight);
    }

    load_messages() {
        const me = this;
        frappe.call({
            method: 'leet_devops.api.claude_api.get_session_messages',
            args: { session_id: this.session_id },
            callback: (r) => {
                if (r.message) {
                    me.messages_container.empty();
                    r.message.forEach(msg => {
                        const type = msg.message_type === 'User' ? 'user' : 'assistant';
                        me.add_message(msg.sender, msg.message_content, type);
                    });
                }
            }
        });
    }

    load_child_sessions_badge() {
        frappe.call({
            method: 'leet_devops.api.claude_api.get_child_sessions',
            args: { parent_session_id: this.session_id },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    this.child_sessions_btn.html(`
                        Child Sessions <span class="badge">${r.message.length}</span>
                    `);
                }
            }
        });
    }

    show_child_sessions() {
        const me = this;
        frappe.call({
            method: 'leet_devops.api.claude_api.get_child_sessions',
            args: { parent_session_id: this.session_id },
            callback: (r) => {
                if (r.message) {
                    me.render_child_sessions_dialog(r.message);
                }
            }
        });
    }

    render_child_sessions_dialog(sessions) {
        const d = new frappe.ui.Dialog({
            title: 'Child Sessions',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'sessions_html'
                }
            ]
        });

        let html = '<div class="child-sessions-list">';
        sessions.forEach(session => {
            html += `
                <div class="child-session-item" data-session="${session.name}">
                    <div class="session-info">
                        <strong>${session.title}</strong>
                        <span class="badge">${session.session_type}</span>
                    </div>
                    <div class="session-meta">
                        <span class="text-muted">${frappe.datetime.comment_when(session.modified)}</span>
                        <button class="btn btn-xs btn-primary open-session" data-session="${session.name}">
                            Open
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        d.fields_dict.sessions_html.$wrapper.html(html);

        d.fields_dict.sessions_html.$wrapper.on('click', '.open-session', function() {
            const session_id = $(this).data('session');
            frappe.set_route('Form', 'Generation Session', session_id);
            d.hide();
        });

        d.show();
    }
};

// Initialize chat when Generation Session form loads
frappe.ui.form.on('Generation Session', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            // Add custom button to open chat
            frm.add_custom_button(__('Open Chat'), function() {
                frappe.set_route('leet-devops-chat', frm.doc.name);
            });
        }
    }
});
