# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.utils import update_included_uom_in_report

def execute(filters=None):
	include_uom = filters.get("include_uom")
	columns = get_columns()
	items = get_items(filters)
	sl_entries = get_stock_ledger_entries(filters, items)
	item_details = get_item_details(items, sl_entries, include_uom)
	opening_row = get_opening_balance(filters, columns)

	data = []
	groups = []
	products = []
	type_transactions = []
	conversion_factors = []
	if opening_row:
		data.append(opening_row)

	actual_qty = stock_value = 0
	for sle in sl_entries:
		item_detail = item_details[sle.item_code]

		sle.update(item_detail)

		if filters.get("batch_no"):
			actual_qty += sle.actual_qty
			stock_value += sle.stock_value_difference

			if sle.voucher_type == 'Stock Reconciliation':
				actual_qty = sle.qty_after_transaction
				stock_value = sle.stock_value
			
			sle.update({
				"qty_after_transaction": actual_qty,
				"stock_value": stock_value
			})

	for sle in sl_entries:
		new_group = True
		if sle.item_group in groups:
			new_group = False
		
		if new_group:
			groups.append(sle.item_group)
		
		new_product = True
		if sle.item_code in products:
			new_product = False
		
		if new_product:
			products.append(sle.item_code)
		
		new_transaction = True
		if sle.voucher_type in type_transactions:
			new_transaction = False
		
		if new_transaction:
			type_transactions.append(sle.voucher_type)

	for group in groups:
		group_list = []
		products_list = []
		transaction_list = []
		group_row = [{'indent': 0.0, "transaction": group}]	

		for sle in sl_entries:
			if sle.item_group == group:
				group_list += [{'indent': 1.0, "transaction": "", "item_code":sle.item_code, "item_name":sle.item_name, "voucher_type":"", "voucher_no":"",
				"stock_uom":0, "actual_qty":0, "qty_after_transaction":0, "incoming_rate":0, "valuation_rate":0, "stock_value":0}]

				# for product in products:
				# 	for sle_product in sl_entries:
				# 		if sle_product.item_code == product:
				# 			group_list += [{'indent': 2.0, "transaction": "", "item_code":"", "item_name":"", "voucher_type":sle_product.voucher_type, "voucher_no":"",
				# 			"stock_uom":0, "actual_qty":0, "qty_after_transaction":0, "incoming_rate":0, "valuation_rate":0, "stock_value":0}]

				# 			for type in type_transactions:
				# 				for sle_transaction in sl_entries:
				# 					if sle_transaction.voucher_type == type:
				# 						group_list += [{'indent': 3.0, "transaction": "", "item_code":"", "item_name":"","voucher_type":"", "voucher_no":sle_transaction.voucher_no, 
				# 						"stock_uom":sle_transaction.stock_uom, "actual_qty":sle_transaction.actual_qty, "qty_after_transaction":sle_transaction.qty_after_transaction, "incoming_rate":sle_transaction.incoming_rate, "valuation_rate":sle_transaction.valuation_rate, "stock_value":sle_transaction.stock_value,}]
			for product in products:
				if sle.item_code == product:
					group_list += [{'indent': 2.0, "transaction": "", "item_code":"", "item_name":"", "voucher_type":sle.voucher_type, "voucher_no":"",
					"stock_uom":0, "actual_qty":0, "qty_after_transaction":0, "incoming_rate":0, "valuation_rate":0, "stock_value":0}]

			for type in type_transactions:
				if sle.voucher_type == type:
					group_list += [{'indent': 3.0, "transaction": "", "item_code":"", "item_name":"","voucher_type":"", "voucher_no":sle.voucher_no, 
					"stock_uom":sle.stock_uom, "actual_qty":sle.actual_qty, "qty_after_transaction":sle.qty_after_transaction, "incoming_rate":sle.incoming_rate, "valuation_rate":sle.valuation_rate, "stock_value":sle.stock_value,}]


		data.extend(group_row or [])
		data.extend(group_list or [])
		# data.extend(products_list or [])
		# data.extend(transaction_list or [])

	update_included_uom_in_report(columns, data, include_uom, conversion_factors)
	return columns, data

def get_columns():
	columns = [
		{"label": _("Group"), "fieldname": "transaction", "width": 100},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 100},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
		{"label": _("Voucher #"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 100},
		{"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 100},
		{"label": _("Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 50, "convertible": "qty"},
		{"label": _("Balance Qty"), "fieldname": "qty_after_transaction", "fieldtype": "Float", "width": 100, "convertible": "qty"},
		{"label": _("Incoming Rate"), "fieldname": "incoming_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
		{"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
		{"label": _("Balance Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency"}
	]

	return columns

def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	if items:
		item_conditions_sql = 'and sle.item_code in ({})'\
			.format(', '.join([frappe.db.escape(i) for i in items]))

	return frappe.db.sql("""select concat_ws(" ", posting_date, posting_time) as date,
			item_code, warehouse, actual_qty, qty_after_transaction, incoming_rate, valuation_rate,
			stock_value, voucher_type, voucher_no, batch_no, serial_no, company, project, stock_value_difference
		from `tabStock Ledger Entry` sle
		where company = %(company)s and
			posting_date between %(from_date)s and %(to_date)s
			{sle_conditions}
			{item_conditions_sql}
			order by posting_date asc, posting_time asc, creation asc"""\
		.format(
			sle_conditions=get_sle_conditions(filters),
			item_conditions_sql = item_conditions_sql
		), filters, as_dict=1)

def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("brand"):
			conditions.append("item.brand=%(brand)s")
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items

def get_item_details(items, sl_entries, include_uom):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sl_entries]))

	if not items:
		return item_details

	cf_field = cf_join = ""
	if include_uom:
		cf_field = ", ucd.conversion_factor"
		cf_join = "left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom=%s" \
			% frappe.db.escape(include_uom)

	res = frappe.db.sql("""
		select
			item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom {cf_field}
		from
			`tabItem` item
			{cf_join}
		where
			item.name in ({item_codes})
	""".format(cf_field=cf_field, cf_join=cf_join, item_codes=','.join(['%s'] *len(items))), items, as_dict=1)

	for item in res:
		item_details.setdefault(item.name, item)

	return item_details

def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("batch_no=%(batch_no)s")
	if filters.get("project"):
		conditions.append("project=%(project)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_opening_balance(filters, columns):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle
	last_entry = get_previous_sle({
		"item_code": filters.item_code,
		"warehouse_condition": get_warehouse_condition(filters.warehouse),
		"posting_date": filters.from_date,
		"posting_time": "00:00:00"
	})
	row = {}
	row["item_code"] = _("'Opening'")
	for dummy, v in ((9, 'qty_after_transaction'), (11, 'valuation_rate'), (12, 'stock_value')):
			row[v] = last_entry.get(v, 0)

	return row

def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
			warehouse_details.rgt)

	return ''

def get_item_group_condition(item_group):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		return "item.item_group in (select ig.name from `tabItem Group` ig \
			where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
			item_group_details.rgt)

	return ''
