# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class Updatecustomerinfoinsaleinvoice(Document):
	def validate(self):
		if self.docstatus == 1:
			self.update_invoice()

	def update_invoice(self):
		invoice = frappe.get_doc("Sales Invoice", self.sale_invoice)
		invoice.db_set('customer', self.customer, update_modified=False)
		invoice.db_set('rtn', self.rtn, update_modified=False)
		invoice.db_set('customer_name', self.customer_name, update_modified=False)
		invoice.db_set('client_name', self.customer_name, update_modified=False)
		invoice.db_set('tax_id', self.rtn, update_modified=False)

	def on_trash(self):
		frappe.throw(_("Yo cant delete this element."))