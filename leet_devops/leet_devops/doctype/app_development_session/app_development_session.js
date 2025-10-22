frappe.ui.form.on('App Development Session', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Open Chat Interface'), function() {
				frappe.set_route('app-development-chat', {'session': frm.doc.name});
			}, __('Actions'));
			
			frm.add_custom_button(__('Scan & Create Sessions'), function() {
				frappe.call({
					method: 'leet_devops.api.claude_api.scan_and_create_doctype_sessions',
					args: {
						session_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message.error) {
							frappe.msgprint({
								title: 'Error',
								indicator: 'red',
								message: r.message.error
							});
						} else if (r.message.created > 0) {
							frappe.msgprint({
								title: 'Success',
								indicator: 'green',
								message: r.message.message
							});
							frm.reload_doc();
						} else {
							frappe.msgprint({
								title: 'Info',
								indicator: 'blue',
								message: r.message.message
							});
						}
					}
				});
			}, __('Actions'));
			
			// Make it primary button
			frm.page.set_primary_action(__('Open Chat'), function() {
				window.location.href = `/app/app-development-chat?session=${encodeURIComponent(frm.doc.name)}`;
			});
		}
	}
});
