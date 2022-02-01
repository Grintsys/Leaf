# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CancelBankChecks(Document):
	def validate(self):
		if self.docstatus == 1:
			self.update_journal_entry()
			self.modified_account()
			self.update_bank_transaction()
	
	def update_bank_transaction(self):
		doc = frappe.get_doc("Bank Transactions", self.check)
		doc.db_set('docstatus', 2, update_modified = False)
		doc.db_set('status', "Cancelled", update_modified = False)
	
	def update_journal_entry(self):
		journals = frappe.get_all("Journal Entry", ["*"], filters = {"bank_transaction": self.check})

		for journal in journals:
			doc = frappe.get_doc("Journal Entry", journal.name)
			doc.db_set('docstatus', 2, update_modified = False)
	
	def modified_account(self):
		doc = frappe.get_doc("Bank Account", self.bank_account)

		doc.deferred_debits -= self.amount
		
		doc.current_balance = doc.deferred_credits - doc.deferred_debits
		
		doc.save()