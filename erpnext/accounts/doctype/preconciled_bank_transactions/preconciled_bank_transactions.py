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
		details = frappe.get_all("precociled bank transactions detail", ["name"], filters = {"parent": self.name})

		for detail in details:
			frappe.delete_doc("precociled bank transactions detail", detail.name)

		condition = self.conditions()
		bank_transactions = frappe.get_all("Bank Transactions", ["name", "amount_data"], filters = condition)

		for transaction in bank_transactions:
			row = self.append("detail", {})
			row.bank_transaction = transaction.name
			row.amount_data = transaction.amount_data
		
		if self.type_transaction == "Bank Check":
			conditionPayment = self.conditionsPayment()
			payments = frappe.get_all("Payment Entry", ["name", "paid_amount"], filters = conditionPayment)

			for payment in payments:
				row = self.append("detail_payment", {})
				row.payment_entry = payment.name
				row.amount_data = payment.paid_amount
	
	def preconciled_transaction(self):
		for d in self.get("detail"):
			bank_transaction = frappe.get_doc("Bank Transactions", d.bank_transaction)
			bank_transaction.db_set('status', "Pre-reconciled", update_modified=False)

		for d in self.get("detail_payment"):	
			bank_transaction = frappe.get_doc("Payment Entry", d.payment_entry)
			bank_transaction.db_set('prereconcilied', 1 , update_modified=False)
	
	def conditionsPayment(self):
		conditions = ''

		conditions += "{"
		conditions += '"posting_date": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "mode_of_payment": "Cheque"'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += ', "prereconcilied": 0'
		conditions += ', "reconciled": 0'
		conditions += '}'

		return conditions

	def conditions(self):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "transaction_data": "{}"'.format(self.type_transaction)
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += ', "status": "Transit"'
		conditions += '}'

		return conditions
