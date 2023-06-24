# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RegistrationStudent(Document):
	def on_update(self):
		for student in self.get("students"):
			exist = frappe.get_list("Enrolled Student", ["*"], filters = {"registration": self.name, "customer": student.customer})

			if len(exist) == 0:
				doc = frappe.new_doc("Enrolled Student")
				doc.item = self.item
				doc.from_date = self.from_date
				doc.to_date = self.to_date
				doc.expiration_days = self.expiration_days
				doc.surcharge = self.surcharge
				doc.dues = self.dues
				doc.frecuency = self.frecuency
				doc.total_amount = self.total_amount
				doc.customer = student.customer
				doc.registration = self.name
				doc.save()
