# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CancelEnrolledStudent(Document):
	def validate(self):
		if self.docstatus == 0:
			if len(self.get("registration_detail")) == 0:
				self.saveData()
		if self.docstatus == 1:
			self.update_enrolled()

	def saveData(self):
		for detail in self.get("details"):
			frappe.delete_doc("details of quotas cancel", detail.name)
		
		for detail in self.get("registration_detail"):
			frappe.delete_doc("details of quotas cancel", detail.name)
		
		for detail in self.get("graduation_expenses"):
			frappe.delete_doc("details of graduation expenses cancel", detail.name)

		enrolled = frappe.get_doc("Enrolled Student", self.enrolled_student)

		for i in enrolled.get("registration_detail"):
			row = self.append("registration_detail", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = i.pay
			row.paid = i.paid
			row.coments = i.coments
			row.type = i.type

		for i in enrolled.get("details"):	
			row = self.append("details", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = i.pay
			row.paid = i.paid
			row.coments = i.coments
			row.type = i.type
		
		for i in enrolled.get("graduation_expenses"):	
			row = self.append("graduation_expenses", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = i.pay
			row.paid = i.paid
			row.coments = i.coments
			row.type = i.type
	
	def update_enrolled(self):
		for detail in self.get("details"):
			registers = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.enrolled_student, "type": "Enrollment", "date": detail.date})

			for register in registers:
				reg = frappe.get_doc("details of quotas", register.name)
				reg.paid = detail.paid
				reg.coments = detail.coments
				reg.save()
		
		for detail in self.get("registration_detail"):
			registers = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.enrolled_student, "type": "Monthly Payment", "date": detail.date})

			for register in registers:
				reg = frappe.get_doc("details of quotas", register.name)
				reg.paid = detail.paid
				reg.coments = detail.coments
				reg.save()
		
		for detail in self.get("graduation_expenses"):
			registers = frappe.get_all("details of graduation expenses", ["*"], filters = {"parent": self.enrolled_student, "date": detail.date})

			for register in registers:
				reg = frappe.get_doc("details of graduation expenses", register.name)
				reg.paid = detail.paid
				reg.coments = detail.coments
				reg.save()