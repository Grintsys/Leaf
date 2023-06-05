// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Enrolled Student', {
	// refresh: function(frm) {

	// }
	refresh: function (frm) {
		frm.events.make_custom_buttons(frm);
	},

	make_custom_buttons: function (frm) {
		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__("Sales Invoice"),
				() => frm.events.create_sale_invoice(frm), __('Create'));

			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},

	create_sale_invoice: function (frm) {
		frappe.call({
			method: "create_sale_invoice",
			doc: frm.doc,
		});
	},
});
