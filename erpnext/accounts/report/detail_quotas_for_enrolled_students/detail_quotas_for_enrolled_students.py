# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	columns = [
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "enrolled_student",
			"label": _("Enrolled Student"),
			"fieldtype": "Link",
			"options": "Enrolled Student",
			"width": 120
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120
		},
		{
			"fieldname": "comments",
			"label": _("Comments"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 120
		}
	]
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	
	conditions = return_filters(filters)
	
	enrolleds = frappe.get_all("Enrolled Student", ["*"], filters = conditions)
	
	for enrolled in enrolleds:
		if filters.get("type") == "" or filters.get("type") == "Enrollment":
			for registration_detail in enrolled.get("registration_detail"):
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Enrollment"]
				data.append(row)
			
		if filters.get("type") == "" or filters.get("type") == "Monthly Payment":
			for registration_detail in enrolled.get("details"):
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Monthly Payment"]
				data.append(row)
		
		if filters.get("type") == "" or filters.get("type") == "Graduation Expenses":
			for registration_detail in enrolled.get("graduation_expenses"):
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Graduation Expenses"]
				data.append(row)

	return data

def return_filters(filters):
	conditions = ''	

	conditions += "{"
	conditions += '"admin_enrolled_students": "{}"'.format(filters.get("admin_enrolled_students"))
	if filters.get("customer"): conditions += ', "customer": "{}"'.format(filters.get("customer"))
	if filters.get("enrolled_student"): conditions += ', "name": "{}"'.format(filters.get("enrolled_student"))
	conditions += '}'

	return conditions