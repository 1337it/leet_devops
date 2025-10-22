// Leet Devops - App Development Chat Interface

let currentSession = null;
let currentDoctypeSession = null;

// Initialize on page load
frappe.ready(function() {
    loadSessionFromUrl();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    document.getElementById('apply-button').addEventListener('click', applyChanges);
    document.getElementById('verify-button').addEventListener('click', verifyFiles);
}

function loadSessionFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionName = urlParams.get('session');
    
    if (sessionName) {
        loadSession(sessionName);
    } else {
        showError('No session specified. Please provide a session parameter.');
    }
}

function loadSession(sessionName) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'App Development Session',
            name: sessionName
        },
        callback: function(r) {
            if (r.message) {
                currentSession = r.message;
                renderSessionInfo();
                renderDoctypeTabs();
                loadConversationHistory();
            } else {
                showError('Session not found');
            }
        }
    });
}

function renderSessionInfo() {
    const infoContainer = document.getElementById('session-info');
    const statusClass = getStatusClass(currentSession.status);
    
    infoContainer.innerHTML = `
        <div class="info-card">
            <div class="info-label">App Name</div>
            <div class="info-value">${currentSession.app_name}</div>
        </div>
        <div class="info-card">
            <div class="info-label">Status</div>
            <div class="info-value">
                <span class="status-badge ${statusClass}">${currentSession.status}</span>
            </div>
        </div>
        <div class="info-card">
            <div class="info-label">DocTypes</div>
            <div class="info-value">${currentSession.doctype_sessions?.length || 0}</div>
        </div>
        <div class="info-card">
            <div class="info-label">Created</div>
            <div class="info-value">${frappe.datetime.str_to_user(currentSession.created_date)}</div>
        </div>
    `;
    
    document.getElementById('session-title').textContent = `${currentSession.app_title || currentSession.app_name} - Development Chat`;
}

function renderDoctypeTabs() {
    const tabsContainer = document.getElementById('doctype-tabs');
    
    let tabs = `
        <div class="doctype-tab active" data-doctype="">
            Main App
        </div>
    `;
    
    if (currentSession.doctype_sessions) {
        currentSession.doctype_sessions.forEach(dt => {
            tabs += `
                <div class="doctype-tab" data-doctype="${dt.doctype_name}">
                    ${dt.doctype_title || dt.doctype_name}
                    <span class="status-badge ${getStatusClass(dt.status)}">${dt.status}</span>
                </div>
            `;
        });
    }
    
    tabsContainer.innerHTML = tabs;
    
    // Add click handlers
    document.querySelectorAll('.doctype-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            switchDoctypeSession(this.dataset.doctype);
        });
    });
}

function switchDoctypeSession(doctypeName) {
    currentDoctypeSession = doctypeName || null;
    
    // Update active tab
    document.querySelectorAll('.doctype-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.doctype === doctypeName) {
            tab.classList.add('active');
        }
    });
    
    // Update context display
    if (doctypeName) {
        document.getElementById('current-context').textContent = `DocType: ${doctypeName}`;
    } else {
        document.getElementById('current-context').textContent = 'Main App Development';
    }
    
    // Load appropriate conversation
    loadConversationHistory();
}

function loadConversationHistory() {
    const messagesContainer = document.getElementById('messages-container');
    let history = [];
    
    try {
        if (currentDoctypeSession) {
            // Load specific DocType session history
            const dtSession = currentSession.doctype_sessions.find(
                dt => dt.doctype_name === currentDoctypeSession
            );
            if (dtSession && dtSession.conversation_history) {
                history = JSON.parse(dtSession.conversation_history);
            }
        } else {
            // Load main session history
            if (currentSession.conversation_history) {
                history = JSON.parse(currentSession.conversation_history);
            }
        }
    } catch (e) {
        console.error('Error parsing conversation history:', e);
    }
    
    if (history.length === 0) {
        messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="message-header">Claude AI</div>
                <div class="message-content">
                    Hello! I'm here to help you develop your Frappe app. 
                    ${currentDoctypeSession 
                        ? `We're working on the ${currentDoctypeSession} DocType. How can I help you modify or improve it?`
                        : 'You can ask me to create DocTypes, explain concepts, or help with your app architecture.'}
                </div>
            </div>
        `;
    } else {
        messagesContainer.innerHTML = history.map(msg => {
            const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : '';
            return `
                <div class="message ${msg.role}">
                    <div class="message-header">
                        ${msg.role === 'user' ? 'You' : 'Claude AI'}
                        ${timestamp ? `<span style="float: right; font-weight: normal; font-size: 11px;">${timestamp}</span>` : ''}
                    </div>
                    <div class="message-content">${formatMessage(msg.content)}</div>
                </div>
            `;
        }).join('');
    }
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(content) {
    // Convert markdown-style code blocks to HTML
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code>${escapeHtml(code)}</code></pre>`;
    });
    
    // Convert newlines to <br>
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Disable input
    input.disabled = true;
    document.getElementById('send-button').disabled = true;
    
    // Add user message to UI immediately
    addMessageToUI('user', message);
    input.value = '';
    
    // Send to API
    frappe.call({
        method: 'leet_devops.api.claude_api.send_message_to_claude',
        args: {
            session_name: currentSession.name,
            message: message,
            doctype_session_name: currentDoctypeSession
        },
        callback: function(r) {
            input.disabled = false;
            document.getElementById('send-button').disabled = false;
            
            if (r.message.error) {
                showError('Error: ' + r.message.error);
                if (r.message.details) {
                    console.error(r.message.details);
                }
            } else {
                addMessageToUI('assistant', r.message.message);
                
                // Check if response contains DocType definition
                checkForDoctypeDefinition(r.message.message);
                
                // Reload session to get updated data
                loadSession(currentSession.name);
            }
            
            input.focus();
        },
        error: function(err) {
            input.disabled = false;
            document.getElementById('send-button').disabled = false;
            showError('Network error: ' + err.message);
        }
    });
}

