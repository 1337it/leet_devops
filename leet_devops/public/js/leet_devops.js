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
            
            // Add Apply Changes button to assistant messages
            this.add_apply_button(streaming_msg, message_id);
        }
        
        // Reload child sessions in case new ones were created
        this.load_child_sessions_badge();
    }

    add_apply_button(message_elem, message_id) {
        // Check if message has code blocks
        const has_code = message_elem.find('pre, code').length > 0 || 
                        message_elem.text().includes('```');
        
        if (has_code) {
            const button_html = `
                <div class="message-actions">
                    <button class="btn btn-sm btn-primary apply-changes-btn" 
                            data-message-id="${message_id}">
                        <i class="fa fa-magic"></i> Apply Changes
                    </button>
                    <button class="btn btn-sm btn-default preview-changes-btn" 
                            data-message-id="${message_id}">
                        <i class="fa fa-eye"></i> Preview
                    </button>
                </div>
            `;
            message_elem.append(button_html);
            
            const me = this;
            message_elem.find('.apply-changes-btn').on('click', function() {
                const msg_id = $(this).data('message-id');
                me.preview_and_apply_changes(msg_id);
            });
            
            message_elem.find('.preview-changes-btn').on('click', function() {
                const msg_id = $(this).data('message-id');
                me.preview_changes(msg_id);
            });
        }
    }

    preview_changes(message_id) {
        const me = this;
        
        frappe.show_alert({
            message: __('Analyzing code...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'leet_devops.api.code_applicator.preview_artifacts',
            args: {
                message_id: message_id
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    me.show_preview_dialog(r.message.previews, message_id);
                } else {
                    frappe.msgprint({
                        title: __('Preview Error'),
                        message: r.message.error || __('Could not preview changes'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    show_preview_dialog(previews, message_id) {
        const me = this;
        
        if (!previews || previews.length === 0) {
            frappe.msgprint(__('No artifacts found to apply'));
            return;
        }
        
        let html = '<div class="artifacts-preview">';
        html += '<p class="text-muted">The following changes will be applied:</p>';
        
        previews.forEach(function(preview, index) {
            html += `
                <div class="artifact-preview-item">
                    <div class="preview-header">
                        <span class="badge badge-primary">${preview.type}</span>
                        <strong>${preview.name}</strong>
                    </div>
                    <div class="preview-body">
                        <p>${preview.description}</p>
                        <small class="text-muted">Path: ${preview.path}</small>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        const d = new frappe.ui.Dialog({
            title: __('Preview Changes'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'preview_html',
                    options: html
                }
            ],
            primary_action_label: __('Apply Changes'),
            primary_action: function() {
                d.hide();
                me.apply_changes(message_id, previews);
            },
            secondary_action_label: __('Cancel')
        });
        
        // Add custom CSS
        if (!$('#artifact-preview-css').length) {
            $('head').append(`
                <style id="artifact-preview-css">
                    .artifacts-preview {
                        max-height: 400px;
                        overflow-y: auto;
                    }
                    .artifact-preview-item {
                        border: 1px solid #e5e5e5;
                        border-radius: 6px;
                        padding: 12px;
                        margin-bottom: 10px;
                        background: #f8f9fa;
                    }
                    .artifact-preview-item .preview-header {
                        display: flex;
                        gap: 10px;
                        align-items: center;
                        margin-bottom: 8px;
                    }
                    .artifact-preview-item .preview-body p {
                        margin: 5px 0;
                    }
                </style>
            `);
        }
        
        d.show();
    }

    preview_and_apply_changes(message_id) {
        const me = this;
        
        // First preview, then apply
        frappe.call({
            method: 'leet_devops.api.code_applicator.preview_artifacts',
            args: {
                message_id: message_id
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    me.show_preview_dialog(r.message.previews, message_id);
                } else {
                    // If preview fails, ask if they want to try applying anyway
                    frappe.confirm(
                        'Could not generate preview. Apply changes anyway?',
                        function() {
                            me.apply_changes(message_id, []);
                        }
                    );
                }
            }
        });
    }

    apply_changes(message_id, previews) {
        const me = this;
        
        frappe.show_alert({
            message: __('Applying changes...'),
            indicator: 'blue'
        });
        
        // Show progress dialog
        const progress_dialog = new frappe.ui.Dialog({
            title: __('Applying Changes'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'progress_html',
                    options: `
                        <div class="apply-progress">
                            <p><i class="fa fa-spinner fa-spin"></i> Applying changes...</p>
                            <p class="text-muted">This may take a moment.</p>
                        </div>
                    `
                }
            ]
        });
        progress_dialog.show();
        
        // First extract artifacts
        frappe.call({
            method: 'leet_devops.api.code_applicator.parse_and_extract_artifacts',
            args: {
                message_id: message_id
            },
            callback: function(r) {
                if (r.message && r.message.success && r.message.artifacts.length > 0) {
                    // Now apply the artifacts
                    frappe.call({
                        method: 'leet_devops.api.code_applicator.apply_artifacts',
                        args: {
                            session_id: me.session_id,
                            message_id: message_id,
                            artifacts_json: JSON.stringify(r.message.artifacts)
                        },
                        callback: function(apply_result) {
                            progress_dialog.hide();
                            
                            if (apply_result.message && apply_result.message.success) {
                                me.show_apply_results(apply_result.message.results);
                            } else {
                                frappe.msgprint({
                                    title: __('Application Error'),
                                    message: apply_result.message.error || __('Could not apply changes'),
                                    indicator: 'red'
                                });
                            }
                        },
                        error: function() {
                            progress_dialog.hide();
                            frappe.msgprint({
                                title: __('Error'),
                                message: __('Failed to apply changes'),
                                indicator: 'red'
                            });
                        }
                    });
                } else {
                    progress_dialog.hide();
                    frappe.msgprint({
                        title: __('No Artifacts'),
                        message: __('No code artifacts found to apply in this message'),
                        indicator: 'orange'
                    });
                }
            }
        });
        
        // Listen for migrate completion
        frappe.realtime.on('migrate_complete', function(data) {
            frappe.show_alert({
                message: __('Migration completed successfully!'),
                indicator: 'green'
            });
        });
    }

    show_apply_results(results) {
        let success_count = 0;
        let error_count = 0;
        
        results.forEach(function(result) {
            if (result.success) success_count++;
            else error_count++;
        });
        
        let html = '<div class="apply-results">';
        
        if (success_count > 0) {
            html += `
                <div class="alert alert-success">
                    <strong>Success!</strong> Applied ${success_count} artifact(s).
                </div>
            `;
        }
        
        if (error_count > 0) {
            html += `
                <div class="alert alert-warning">
                    <strong>Warning:</strong> ${error_count} artifact(s) could not be applied.
                </div>
            `;
        }
        
        html += '<div class="results-list">';
        results.forEach(function(result) {
            const icon = result.success ? 'fa-check-circle text-success' : 'fa-times-circle text-danger';
            html += `
                <div class="result-item">
                    <i class="fa ${icon}"></i>
                    <div class="result-details">
                        <strong>${result.type || 'Unknown'}</strong>
                        ${result.name ? `<span>: ${result.name}</span>` : ''}
                        <p class="text-muted small">${result.message || result.error || ''}</p>
                        ${result.file ? `<small class="text-muted">${result.file}</small>` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        html += `
            <div class="mt-3">
                <p class="text-muted">
                    <i class="fa fa-info-circle"></i> 
                    Changes have been applied. Migration is running in the background.
                </p>
                <p class="text-muted small">
                    You may need to refresh your browser to see the new DocTypes.
                </p>
            </div>
        `;
        
        html += '</div>';
        
        const d = new frappe.ui.Dialog({
            title: __('Apply Results'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'results_html',
                    options: html
                }
            ],
            primary_action_label: __('Refresh Browser'),
            primary_action: function() {
                window.location.reload();
            },
            secondary_action_label: __('Close')
        });
        
        // Add custom CSS
        if (!$('#apply-results-css').length) {
            $('head').append(`
                <style id="apply-results-css">
                    .apply-results {
                        max-height: 500px;
                        overflow-y: auto;
                    }
                    .results-list {
                        margin: 15px 0;
                    }
                    .result-item {
                        display: flex;
                        gap: 10px;
                        padding: 10px;
                        border-bottom: 1px solid #e5e5e5;
                    }
                    .result-item:last-child {
                        border-bottom: none;
                    }
                    .result-item i {
                        font-size: 18px;
                        margin-top: 2px;
                    }
                    .result-details {
                        flex: 1;
                    }
                    .result-details p {
                        margin: 5px 0;
                    }
                </style>
            `);
        }
        
        d.show();
        
        // Show success notification
        frappe.show_alert({
            message: __('Changes applied successfully!'),
            indicator: 'green'
        }, 5);
    }

    remove_streaming_placeholder() {
        this.messages_container.find('.message.streaming[data-streaming="true"]').remove();
    }

    add_message(sender, content, type, message_id = null) {
        const msg_html = `
            <div class="message ${type}" data-message-id="${message_id || ''}">
                <div class="message-header">
                    <strong>${sender}</strong>
                    <span class="message-time">${frappe.datetime.now_time()}</span>
                </div>
                <div class="message-content">${this.format_content(content)}</div>
            </div>
        `;
        this.messages_container.append(msg_html);
        
        // Add apply button if this is an assistant message with code
        if (type === 'assistant' && message_id && (content.includes('```') || content.includes('</code>'))) {
            const msg_elem = this.messages_container.find(`.message[data-message-id="${message_id}"]`);
            this.add_apply_button(msg_elem, message_id);
        }
        
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
                        me.add_message(msg.sender, msg.message_content, type, msg.name);
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
