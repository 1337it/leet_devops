frappe.ui.form.on('Dev Chat Session', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Open Chat'), function() {
                frappe.set_route('dev-chat', frm.doc.name);
            });
        }
    }
});
