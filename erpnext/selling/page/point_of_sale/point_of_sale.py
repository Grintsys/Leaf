# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.utils.nestedset import get_root_of
from frappe.utils import cint
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from datetime import datetime
import json

from six import string_types

@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, search_value="", pos_profile=None):
	data = dict()
	warehouse = ""
	display_items_in_stock = 0

	if pos_profile:
		warehouse, display_items_in_stock, company = frappe.db.get_value('POS Profile', pos_profile, ['warehouse', 'display_items_in_stock', 'company'])

	if not frappe.db.exists('Item Group', item_group):
		item_group = get_root_of('Item Group')

	if search_value:
		data = search_serial_or_batch_or_barcode_number(search_value)

	item_code = data.get("item_code") if data.get("item_code") else search_value
	serial_no = data.get("serial_no") if data.get("serial_no") else ""
	batch_no = data.get("batch_no") if data.get("batch_no") else ""
	barcode = data.get("barcode") if data.get("barcode") else ""

	condition = get_conditions(item_code, serial_no, batch_no, barcode)

	if pos_profile:
		condition += get_item_group_condition(pos_profile)

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])
	# locate function is used to sort by closest match from the beginning of the value


	result = []

	items_data = frappe.db.sql(""" SELECT name as item_code,
			item_name, image as item_image, idx as idx,is_stock_item
		FROM
			`tabItem`
		WHERE
			disabled = 0 and has_variants = 0 and is_sales_item = 1
			and item_group in (select name from `tabItem Group` where lft >= {lft} and rgt <= {rgt})
			and {condition} order by idx desc limit {start}, {page_length}"""
		.format(
			start=start, page_length=page_length,
			lft=lft, rgt=rgt,
			condition=condition
		), as_dict=1)

	cont = 0

	for i in range(len(items_data)):
		if cont > 0:
			i -= cont

		company_result = frappe.get_all("Item Default", ["name"], filters = {"parent": items_data[i].item_code, "company": company})

		if len(company_result) == 0:
			items_data.pop(i)
			cont += 1

	if items_data:
		items = [d.item_code for d in items_data]
		item_prices_data = frappe.get_all("Item Price",
			fields = ["item_code", "price_list_rate", "currency"],
			filters = {'price_list': price_list, 'item_code': ['in', items]})

		item_prices, bin_data = {}, {}
		for d in item_prices_data:
			item_prices[d.item_code] = d


		if display_items_in_stock:
			filters = {'actual_qty': [">", 0], 'item_code': ['in', items]}

			if warehouse:
				filters['warehouse'] = warehouse

			bin_data = frappe._dict(
				frappe.get_all("Bin", fields = ["item_code", "sum(actual_qty) as actual_qty"],
				filters = filters, group_by = "item_code")
			)

		for item in items_data:
			row = {}

			row.update(item)
			item_price = item_prices.get(item.item_code) or {}
			row.update({
				'price_list_rate': item_price.get('price_list_rate'),
				'currency': item_price.get('currency'),
				'actual_qty': bin_data.get('actual_qty')
			})

			result.append(row)

	res = {
		'items': result
	}

	if serial_no:
		res.update({
			'serial_no': serial_no
		})

	if batch_no:
		res.update({
			'batch_no': batch_no
		})

	if barcode:
		res.update({
			'barcode': barcode
		})

	return res

@frappe.whitelist()
def is_rounding(pos_profile):
	rounding = False

	pos = frappe.get_doc("POS Profile", pos_profile)
	if pos.round_off_discount == 1:
		rounding = True

	return {
		"rounding": rounding
	}

@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value):
	# search barcode no
	barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
	if barcode_data:
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}

def get_conditions(item_code, serial_no, batch_no, barcode):
	if serial_no or batch_no or barcode:
		return "name = {0}".format(frappe.db.escape(item_code))
			
	return """(name like {item_code} or item_name like {item_code} or active_component like {item_code})""".format(item_code = frappe.db.escape('%' + item_code + '%'))

@frappe.whitelist()
def get_isv(item):
	taxed15 = 0
	taxed18 = 0
	taxed_sales15 = 0
	taxed_sales18 = 0

	# Cargar el JSON
	data = json.loads(item)

	item_taxes = frappe.get_all("Item Tax", ['name', "item_tax_template"], filters = {"parent": data.get("item_code")})
	if len(item_taxes) >0:
		for item_tax in item_taxes:
			tax_tamplates = frappe.get_all("Item Tax Template", ["name"], filters = {"name": item_tax.item_tax_template})
					
			for tax_tamplate in tax_tamplates:

				tax_details = frappe.get_all("Item Tax Template Detail", ["name", "tax_rate", "tax_type"], filters = {"parent": tax_tamplate.name})
								
				for tax_detail in tax_details:
					# frappe.msgprint("tax detail {}".format(tax_detail))
					if tax_detail.tax_rate == 15:
						taxed_sales15 += data.get("amount")/1.15
						taxed15 += data.get("amount") - (data.get("amount")/1.15)
													
					if tax_detail.tax_rate == 18:
						taxed_sales18 += data.get("amount")/1.18
						taxed18 += data.get("amount") - (data.get("amount")/1.18)
	
	return taxed15, taxed18, taxed_sales15, taxed_sales18


def get_item_group_condition(pos_profile):
	cond = "and 1=1"
	item_groups = get_item_groups(pos_profile)
	if item_groups:
		cond = "and item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

	return cond % tuple(item_groups)

def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = []
	cond = "1=1"
	pos_profile= filters.get('pos_profile')

	if pos_profile:
		item_groups = get_item_groups(pos_profile)

		if item_groups:
			cond = "name in (%s)"%(', '.join(['%s']*len(item_groups)))
			cond = cond % tuple(item_groups)

	return frappe.db.sql(""" select distinct name from `tabItem Group`
			where {condition} and (name like %(txt)s) limit {start}, {page_len}"""
		.format(condition = cond, start=start, page_len= page_len),
			{'txt': '%%%s%%' % txt})