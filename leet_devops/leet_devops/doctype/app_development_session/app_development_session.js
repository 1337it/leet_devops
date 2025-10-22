frappe.ui.form.on('App Development Session', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Open Chat Interface'), function() {
				frappe.set_route('app-development-chat', {'session': frm.doc.name});
			}, __('Actions'));
			
			// Make it primary button
			frm.page.set_primary_action(__('Open Chat'), function() {
				window.location.href = `/app/app-development-chat?session=${encodeURIComponent(frm.doc.name)}`;
			});
		}
	}
});
