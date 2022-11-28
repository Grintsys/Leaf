# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class BankBookReconciliations(Document):
	def validate(self):		
		if self.docstatus == 0:
			self.verificate_bank_account()
			self.delete_bank_transactions()
			self.add_bank_transactions()
			self.delete_payments()
			self.add_payments()
			self.transit_check()

		if self.docstatus == 1:
			self.verificate_defference_amount()
			# self.conciliation_transactions()
			self.create_reconciled_balance()
			self.modified_total_reconcilitiation_account()
			# self.mark_reconciled_payment_entry()
			self.conciliation_transactions_pre_reconciled()

	def on_update(self):
		if self.docstatus == 0:			
			self.transit_check_amount()
			self.bank_book_value()
			self.update_amount()
			self.conciliation_transactions_pre_reconciled_cancel()
	
	def on_cancel(self):
		# self.conciliation_transactions_cancel()
		self.modified_total_reconcilitiation_account_cancel()
		# self.mark_reconciled_payment_entry_cancel()

	def transit_check(self):
		filters_transactions= self.filters_bank_transactions_amounts("check")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		for transaction in transactions:
			no_document = transaction.no_bank_check

			self.set_new_row_detail(transaction.name, no_document, transaction.transaction_data, transaction.date_data, "Transit", transaction.amount_data)

		filters_payments = self.filters_payment_amount()

		payments = frappe.get_all("Payment Entry", ["*"], filters = filters_payments)

		for payment in payments:			
			is_validate = False

			if payment.mode_of_payment == "Cheque":
				is_validate = True
			if payment.mode_of_payment == "Transferencia Bancaria":
				# wire_transfer_amount += payment.paid_amount
				is_validate = True

			if is_validate:
				self.set_new_row_payments(payment.name, payment.payment_type, payment.posting_date, payment.paid_amount)

		filters_transactions= self.filters_bank_transactions_amounts("debit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		for transaction in transactions:
			no_document = transaction.next_note_nd
			self.set_new_row_detail(transaction.name, no_document, transaction.transaction_data, transaction.date_data, "Transit", transaction.amount_data)

		filters_transactions= self.filters_bank_transactions_amounts("credit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		for transaction in transactions:
			no_document = transaction.next_note_nc
			self.set_new_row_detail(transaction.name, no_document, transaction.transaction_data, transaction.date_data, "Transit", transaction.amount_data)

		filters_transactions= self.filters_bank_transactions_amounts("deposit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		for transaction in transactions:
			no_document = transaction.document
			self.set_new_row_detail(transaction.name, no_document, transaction.transaction_data, transaction.date_data, "Transit", transaction.amount_data)
	
	def transit_check_amount(self):
		filters_transactions= self.filters_bank_transactions_amounts_by_range("check")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		bank_check_transit_amount = 0

		for transaction in transactions:
			bank_check_transit_amount += transaction.amount_data

		filters_payments = self.filters_payment_amount_by_range()

		payments = frappe.get_all("Payment Entry", ["*"], filters = filters_payments)

		for payment in payments:		

			if payment.mode_of_payment == "Cheque":
				bank_check_transit_amount += payment.paid_amount
		
		self.db_set('bank_check_transit_amount', bank_check_transit_amount, update_modified=False)

		filters_transactions= self.filters_bank_transactions_amounts_by_range("debit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		debit_note_transit = 0

		for transaction in transactions:
			debit_note_transit += transaction.amount_data
		
		self.db_set('debit_note_transit', debit_note_transit, update_modified=False)

		filters_transactions= self.filters_bank_transactions_amounts_by_range("credit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		credit_note_transit = 0

		for transaction in transactions:
			credit_note_transit += transaction.amount_data
		
		self.db_set('credit_note_transit', credit_note_transit, update_modified=False)

		filters_transactions= self.filters_bank_transactions_amounts_by_range("deposit")
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		bank_deposit_transit = 0

		for transaction in transactions:
			bank_deposit_transit += transaction.amount_data
		
		self.db_set('bank_deposit_transit', bank_deposit_transit, update_modified=False)
	
	def update_amount(self):
		account = frappe.get_doc("Bank Account", self.bank_account)
		
		self.db_set('total_last_reconciliations', account.total_reconciliation, update_modified=False)
		self.db_set('date_last_reconciliations', account.reconciliation_date, update_modified=False)

		self.transaction_amount = self.credit_note_transit - self.bank_check_transit_amount - self.debit_note_transit + self.bank_deposit_transit + self.wire_transfer_amount

		self.db_set('transaction_amount', self.transaction_amount, update_modified=False)

		if self.bank_amount == '':
			self.bank_amount = 0

		# self.actual_total_conciliation = self.bank_amount + self.credit_note_amount - self.bank_check_amount - self.debit_note_amount + self.bank_deposit_amount + self.wire_transfer_amount

		self.actual_total_conciliation = self.bank_amount + self.credit_note_transit - self.bank_check_transit_amount - self.debit_note_transit + self.bank_deposit_transit + self.wire_transfer_amount

		self.defference_amount = self.actual_total_conciliation - self.book_balance

		if self.actual_total_conciliation < 0:
			self.actual_total_conciliation = self.actual_total_conciliation * -1

		self.db_set('defference_amount', self.defference_amount, update_modified=False)
		self.db_set('actual_total_conciliation', self.actual_total_conciliation, update_modified=False)
	
	def delete_bank_transactions(self):
		transactions = frappe.get_all("Bank reconciliations Table", ["*"], filters = {"parent": self.name})

		for transaction in transactions:
			frappe.delete_doc("Bank reconciliations Table", transaction.name)

	def add_bank_transactions(self):
		filters_transactions = self.filters_bank_transactions()
		transactions = frappe.get_all("Bank Transactions", ["*"], filters = filters_transactions)

		bank_check_amount = 0
		credit_note_amount = 0
		debit_note_amount = 0
		bank_deposit_amount = 0

		for transaction in transactions:

			if transaction.check:
				bank_check_amount += transaction.amount_data
		
			if transaction.debit_note:
				debit_note_amount += transaction.amount_data

			if transaction.credit_note:
				credit_note_amount += transaction.amount_data
			
			if transaction.bank_deposit:
				bank_deposit_amount += transaction.amount_data
		
		self.db_set('bank_check_amount', bank_check_amount, update_modified=False)
		self.db_set('credit_note_amount', credit_note_amount, update_modified=False)
		self.db_set('debit_note_amount', debit_note_amount, update_modified=False)
		self.db_set('bank_deposit_amount', bank_deposit_amount, update_modified=False)
	
	def bank_book_value(self):
		account = frappe.get_doc("Bank Account", self.bank_account)
		
		self.db_set('total_last_reconciliations', account.total_reconciliation, update_modified=False)
		self.db_set('date_last_reconciliations', account.reconciliation_date, update_modified=False)

		if self.bank_check_transit_amount == None: self.bank_check_transit_amount = 0
		if self.bank_check_amount == None: self.bank_check_amount = 0
		if self.debit_note_amount == None: self.debit_note_amount = 0
		if self.debit_note_transit == None: self.debit_note_transit = 0
		if self.credit_note_amount == None: self.credit_note_amount = 0
		if self.credit_note_transit == None: self.credit_note_transit = 0
		if self.bank_deposit_amount == None: self.bank_deposit_amount = 0
		if self.bank_deposit_transit == None: self.bank_deposit_transit = 0
		if self.total_last_reconciliations == None: self.total_last_reconciliations = 0
		if self.wire_transfer_amount == None: self.wire_transfer_amount = 0

		check = self.bank_check_amount + self.bank_check_transit_amount
		debit_note = self.debit_note_amount + self.debit_note_transit
		credit_note = self.credit_note_amount + self.credit_note_transit
		deposit = self.bank_deposit_amount + self.bank_deposit_transit

		debits_totals = debit_note + check
		credits_totals = deposit + credit_note + self.wire_transfer_amount
		book_balance = self.total_last_reconciliations + credits_totals - debits_totals

		self.db_set('book_balance', book_balance, update_modified=False)

	def set_new_row_detail(self, bank_trasaction, no_document, type, date, mode, amount):
		row = self.append("detail", {})
		row.bank_trasaction = bank_trasaction
		row.no_document = no_document
		row.type = type
		row.date = date
		row.mode = mode
		row.amount = amount
	
	def delete_payments(self):
		transactions = frappe.get_all("Bank reconciliations payment entry Table", ["*"], filters = {"parent": self.name})

		for transaction in transactions:
			frappe.delete_doc("Bank reconciliations payment entry Table", transaction.name)
	
	def add_payments(self):
		filters_payments = self.filters_payment()
		payments = frappe.get_all("Payment Entry", ["*"], filters = filters_payments)
		
		bank_check_amount = self.bank_check_amount
		wire_transfer_amount = 0

		for payment in payments:

			if payment.mode_of_payment == "Cheque":
				bank_check_amount += payment.paid_amount
			if payment.mode_of_payment == "Transferencia Bancaria":
				wire_transfer_amount += payment.paid_amount
		
		self.db_set('bank_check_amount', bank_check_amount, update_modified=False)
		self.db_set('wire_transfer_amount', wire_transfer_amount, update_modified=False)
		
	def set_new_row_payments(self, payment_entry, type, date, amount):
		row = self.append("payment_entry_detail", {})
		row.payment_entry = payment_entry
		row.type = type
		row.date = date
		row.amount = amount

	def verificate_defference_amount(self):
		if self.defference_amount != 0:
			frappe.throw(_("Difference amount must be 0"))

	def conciliation_transactions_pre_reconciled(self):
		conditions = self.filters_bank_transactions_prereconciled()
		details = frappe.get_all("Bank Transactions", ["*"], filters = conditions)

		for detail in details:
			doc = frappe.get_doc("Bank Transactions", detail.name)
			doc.docstatus = 5
			doc.status = "Reconciled"
			doc.db_set('conciliation', self.name, update_modified=False)
			doc.conciliation = self.name
			doc.save()
	
	def conciliation_transactions_pre_reconciled_cancel(self):
		conditions = self.filters_bank_transactions_prereconciled_cancel()
		details = frappe.get_all("Bank Transactions", ["*"], filters = conditions)

		for detail in details:
			doc = frappe.get_doc("Bank Transactions", detail.name)
			doc.docstatus = 3
			doc.status = "Transit"
			doc.save()
	
	def conciliation_transactions(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction"], filters = {"parent": self.name})

		for detail in details:
			doc = frappe.get_doc("Bank Transactions", detail.bank_trasaction)
			doc.docstatus = 5
			doc.status = "Reconciled"
			doc.save()
	
	def conciliation_transactions_cancel(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction"], filters = {"parent": self.name})

		for detail in details:
			doc = frappe.get_doc("Bank Transactions", detail.bank_trasaction)
			doc.docstatus = 3
			doc.status = "Transit"
			doc.save()
	
	def mark_reconciled_payment_entry(self):
		details = frappe.get_all("Bank reconciliations payment entry Table", ["payment_entry"], filters = {"parent": self.name})

		for detail in details:
			doc = frappe.get_doc("Payment Entry", detail.payment_entry)
			doc.db_set('reconciled', 1, update_modified=False)
			doc.save()
	
	def mark_reconciled_payment_entry_cancel(self):
		details = frappe.get_all("Bank reconciliations payment entry Table", ["payment_entry"], filters = {"parent": self.name})

		for detail in details:
			doc = frappe.get_doc("Payment Entry", detail.payment_entry)
			doc.db_set('reconciled', 0, update_modified=False)
			doc.save()
	
	def create_reconciled_balance(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction", "amount"], filters = {"parent": self.name})

		if len(details) > 0:
			transaction = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data"], filters = {"name": details[0].bank_trasaction})
			
			if len(transaction) > 0:
				doc = frappe.new_doc("Reconciled balances")
				doc.reconciled_date = self.date
				doc.reconciled_balance = self.bank_amount
				doc.docstatus = 1
				doc.bank_account = transaction[0].bank_account
				doc.insert()
	
	def modified_total_reconcilitiation_account(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction", "amount"], filters = {"parent": self.name})
		
		if len(details) > 0:
			transaction = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data"], filters = {"name": details[0].bank_trasaction})
			doc = frappe.get_doc("Bank Account", transaction[0].bank_account)
			if len(transaction) > 0:
				doc.reconciliation_date = self.date
				doc.total_reconciliation = self.actual_total_conciliation

			for detail in details:
				transac = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data", "amount_data"], filters = {"name": detail.bank_trasaction})
				if transac[0].transaction_data == "Bank Check" or transac[0].transaction_data== "Debit Note":
					doc.deferred_debits -= transac[0].amount_data
				else:
					doc.deferred_credits -= transac[0].amount_data
			
			doc.current_balance = doc.deferred_credits - doc.deferred_debits

			doc.save()
	
	def modified_total_reconcilitiation_account_cancel(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction", "amount"], filters = {"parent": self.name})
		
		if len(details) > 0:
			transaction = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data"], filters = {"name": details[0].bank_trasaction})
			doc = frappe.get_doc("Bank Account", transaction[0].bank_account)
			if len(transaction) > 0:
				doc.reconciliation_date = self.date_last_reconciliations
				doc.total_reconciliation = self.total_last_reconciliations

			for detail in details:
				transac = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data", "amount_data"], filters = {"name": detail.bank_trasaction})
				if transac[0].transaction_data == "Bank Check" or transac[0].transaction_data== "Debit Note":
					doc.deferred_debits += transac[0].amount_data
				else:
					doc.deferred_credits += transac[0].amount_data
			
			doc.current_balance = doc.deferred_credits - doc.deferred_debits

			doc.save()
	
	def verificate_bank_account(self):
		details = frappe.get_all("Bank reconciliations Table", ["bank_trasaction", "amount"], filters = {"parent": self.name})

		for detail in details:
			transaction = frappe.get_all("Bank Transactions", ["bank_account", "transaction_data"], filters = {"name": detail.bank_trasaction})

			if transaction[0].bank_account != self.bank_account:
				frappe.throw(_("Bank transaction {} has a different bank account {} than the one selected".format(detail.bank_trasaction, transaction[0].bank_account)))

	def filters_bank_transactions(self):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "status": "Pre-reconciled"'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)

		conditions += '}'

		return conditions
	
	def filters_bank_transactions_amounts(self, transaction):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["<=", "{}"]'.format(self.to_date)
		conditions += ', "status": "Transit"'
		if transaction == "check": conditions += ', "check": 1'
		if transaction == "deposit": conditions += ', "bank_deposit": 1'
		if transaction == "debit": conditions += ', "debit_note": 1'
		if transaction == "credit": conditions += ', "credit_note": 1'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions
	
	def filters_bank_transactions_prereconciled(self):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["<=", "{}"]'.format(self.to_date)
		conditions += ', "status": "Pre-reconciled"'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions
	
	def filters_bank_transactions_prereconciled_cancel(self):
		conditions = ''

		conditions += "{"
		conditions += '"conciliation": "{}"'.format(self.name)
		conditions += '}'

		return conditions
	
	def filters_payment(self):
		conditions = ''

		conditions += "{"
		conditions += '"posting_date": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "prereconcilied": 1'
		conditions += ', "reconciled": 0'
		conditions += ', "company": "{}"'.format(self.company)
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions
	
	def filters_payment_amount(self):
		conditions = ''
		
		conditions += "{"
		conditions += '"posting_date": ["<=", "{}"]'.format(self.to_date)
		conditions += ', "prereconcilied": 0'
		conditions += ', "reconciled": 0'
		conditions += ', "company": "{}"'.format(self.company)
		conditions += ', "status": "Submitted"'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions
	
	def filters_payment_amount_by_range(self):
		conditions = ''
		
		conditions += "{"
		conditions += '"posting_date": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "prereconcilied": 0'
		conditions += ', "reconciled": 0'
		conditions += ', "company": "{}"'.format(self.company)
		conditions += ', "status": "Submitted"'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions

	def filters_bank_transaction_by_name(self, name):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "name": "{}"',format(name)

		conditions += '}'

	def filters_bank_transactions_amounts_by_range(self, transaction):
		conditions = ''

		conditions += "{"
		conditions += '"date_data": ["between", ["{}", "{}"]]'.format(self.from_date, self.to_date)
		conditions += ', "status": "Transit"'
		if transaction == "check": conditions += ', "check": 1'
		if transaction == "deposit": conditions += ', "bank_deposit": 1'
		if transaction == "debit": conditions += ', "debit_note": 1'
		if transaction == "credit": conditions += ', "credit_note": 1'
		conditions += ', "bank_account": "{}"'.format(self.bank_account)
		conditions += '}'

		return conditions
