// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Details Enrolled Students"] = {
	"filters": [
		{
			"fieldname": "admin_enrolled_students",
			"label": __("Admin Enrolled Students"),
			"fieldtype": "Link",
			"options": "Admin Enrolled Students",
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "enrolled_students",
			"label": __("Enrolled Student"),
			"fieldtype": "Link",
			"options": "Enrolled Student"
		},
		{
			"fieldname":"type",
			"label": __("Type"),
			"fieldtype": "Select",
			"options": "Enrollment\nMonthly Payment\nGraduation Expenses"
		}
	]
};
