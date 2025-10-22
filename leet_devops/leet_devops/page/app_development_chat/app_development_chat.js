frappe.pages['app-development-chat'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'App Development Chat',
		single_column: true
	});

	// Add custom CSS
	const style = document.createElement('style');
	style.textContent = `
		.chat-container {
			max-width: 100%;
			padding: 20px;
			background: #f9f9f9;
		}
		
		.session-header {
			background: white;
			padding: 20px;
			border-radius: 8px;
			margin-bottom: 20px;
			box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		}
		
		.session-info {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
			gap: 15px;
			margin-top: 15px;
		}
		
		.info-card {
			background: #f5f5f5;
			padding: 10px;
			border-radius: 4px;
		}
		
		.info-label {
			font-size: 12px;
			color: #666;
			text-transform: uppercase;
			margin-bottom: 5px;
		}
		
		.info-value {
			font-size: 16px;
			font-weight: 600;
		}
		
		.doctype-tabs {
			display: flex;
			gap: 10px;
			flex-wrap: wrap;
			margin-bottom: 20px;
		}
		
		.doctype-tab {
			padding: 10px 20px;
			background: white;
			border: 2px solid #ddd;
			border-radius: 4px;
			cursor: pointer;
			transition: all 0.3s;
		}
		
		.doctype-tab:hover {
			border-color: var(--primary-color);
		}
		
		.doctype-tab.active {
			background: var(--primary-color);
			color: white;
			border-color: var(--primary-color);
		}
		
		.chat-area {
			background: white;
			border-radius: 8px;
			padding: 20px;
			margin-bottom: 20px;
			box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		}
		
		.messages-container {
			max-height: 500px;
			overflow-y: auto;
			padding: 20px;
			background: #fafafa;
			border-radius: 8px;
			margin-bottom: 20px;
			min-height: 300px;
		}
		
		.message {
			margin-bottom: 15px;
			padding: 12px;
			border-radius: 8px;
			animation: fadeIn 0.3s;
		}
		
		@keyframes fadeIn {
			from { opacity: 0; transform: translateY(10px); }
			to { opacity: 1; transform: translateY(0); }
		}
		
		.message.user {
			background: #e3f2fd;
			margin-left: 20%;
		}
		
		.message.assistant {
			background: #f5f5f5;
			margin-right: 20%;
		}
		
		.message-header {
			font-weight: 600;
			margin-bottom: 8px;
			color: #666;
			font-size: 12px;
		}
		
		.message-content {
			line-height: 1.6;
			word-wrap: break-word;
		}
		
		.message-content pre {
			background: #2d2d2d;
			color: #f8f8f2;
			padding: 10px;
			border-radius: 4px;
			overflow-x: auto;
			margin: 10px 0;
		}
		
		.message-content code {
			font-family: 'Courier New', monospace;
			font-size: 13px;
		}
		
		.input-area {
			display: flex;
			gap: 10px;
			align-items: flex-end;
		}
		
		.chat-input {
			flex: 1;
			padding: 12px;
			border: 2px solid #ddd;
			border-radius: 4px;
			font-size: 14px;
			font-family: inherit;
			resize: vertical;
			min-height: 80px;
		}
		
		.chat-input:focus {
			outline: none;
			border-color: var(--primary-color);
		}
		
		.action-buttons {
			display: flex;
			gap: 10px;
			margin-top: 20px;
		}
		
		.status-badge {
			display: inline-block;
			padding: 4px 12px;
			border-radius: 12px;
			font-size: 11px;
			font-weight: 600;
			margin-left: 8px;
		}
		
		.status-active {
			background: #e3f2fd;
			color: #1976d2;
		}
		
		.status-completed {
			background: #e8f5e9;
			color: #4caf50;
		}
		
		.status-error {
			background: #ffebee;
			color: #f44336;
		}
		
		.changes-preview {
			background: white;
			padding: 20px;
			border-radius: 8px;
			margin-top: 20px;
			box-shadow: 0 2px 4px rgba(0,0,0,0.1);
			display: none;
		}
		
		.change-item {
			padding: 10px;
			background: #f5f5f5;
			border-radius: 4px;
			margin-bottom: 10px;
			font-size: 13px;
		}
		
		.loading-spinner {
			text-align: center;
			padding: 20px;
			color: #666;
		}
	`;
	document.head.appendChild(style);

	let currentSession = null;
	let currentDoctypeSession = null;

	// Get session from URL
	const urlParams = new URLSearchParams(window.location.search);
	const sessionName = urlParams.get('session');

	if (!sessionName) {
		page.$body.html(`
			<div class="chat-container">
				<div class="session-header">
					<h3>No Session Selected</h3>
					<p>Please select an App Development Session to continue.</p>
					<button class="btn btn-primary" onclick="frappe.set_route('List', 'App Development Session')">
						Go to Sessions
					</button>
				</div>
			</div>
		`);
		return;
	}

	// Build the page HTML
	page.$body.html(`
		<div class="chat-container">
			<div class="session-header">
				<h3 id="session-title">Loading...</h3>
				<div class="session-info" id="session-info"></div>
			</div>

			<div class="doctype-tabs" id="doctype-tabs"></div>

			<div class="chat-area">
				<h4 id="current-context">Main App Development</h4>
				<div class="messages-container" id="messages-container">
					<div class="loading-spinner">Loading conversation...</div>
				</div>
				
				<div class="input-area">
					<textarea 
						class="chat-input" 
						id="chat-input" 
						placeholder="Ask Claude to help develop your app..."
						rows="3"
					></textarea>
					<button class="btn btn-primary btn-lg" id="send-button">
						<i class="fa fa-paper-plane"></i> Send
					</button>
				</div>
			</div>

			<div class="action-buttons">
				<button class="btn btn-success" id="apply-button">
					<i class="fa fa-check"></i> Apply Changes
				</button>
				<button class="btn btn-warning" id="verify-button">
					<i class="fa fa-shield"></i> Verify Files
				</button>
				<button class="btn btn-default" id="refresh-button">
					<i class="fa fa-refresh"></i> Refresh
				</button>
			</div>

			<div class="changes-preview" id="changes-preview">
				<h4>Results</h4>
				<div id="changes-content"></div>
			</div>
		</div>
	`);

	// Load session data
	loadSession();

	function loadSession() {
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
					setupEventListeners();
				} else {
					frappe.msgprint('Session not found');
				}
			}
		});
	}

	function renderSessionInfo() {
		const statusClass = getStatusClass(currentSession.status);
		
		$('#session-title').text(`${currentSession.app_title || currentSession.app_name} - Development Chat`);
		$('#session-info').html(`
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
		`);
	}

	function renderDoctypeTabs() {
		let tabs = `
			<div class="doctype-tab active" data-doctype="">
				<i class="fa fa-home"></i> Main App
			</div>
		`;
		
		if (currentSession.doctype_sessions) {
			currentSession.doctype_sessions.forEach(dt => {
				tabs += `
					<div class="doctype-tab" data-doctype="${dt.doctype_name}">
						<i class="fa fa-file-text-o"></i> ${dt.doctype_title || dt.doctype_name}
						<span class="status-badge ${getStatusClass(dt.status)}">${dt.status}</span>
					</div>
				`;
			});
		}
		
		$('#doctype-tabs').html(tabs);
		
		$('.doctype-tab').on('click', function() {
			switchDoctypeSession($(this).data('doctype'));
		});
	}

	function switchDoctypeSession(doctypeName) {
		currentDoctypeSession = doctypeName || null;
		
		$('.doctype-tab').removeClass('active');
		$(`.doctype-tab[data-doctype="${doctypeName}"]`).addClass('active');
		
		if (doctypeName) {
			$('#current-context').html(`<i class="fa fa-file-text-o"></i> DocType: ${doctypeName}`);
		} else {
			$('#current-context').html(`<i class="fa fa-home"></i> Main App Development`);
		}
		
		loadConversationHistory();
	}

	function loadConversationHistory() {
		let history = [];
		
		try {
			if (currentDoctypeSession) {
				const dtSession = currentSession.doctype_sessions.find(
					dt => dt.doctype_name === currentDoctypeSession
				);
				if (dtSession && dtSession.conversation_history) {
					history = JSON.parse(dtSession.conversation_history);
				}
			} else {
				if (currentSession.conversation_history) {
					history = JSON.parse(currentSession.conversation_history);
				}
			}
		} catch (e) {
			console.error('Error parsing conversation history:', e);
		}
		
		const container = $('#messages-container');
		
		if (history.length === 0) {
			container.html(`
				<div class="message assistant">
					<div class="message-header"><i class="fa fa-robot"></i> Claude AI</div>
					<div class="message-content">
						Hello! I'm here to help you develop your Frappe app. 
						${currentDoctypeSession 
							? `We're working on the <strong>${currentDoctypeSession}</strong> DocType. How can I help you modify or improve it?`
							: 'You can ask me to create DocTypes, explain concepts, or help with your app architecture.'}
					</div>
				</div>
			`);
		} else {
			let html = '';
			history.forEach(msg => {
				const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : '';
				const icon = msg.role === 'user' ? 'fa-user' : 'fa-robot';
				html += `
					<div class="message ${msg.role}">
						<div class="message-header">
							<i class="fa ${icon}"></i> ${msg.role === 'user' ? 'You' : 'Claude AI'}
							${timestamp ? `<span style="float: right; font-weight: normal;">${timestamp}</span>` : ''}
						</div>
						<div class="message-content">${formatMessage(msg.content)}</div>
					</div>
				`;
			});
			container.html(html);
		}
		
		container.scrollTop(container[0].scrollHeight);
	}

	function formatMessage(content) {
		content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
			return `<pre><code>${escapeHtml(code)}</code></pre>`;
		});
		content = content.replace(/\n/g, '<br>');
		return content;
	}

	function escapeHtml(text) {
		const div = document.createElement('div');
		div.textContent = text;
		return div.innerHTML;
	}

	function setupEventListeners() {
		$('#send-button').on('click', sendMessage);
		
		$('#chat-input').on('keydown', function(e) {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				sendMessage();
			}
		});
		
		$('#apply-button').on('click', applyChanges);
		$('#verify-button').on('click', verifyFiles);
		$('#refresh-button').on('click', loadSession);
	}

	function sendMessage() {
		const input = $('#chat-input');
		const message = input.val().trim();
		
		if (!message) return;
		
		input.prop('disabled', true);
		$('#send-button').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Sending...');
		
		addMessageToUI('user', message);
		input.val('');
		
		frappe.call({
			method: 'leet_devops.api.claude_api.send_message_to_claude',
			args: {
				session_name: currentSession.name,
				message: message,
				doctype_session_name: currentDoctypeSession
			},
			callback: function(r) {
				input.prop('disabled', false);
				$('#send-button').prop('disabled', false).html('<i class="fa fa-paper-plane"></i> Send');
				
				if (r.message.error) {
					frappe.msgprint({
						title: 'Error',
						indicator: 'red',
						message: r.message.error
					});
				} else {
					addMessageToUI('assistant', r.message.message);
					checkForDoctypeDefinition(r.message.message);
					loadSession();
				}
				
				input.focus();
			},
			error: function(err) {
				input.prop('disabled', false);
				$('#send-button').prop('disabled', false).html('<i class="fa fa-paper-plane"></i> Send');
				frappe.msgprint({
					title: 'Error',
					indicator: 'red',
					message: 'Network error: ' + err.message
				});
			}
		});
	}

	function addMessageToUI(role, content) {
		const container = $('#messages-container');
		const timestamp = new Date().toLocaleString();
		const icon = role === 'user' ? 'fa-user' : 'fa-robot';
		
		const messageDiv = $(`
			<div class="message ${role}">
				<div class="message-header">
					<i class="fa ${icon}"></i> ${role === 'user' ? 'You' : 'Claude AI'}
					<span style="float: right; font-weight: normal;">${timestamp}</span>
				</div>
				<div class="message-content">${formatMessage(content)}</div>
			</div>
		`);
		
		container.append(messageDiv);
		container.scrollTop(container[0].scrollHeight);
	}

	function checkForDoctypeDefinition(message) {
		const jsonMatch = message.match(/```json\s*([\s\S]*?)```/);
		
		if (jsonMatch) {
			try {
				const definition = JSON.parse(jsonMatch[1]);
				if (definition.doctype === 'DocType' && definition.name) {
					frappe.confirm(
						`I found a DocType definition for "${definition.name}". Would you like to create a session for it?`,
						() => createDoctypeSession(definition.name, definition)
					);
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
					frappe.msgprint({
						title: 'Error',
						indicator: 'red',
						message: r.message.error
					});
				} else {
					frappe.show_alert({
						message: `DocType session created for ${doctypeName}`,
						indicator: 'green'
					});
					loadSession();
				}
			}
		});
	}

	function applyChanges() {
		frappe.confirm(
			'This will create/modify files in your Frappe app. Continue?',
			() => {
				$('#apply-button').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Applying...');
				
				frappe.call({
					method: 'leet_devops.api.claude_api.apply_changes',
					args: {
						session_name: currentSession.name
					},
					callback: function(r) {
						$('#apply-button').prop('disabled', false).html('<i class="fa fa-check"></i> Apply Changes');
						
						if (r.message.error) {
							frappe.msgprint({
								title: 'Error',
								indicator: 'red',
								message: 'Error applying changes: ' + r.message.error
							});
						} else {
							frappe.show_alert({
								message: 'Changes applied successfully!',
								indicator: 'green'
							});
							showChangesPreview(r.message.results);
							loadSession();
						}
					}
				});
			}
		);
	}

	function verifyFiles() {
		$('#verify-button').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Verifying...');
		
		frappe.call({
			method: 'leet_devops.api.claude_api.verify_files',
			args: {
				session_name: currentSession.name
			},
			callback: function(r) {
				$('#verify-button').prop('disabled', false).html('<i class="fa fa-shield"></i> Verify Files');
				
				if (r.message.error) {
					frappe.msgprint({
						title: 'Error',
						indicator: 'red',
						message: 'Verification error: ' + r.message.error
					});
				} else {
					if (r.message.verified) {
						frappe.show_alert({
							message: 'All files verified successfully!',
							indicator: 'green'
						});
					} else {
						frappe.msgprint({
							title: 'Verification Failed',
							indicator: 'orange',
							message: 'Some files are missing or could not be verified.'
						});
					}
					showVerificationResults(r.message.results);
					loadSession();
				}
			}
		});
	}

	function showChangesPreview(results) {
		let html = '<h4>Changes Applied</h4>';
		results.forEach(result => {
			if (result.doctype) {
				const icon = result.status === 'success' ? 'fa-check-circle' : 'fa-times-circle';
				const color = result.status === 'success' ? 'green' : 'red';
				html += `
					<div class="change-item">
						<i class="fa ${icon}" style="color: ${color}"></i>
						<strong>${result.doctype}</strong>: ${result.status}
						${result.files ? `<br><small>Files: ${result.files.join(', ')}</small>` : ''}
						${result.error ? `<br><span style="color: red;">Error: ${result.error}</span>` : ''}
					</div>
				`;
			}
		});
		
		$('#changes-content').html(html);
		$('#changes-preview').show();
	}

	function showVerificationResults(results) {
		let html = '<h4>Verification Results</h4>';
		results.forEach(result => {
			html += `<div class="change-item"><strong>${result.doctype}</strong><br>`;
			result.files.forEach(file => {
				const icon = file.exists ? 'fa-check' : 'fa-times';
				const color = file.exists ? 'green' : 'red';
				html += `<small><i class="fa ${icon}" style="color: ${color}"></i> ${file.path} (${file.size} bytes)</small><br>`;
			});
			html += '</div>';
		});
		
		$('#changes-content').html(html);
		$('#changes-preview').show();
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
};
