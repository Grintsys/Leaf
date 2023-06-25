# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class UpdateBiometricDataStudents(Document):
	def validate(self):
		if self.docstatus == 0:
			self.verificate_suscriptions()

	def verificate_suscriptions(self):
		for detail in self.get("cancel"):
			frappe.delete_doc("Update Biotemtric Data Students Details", detail.name)

		for detail in self.get("successful"):
			frappe.delete_doc("Update Biotemtric Data Students Details", detail.name)

		filters = self.filters()
		admin_enrolled_students = frappe.get_all("Admin Enrolled Students", ["*"], filters = filters)

		for admin in admin_enrolled_students:
			enrolled_students = frappe.get_all("Enrolled Student", ["*"], filters = {"admin_enrolled_students": admin.name})

			for enrolled in enrolled_students:
				registers = frappe.get_all("details of quotas", ["*"], filters = {"parent": enrolled.name, "date": ["<", self.date], "paid": 0})

				customer = frappe.get_doc("Customer", enrolled.customer)

				if len(registers) > 0:
					row = self.append("cancel", {})
					row.customer = enrolled.customer
					row.biometric_identifier = customer.biometric_identifier
				else:
					row = self.append("successful", {})
					row.customer = enrolled.customer
					row.biometric_identifier = customer.biometric_identifier
	
	def filters(self):
		conditions = ''

		conditions += "{"
		conditions += '"pre_from": ["<=", "{}"]'.format(self.date)
		conditions += ', "limit_date": [">=", "{}"]'.format(self.date)
		conditions += '}'

		return conditions
