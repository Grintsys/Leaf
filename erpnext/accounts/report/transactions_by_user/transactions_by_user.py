# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import datetime
import time

def execute(filters=None):
	if not filters: filters = {}
	data = get_data(filters)

	columns = [
		{
   			"fieldname": "date",
  			"fieldtype": "Data",
  			"label": "Date",
  		},
		{
   			"fieldname": "time",
  			"fieldtype": "Data",
  			"label": "Time",
  		},
		{
			"label": _("Reference Doctype"),
			"fieldname": "reference_doctype",
			"width": 240
		},
		{
			"label": _("Reference Name"),
			"fieldname": "reference_name",
			"fieldtype": "Dynamic Link",
			"options": "reference_doctype",
			"width": 240
		},
		{
   			"fieldname": "item_description",
  			"fieldtype": "Data",
  			"label": "Item Description",
			"fieldtype": "Link",
			"options": "Item",
  		},
		{
			"fieldname": "quantity",
   			"fieldtype": "Float",
   			"label": "Quantity"
		},
		{
			"fieldname": "warehouse",
   			"fieldtype": "Data",
   			"label": "Warehouse"
		},
		{
			"fieldname": "item_group",
   			"fieldtype": "Data",
   			"label": "Item Group"
		},
		{
			"fieldname": "user",
   			"fieldtype": "Data",
   			"label": "User"
		}
	]

	return columns, data

def get_data(filters):
	data = []
	if filters.get("from_date"): from_date = filters.get("from_date")
	if filters.get("to_date"): to_date = filters.get("to_date")
	from_time = datetime.datetime.strptime(filters.get("from_time"), '%H:%M:%S')
	to_time = datetime.datetime.strptime(filters.get("to_time"), '%H:%M:%S')

	conditions = return_filters(filters, from_date, to_date)

	stock_entries = frappe.get_all("Stock Entry" , ["*"], filters = conditions)

	for entry in stock_entries:		
		hour_invoice_str = convert(entry.posting_time.seconds)
		hour_invoice = datetime.datetime.strptime(hour_invoice_str, '%H:%M:%S')
		if hour_invoice >= from_time and hour_invoice <= to_time:
			items = frappe.get_all("Stock Entry Detail", ["*"], filters = {"parent": entry.name})
			for item in items:
				row = [entry.posting_date, entry.posting_time, "Stock Entry", entry.name, item.item_code, item.qty, entry.from_warehouse, item.item_group, entry.owner]
				data.append(row)

	purchase_receipts = frappe.get_all("Purchase Receipt" , ["*"], filters = conditions)

	for receipt in purchase_receipts:
		hour_invoice_str = convert(receipt.posting_time.seconds)
		hour_invoice = datetime.datetime.strptime(hour_invoice_str, '%H:%M:%S')
		if hour_invoice >= from_time and hour_invoice <= to_time:
			items = frappe.get_all("Purchase Receipt Item", ["*"], filters = {"parent": receipt.name})
			for item in items:
				row = [receipt.posting_date, receipt.posting_time, "Purchase Receipt", receipt.name, item.item_code, item.qty, receipt.set_warehouse, item.item_group, receipt.owner]
				data.append(row)
	
	purchase_invoices = frappe.get_all("Purchase Invoice" , ["*"], filters = conditions)

	for purchase in purchase_invoices:
		hour_invoice_str = convert(purchase.posting_time.seconds)
		hour_invoice = datetime.datetime.strptime(hour_invoice_str, '%H:%M:%S')
		if hour_invoice >= from_time and hour_invoice <= to_time:
			items = frappe.get_all("Purchase Invoice Item", ["*"], filters = {"parent": purchase.name})
			for item in items:
				row = [purchase.posting_date, purchase.posting_time, "Purchase Invoice", purchase.name, item.item_code, item.qty, purchase.set_warehouse, item.item_group, purchase.owner]
				data.append(row)
	
	conditions = return_filters_inventory_download(filters, from_date, to_date)
	inventory_downloads = frappe.get_all("Inventory Download" , ["*"], filters = conditions)

	for inventory in inventory_downloads:
		hour_invoice_str = convert(inventory.posting_time.seconds)
		hour_invoice = datetime.datetime.strptime(hour_invoice_str, '%H:%M:%S')
		if hour_invoice >= from_time and hour_invoice <= to_time:
			items = frappe.get_all("Inventory Download Detail", ["*"], filters = {"parent": inventory.name})
			for item in items:
				row = [inventory.creation_date, inventory.posting_time, "Inventory Download", inventory.name, item.item_code, item.qty, inventory.warehouse, item.item_group, inventory.owner]
				data.append(row)
	
	conditions = return_filters_dispatch(filters, from_date, to_date)
	dispatch_controls = frappe.get_all("Dispatch Control" , ["*"], filters = conditions)
	
	for dispatch in dispatch_controls:
		items = frappe.get_all("Dispatch Control Detail", ["*"], filters = {"parent": dispatch.name})
		for item in items:
			row = [dispatch.creation_date, "", "Dispatch Control", dispatch.name, item.item_code, item.qty, "", "", dispatch.owner]
			data.append(row)

	return data

def convert(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    return "%d:%02d:%02d" % (hour, minutes, seconds) 

def return_filters(filters, from_date, to_date):
	conditions = ''	

	conditions += "{"
	conditions += '"posting_date": ["between", ["{}", "{}"]]'.format(from_date, to_date)
	conditions += ', "company": "{}"'.format(filters.get("company"))
	conditions += ', "docstatus": 1'
	if filters.get("owner"): conditions += ', "owner": "{}"'.format(filters.get("owner"))
	conditions += '}'

	return conditions

def return_filters_inventory_download(filters, from_date, to_date):
	conditions = ''	

	conditions += "{"
	conditions += '"creation_date": ["between", ["{}", "{}"]]'.format(from_date, to_date)
	conditions += ', "company": "{}"'.format(filters.get("company"))
	conditions += ', "docstatus": 1'
	if filters.get("owner"): conditions += ', "owner": "{}"'.format(filters.get("owner"))
	conditions += '}'

	return conditions

def return_filters_dispatch(filters, from_date, to_date):
	conditions = ''	

	conditions += "{"
	conditions += '"creation_date": ["between", ["{}", "{}"]]'.format(from_date, to_date)
	conditions += ', "docstatus": 1'
	if filters.get("owner"): conditions += ', "owner": "{}"'.format(filters.get("owner"))
	conditions += '}'

	return conditions
