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
		deatil_list = frappe.get_all("details of quotas", ["*"], filters = {"parent": enrolled.name})

		deatil_list_expenses = frappe.get_all("details of graduation expenses", ["*"], filters = {"parent": enrolled.name})

		last_register = deatil_list[len(deatil_list) - 1].name

		if filters.get("type"):
			if filters.get("type") == "Enrollment":
				row = [deatil_list[len(deatil_list) - 1].date, enrolled.name, enrolled.customer, deatil_list[len(deatil_list) - 1].coments, "Enrollment"]
				data.append(row)
				
			if filters.get("type") == "Monthly Payment":
				for registration_detail in deatil_list:
					if last_register != registration_detail.name:
						row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Monthly Payment"]
						data.append(row)
			
			if filters.get("type") == "Graduation Expenses":
				for registration_detail in deatil_list_expenses:
					row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Graduation Expenses"]
					data.append(row)
		else:
			row = [deatil_list[len(deatil_list) - 1].date, enrolled.name, enrolled.customer, deatil_list[len(deatil_list) - 1].coments, "Enrollment"]
			data.append(row)
			
			for registration_detail in deatil_list:
				if last_register != registration_detail.name:
					row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Monthly Payment"]
					data.append(row)
			
			for registration_detail in deatil_list_expenses:
				row = [registration_detail.date, enrolled.name, enrolled.customer, registration_detail.coments, "Graduation Expenses"]
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