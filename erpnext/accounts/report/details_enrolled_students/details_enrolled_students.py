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
		from_date = ""
		to_date = ""
		if filters.get("from_date"): from_date = filters.get("from_date")
		if filters.get("to_date"): to_date = filters.get("to_date")
		conditions = return_filters_details(filters, enrolled.name, from_date, to_date)


		deatil_list = frappe.get_all("details of quotas", ["*"], filters = conditions)

		deatil_list_expenses = frappe.get_all("details of graduation expenses", ["*"], filters = conditions)

		if filters.get("type"):	
			if filters.get("type") == "Enrollment":
				for registration_detail in deatil_list:
					if registration_detail.type == "Enrollment":
						row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, registration_detail.type]
						data.append(row)

			if filters.get("type") == "Monthly Payment":
				for registration_detail in deatil_list:
					if registration_detail.type == "Monthly Payment":
						row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, registration_detail.type]
						data.append(row)
			
			if filters.get("type") == "Graduation Expenses":
				for registration_detail in deatil_list_expenses:
					row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, registration_detail.type]
					data.append(row)
		else:
			
			for registration_detail in deatil_list:
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, registration_detail.type]
				data.append(row)
			
			for registration_detail in deatil_list_expenses:
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, registration_detail.type]
				data.append(row)

	return data

def return_filters(filters):
	conditions = ''	

	conditions += "{"
	conditions += '"admin_enrolled_students": "{}"'.format(filters.get("admin_enrolled_students"))
	if filters.get("customer"): conditions += ', "customer": "{}"'.format(filters.get("customer"))
	if filters.get("enrolled_students"): conditions += ', "name": "{}"'.format(filters.get("enrolled_students"))
	conditions += '}'

	return conditions

def return_filters_details(filters, parent, from_date, to_date):
	conditions = ''	

	conditions += "{"
	conditions += '"parent": "{}"'.format(parent)
	if filters.get("from_date") and filters.get("to_date"): conditions += ', "date": ["between", ["{}", "{}"]]'.format(from_date, to_date)
	conditions += '}'

	return conditions