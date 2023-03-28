# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PreconciledBankTransactions(Document):
	def validate(self):
		if self.docstatus == 0:
			self.add_registers()
		
		if self.docstatus == 1:
			self.preconciled_transaction()
	
	def add_registers(self):
		condition = self.conditions()
		bank_transactions = frappe.get_all("Bank Transactions", ["name", "amount_data"], filters = condition)

		for transaction in bank_transactions:
			row = self.append("detail", {})
			row.bank_transaction = transaction.name
			row.amount_data = transaction.amount_data
	
	def preconciled_transaction(self):
		for d in self.get("detail"):
			bank_transaction = frappe.get_doc("Bank Transactions", d.bank_transaction)
			bank_transaction.db_set('status', "Pre-reconciled", update_modified=False)
	
	def conditions(self):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "transaction_data": "{}"'.format(self.type_transaction)
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += ', "status": "Transit"'
		conditions += '}'

		return conditions