function addMessageToUI(role, content) {
    const messagesContainer = document.getElementById('messages-container');
    const timestamp = new Date().toLocaleString();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-header">
            ${role === 'user' ? 'You' : 'Claude AI'}
            <span style="float: right; font-weight: normal; font-size: 11px;">${timestamp}</span>
        </div>
        <div class="message-content">${formatMessage(content)}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function checkForDoctypeDefinition(message) {
    // Check if the message contains a JSON code block that might be a DocType definition
    const jsonMatch = message.match(/```json\s*([\s\S]*?)```/);
    
    if (jsonMatch) {
        try {
            const definition = JSON.parse(jsonMatch[1]);
            if (definition.doctype === 'DocType' && definition.name) {
                // Offer to create a DocType session
                if (confirm(`I found a DocType definition for "${definition.name}". Would you like to create a session for it?`)) {
                    createDoctypeSession(definition.name, definition);
                }
            }
        } catch (e) {
            // Not a valid DocType definition
        }
    }
}

function createDoctypeSession(doctypeName, definition) {
    frappe.call({
        method: 'leet_devops.api.claude_api.create_doctype_session',
        args: {
            session_name: currentSession.name,
            doctype_name: doctypeName,
            doctype_definition: definition
        },
        callback: function(r) {
            if (r.message.error) {
                showError(r.message.error);
            } else {
                showSuccess(`DocType session created for ${doctypeName}`);
                loadSession(currentSession.name);
            }
        }
    });
}

function applyChanges() {
    if (!confirm('This will create/modify files in your Frappe app. Continue?')) {
        return;
    }
    
    document.getElementById('apply-button').disabled = true;
    document.getElementById('apply-button').textContent = 'Applying...';
    
    frappe.call({
        method: 'leet_devops.api.claude_api.apply_changes',
        args: {
            session_name: currentSession.name
        },
        callback: function(r) {
            document.getElementById('apply-button').disabled = false;
            document.getElementById('apply-button').textContent = 'Apply Changes';
            
            if (r.message.error) {
                showError('Error applying changes: ' + r.message.error);
            } else {
                showSuccess('Changes applied successfully!');
                showChangesPreview(r.message.results);
                loadSession(currentSession.name);
            }
        }
    });
}

function verifyFiles() {
    document.getElementById('verify-button').disabled = true;
    document.getElementById('verify-button').textContent = 'Verifying...';
    
    frappe.call({
        method: 'leet_devops.api.claude_api.verify_files',
        args: {
            session_name: currentSession.name
        },
        callback: function(r) {
            document.getElementById('verify-button').disabled = false;
            document.getElementById('verify-button').textContent = 'Verify Files';
            
            if (r.message.error) {
                showError('Verification error: ' + r.message.error);
            } else {
                if (r.message.verified) {
                    showSuccess('All files verified successfully!');
                } else {
                    showError('Some files are missing or could not be verified.');
                }
                showVerificationResults(r.message.results);
                loadSession(currentSession.name);
            }
        }
    });
}

function showChangesPreview(results) {
    const previewDiv = document.getElementById('changes-preview');
    const contentDiv = document.getElementById('changes-content');
    
    let html = '';
    results.forEach(result => {
        if (result.doctype) {
            html += `
                <div class="change-item">
                    <strong>${result.doctype}</strong>: ${result.status}
                    ${result.files ? `<br><small>Files: ${result.files.join(', ')}</small>` : ''}
                    ${result.error ? `<br><span style="color: red;">Error: ${result.error}</span>` : ''}
                </div>
            `;
        }
    });
    
    contentDiv.innerHTML = html;
    previewDiv.style.display = 'block';
}

function showVerificationResults(results) {
    const previewDiv = document.getElementById('changes-preview');
    const contentDiv = document.getElementById('changes-content');
    
    let html = '<h4>Verification Results</h4>';
    results.forEach(result => {
        html += `<div class="change-item">
            <strong>${result.doctype}</strong><br>`;
        
        result.files.forEach(file => {
            const icon = file.exists ? '✓' : '✗';
            const color = file.exists ? 'green' : 'red';
            html += `<small style="color: ${color};">${icon} ${file.path} (${file.size} bytes)</small><br>`;
        });
        
        html += '</div>';
    });
    
    contentDiv.innerHTML = html;
    previewDiv.style.display = 'block';
}

function getStatusClass(status) {
    const statusMap = {
        'Active': 'status-active',
        'Completed': 'status-completed',
        'Error': 'status-error',
        'Draft': 'status-active',
        'Ready': 'status-completed',
        'Applied': 'status-completed'
    };
    return statusMap[status] || 'status-active';
}

function showError(message) {
    frappe.msgprint({
        title: 'Error',
        indicator: 'red',
        message: message
    });
}

function showSuccess(message) {
    frappe.msgprint({
        title: 'Success',
        indicator: 'green',
        message: message
    });
}
