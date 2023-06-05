// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Settings Enrolled Students', {
	onload: function(frm) {
		frm.events.get_prefix(frm);
	},

	get_prefix: function(frm) {
		frappe.call({
			method: "get_prefix",
			doc: frm.doc,
			callback: function(r) {
				frm.set_df_property("naming_series", "options", r.message.prefix);
			}
		});
	},
});
