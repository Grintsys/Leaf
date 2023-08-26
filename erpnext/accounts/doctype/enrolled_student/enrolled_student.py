# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe import _

class EnrolledStudent(Document):
	def update_admins_enrolled(self, arg=None):
		now = datetime.now()
		fecha_i = now.strftime('%d-%m-%Y')
		admins_enrolleds = frappe.get_all("Admin Enrolled Students", ["*"], filters = {"pre_from": ["<=", fecha_i], "limit_date": [">=", fecha_i], "able": 0})
		
		for admin in admins_enrolleds:
			doc = frappe.get_doc("Admin Enrolled Students", admin.name)
			doc.able = 1
			doc.save()
		
		admins_enrolleds = frappe.get_all("Admin Enrolled Students", ["*"], filters = {"limit_date": ["<", fecha_i], "able": 1})
		
		for admin in admins_enrolleds:
			doc = frappe.get_doc("Admin Enrolled Students", admin.name)
			doc.able = 0
			doc.save()

	def validate(self):
		invoices = frappe.get_all("Sales Invoice", ["*"], filters = {"enrolled_students": self.name})

		admin_enrolled = frappe.get_all("details quotes admin", ["*"], filters = {"parent": self.admin_enrolled_students})

		if(len(self.get("registration_detail")) + len(self.get("details")) != len(admin_enrolled)):
			if(len(invoices) == 0):
				self.calculate_quotas()
			else:
				frappe.throw(_("You can´t delete regiters."))

		if(len(invoices) == 0):
			self.verificate_customer()

	def calculate_quotas(self):
		for detail in self.get("details"):
			frappe.delete_doc("details of quotas", detail.name)
		
		for detail in self.get("registration_detail"):
			frappe.delete_doc("details of quotas", detail.name)
		
		for detail in self.get("graduation_expenses"):
			frappe.delete_doc("details of quotas", detail.name)

		admin_enrolled = frappe.get_doc("Admin Enrolled Students", self.admin_enrolled_students)

		for i in admin_enrolled.get("registration_detail"):	
			row = self.append("registration_detail", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = 0
			row.paid = 0
			row.coments = "UNPAID"
			row.type = i.type

		for i in admin_enrolled.get("details"):	
			row = self.append("details", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = 0
			row.paid = 0
			row.coments = "UNPAID"
			row.type = i.type
		
		for i in admin_enrolled.get("graduation_expenses"):	
			row = self.append("graduation_expenses", {})
			row.date = i.date
			row.item = i.item
			row.amount = i.amount
			row.pay = 0
			row.paid = 0
			row.coments = "UNPAID"
			row.type = i.type

	
	def verificate_customer(self):
		enrolleds = frappe.get_all("Enrolled Student", ["*"], filters = {"customer": self.customer})

		for enrolled in enrolleds:
			if enrolled.admin_enrolled_students != None:
				admin_enrolled = frappe.get_doc("Admin Enrolled Students", enrolled.admin_enrolled_students)

				details = frappe.get_all("details of quotas", ["*"], filters = {"parent": enrolled.name, "paid": 0})

				now = datetime.now()

				if datetime.strptime(str(admin_enrolled.final_date ).split(" ")[0], '%Y-%m-%d') < datetime.strptime(str(now).split(" ")[0], '%Y-%m-%d') and len(details) > 0:
					frappe.throw(_("This customer have another course not paid."))
	
	def create_sale_invoice(self):
		settings = frappe.get_all("Settings Enrolled Students", ["*"])

		if len(settings) == 0:
			frappe.throw(_("Create Settings Enrolled Students."))
		
		if settings[0].item == None:
			frappe.throw(_("Assign a Product for late payments in Settings Enrolled Students."))
		
		doc = frappe.new_doc('Sales Invoice')

		graduation_exp = True

		details_graduation_expenses = frappe.get_all("details of graduation expenses", ["*"], filters = {"parent": self.name, "paid": 0, "pay": 1})

		for det in details_graduation_expenses:
			row = doc.append("items", {})
			row.item_code = det.item
			row.qty = 1
			row.rate = det.amount
			row.description = str(det.date ) + " " + det.item

			graduation_exp = False

		details = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.name, "paid": 0, "pay": 1})

		if len(details) == 0 and graduation_exp:
			frappe.throw(_("You don´t have pending payments."))
		
		now = datetime.now()
		amount = 0
		qty = 0
		mora = 0
		mora_qty = 0		

		for detail in details:
			if amount == 0:
				amount = detail.amount

			details_before = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.name, "paid": 0, "pay": 0})

			for detail_b in details_before:
				if datetime.strptime(str(detail_b.date).split(" ")[0], '%Y-%m-%d') <= datetime.strptime(str(detail.date).split(" ")[0], '%Y-%m-%d'):
					frappe.throw(_("You are skipping the payment of the fee with the date: {}".format(detail_b.date)))
			
			if datetime.strptime(str(detail.date).split(" ")[0], '%Y-%m-%d') <= datetime.strptime(str(now).split(" ")[0], '%Y-%m-%d'):
				qty += 1

			# initial_date =  detail.date 

			apply_mora = True

			r_detail = self.get("registration_detail")

			for r_d in r_detail:
				if r_d.name == detail.name:
					apply_mora = False

			if apply_mora:
				if datetime.strptime(str(detail.date ).split(" ")[0], '%Y-%m-%d') < datetime.strptime(str(now).split(" ")[0], '%Y-%m-%d'):
					admin_enrolled = frappe.get_doc("Admin Enrolled Students", self.admin_enrolled_students)
					if mora == 0: mora = admin_enrolled.surcharge
					mora_qty += 1
			
			row = doc.append("items", {})
			row.item_code = detail.item
			row.qty = 1
			row.rate = detail.amount
			row.description = str(detail.date ) + " " + detail.item

		if qty == 0: qty = 1
		if amount == 0: amount = 0

		doc.naming_series = settings[0].naming_series
		doc.enrolled_students = self.name
		doc.due_date = now.date()
		doc.customer = self.customer
		# doc.reason_for_sale = self.reason_for_sale
		# doc.patient = self.patient
		# doc.selling_price_list = settings[0].price_list
		doc.ignore_pricing_rule = 1
		doc.excesses = 0
		doc.deductible = 0
		doc.ineligible_expenses = 0
		doc.co_pay20 = 0			

		if mora > 0:
			row = doc.append("items", {})
			row.item_code = settings[0].item
			row.qty = mora_qty
			row.rate = mora

		doc.save()

		frappe.msgprint(_("Sales invoice {} created.".format(doc.name)))