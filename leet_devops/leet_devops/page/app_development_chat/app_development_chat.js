frappe.pages['app-development-chat'].on_page_load = function(wrapper) {
	frappe.pages['app-development-chat'].wrapper = wrapper;
	
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'App Development Chat',
		single_column: true
	});
	
	frappe.pages['app-development-chat'].page = page;
	
	// Get session from URL
	const urlParams = new URLSearchParams(window.location.search);
	let sessionName = urlParams.get('session');
	
	// Also try to get from hash if not in query string
	if (!sessionName && window.location.hash) {
		const hashParams = new URLSearchParams(window.location.hash.split('?')[1]);
		sessionName = hashParams.get('session');
	}

	if (!sessionName) {
		$(page.body).html(`
			<div style="padding: 40px;">
				<h3>No Session Selected</h3>
				<p>Please select an App Development Session to continue.</p>
				
				<div style="margin: 20px 0;">
					<label style="display: block; margin-bottom: 10px;">Select Session:</label>
					<select id="session-selector" class="form-control" style="max-width: 400px;">
						<option value="">Loading sessions...</option>
					</select>
				</div>
				
				<button class="btn btn-primary" id="open-session-btn" disabled>
					Open Session
				</button>
				
				<p style="margin-top: 20px;">
					<a href="/app/app-development-session">View All Sessions</a>
				</p>
			</div>
		`);
		
		// Load available sessions
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'App Development Session',
				fields: ['name', 'app_name', 'app_title'],
				limit_page_length: 50,
				order_by: 'modified desc'
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					let options = '<option value="">-- Select a session --</option>';
					r.message.forEach(session => {
						options += `<option value="${session.name}">${session.app_title || session.app_name} (${session.name})</option>`;
					});
					$('#session-selector').html(options);
					
					$('#session-selector').on('change', function() {
						const selected = $(this).val();
						$('#open-session-btn').prop('disabled', !selected);
					});
					
					$('#open-session-btn').on('click', function() {
						const selected = $('#session-selector').val();
						if (selected) {
							window.location.href = `/app/app-development-chat?session=${encodeURIComponent(selected)}`;
						}
					});
				} else {
					$('#session-selector').html('<option value="">No sessions found</option>');
				}
			}
		});
		
		return;
	}

	let currentSession = null;
	let currentDoctypeSession = null;

	// Build the page HTML
	$(page.body).html(`
		<style>
			.chat-container {
				max-width: 100%;
				padding: 20px;
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
				font-size: 11px;
				color: #666;
				text-transform: uppercase;
				margin-bottom: 5px;
			}
			
			.info-value {
				font-size: 15px;
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
			
			.input-area {
				display: flex;
				gap: 10px;
				align-items: flex-end;
			}
			
			.chat-input {
				flex: 1;
				padding: 12px;
				border: 1px solid #d1d8dd;
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
				padding: 3px 10px;
				border-radius: 12px;
				font-size: 10px;
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
		</style>
		
		<div class="chat-container">
			<div class="session-header">
				<h3 id="session-title">Loading...</h3>
				<div class="session-info" id="session-info"></div>
			</div>

			<div class="doctype-tabs" id="doctype-tabs"></div>

			<div class="chat-area">
				<h4 id="current-context">Main App Development</h4>
				<div class="messages-container" id="messages-container">
					<div style="text-align: center; padding: 20px; color: #666;">
						Loading conversation...
					</div>
				</div>
				
				<div class="input-area">
					<textarea 
						class="chat-input" 
						id="chat-input" 
						placeholder="Ask Claude to help develop your app..."
						rows="3"
					></textarea>
					<button class="btn btn-primary btn-lg" id="send-button">
						Send
					</button>
				</div>
			</div>

			<div class="action-buttons">
				<button class="btn btn-success" id="apply-button">
					Apply Changes
				</button>
				<button class="btn btn-warning" id="verify-button">
					Verify Files
				</button>
				<button class="btn btn-default" id="refresh-button">
					Refresh
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
			$('#current-context').html(`DocType: ${doctypeName}`);
		} else {
			$('#current-context').html(`Main App Development`);
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
					<div class="message-header">Claude AI</div>
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
				html += `
					<div class="message ${msg.role}">
						<div class="message-header">
							${msg.role === 'user' ? 'You' : 'Claude AI'}
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
		$('#send-button').off('click').on('click', sendMessage);
		
		$('#chat-input').off('keydown').on('keydown', function(e) {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				sendMessage();
			}
		});
		
		$('#apply-button').off('click').on('click', applyChanges);
		$('#verify-button').off('click').on('click', verifyFiles);
		$('#refresh-button').off('click').on('click', loadSession);
	}

	function sendMessage() {
		const input = $('#chat-input');
		const message = input.val().trim();
		
		if (!message) return;
		
		input.prop('disabled', true);
		$('#send-button').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Sending...');
		
		addMessageToUI('user', message);
		input.val('');
		
		// Add a "thinking" indicator
		const thinkingDiv = $(`
			<div class="message assistant" id="thinking-message">
				<div class="message-header">Claude AI</div>
				<div class="message-content">
					<i class="fa fa-circle-o-notch fa-spin"></i> Thinking... This may take up to 3 minutes for complex requests.
				</div>
			</div>
		`);
		$('#messages-container').append(thinkingDiv);
		$('#messages-container').scrollTop($('#messages-container')[0].scrollHeight);
		
		frappe.call({
			method: 'leet_devops.api.claude_api.send_message_to_claude',
			args: {
				session_name: currentSession.name,
				message: message,
				doctype_session_name: currentDoctypeSession
			},
			callback: function(r) {
				// Remove thinking indicator
				$('#thinking-message').remove();
				
				input.prop('disabled', false);
				$('#send-button').prop('disabled', false).text('Send');
				
				if (r.message.error) {
					frappe.msgprint({
						title: 'Error',
						indicator: 'red',
						message: r.message.error + (r.message.details ? '<br><br><small>' + r.message.details + '</small>' : '')
					});
				} else {
					addMessageToUI('assistant', r.message.message);
					checkForDoctypeDefinition(r.message.message);
					loadSession();
				}
				
				input.focus();
			},
			error: function(err) {
				// Remove thinking indicator
				$('#thinking-message').remove();
				
				input.prop('disabled', false);
				$('#send-button').prop('disabled', false).text('Send');
				frappe.msgprint({
					title: 'Error',
					indicator: 'red',
					message: 'Network error: ' + (err.message || 'Unknown error') + '<br><br>This could be due to:<br>- Slow internet connection<br>- API timeout<br>- Network connectivity issues<br><br>Please try again.'
				});
			}
		});
	}

	function addMessageToUI(role, content) {
		const container = $('#messages-container');
		const timestamp = new Date().toLocaleString();
		
		const messageDiv = $(`
			<div class="message ${role}">
				<div class="message-header">
					${role === 'user' ? 'You' : 'Claude AI'}
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
				$('#apply-button').prop('disabled', true).text('Applying...');
				
				frappe.call({
					method: 'leet_devops.api.claude_api.apply_changes',
					args: {
						session_name: currentSession.name
					},
					callback: function(r) {
						$('#apply-button').prop('disabled', false).text('Apply Changes');
						
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
		$('#verify-button').prop('disabled', true).text('Verifying...');
		
		frappe.call({
			method: 'leet_devops.api.claude_api.verify_files',
			args: {
				session_name: currentSession.name
			},
			callback: function(r) {
				$('#verify-button').prop('disabled', false).text('Verify Files');
				
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
				const color = result.status === 'success' ? 'green' : 'red';
				html += `
					<div class="change-item">
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
				const color = file.exists ? 'green' : 'red';
				html += `<small style="color: ${color};">${file.exists ? '✓' : '✗'} ${file.path} (${file.size} bytes)</small><br>`;
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
