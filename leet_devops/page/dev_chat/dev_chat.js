frappe.pages['dev-chat'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Dev Chat',
        single_column: true
    });
