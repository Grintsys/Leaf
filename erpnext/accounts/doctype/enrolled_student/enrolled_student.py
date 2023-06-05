# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe import _

class EnrolledStudent(Document):
	def validate(self):
		self.calculate_quotas()

	def calculate_quotas(self):
		for detail in self.get("details"):
			frappe.delete_doc("details of quotas", detail.name)

		initial_date = self.from_date
		amount = self.total_amount/self.dues 
		days = frappe.db.get_value("Frecuency Enrolled Students", self.frecuency, "days")

		for i in range(self.dues):	
			initial_date = str(initial_date).split(" ")[0]	
			initial_date =  datetime.strptime(initial_date, '%Y-%m-%d') + timedelta(days)

			row = self.append("details", {})
			row.date = initial_date
			row.amount = amount
			row.paid = 0
	
	def create_sale_invoice(self):
		settings = frappe.get_all("Settings Enrolled Students", ["*"])

		if len(settings) == 0:
			frappe.throw(_("Create Settings Enrolled Students."))
		
		if settings[0].item == None:
			frappe.throw(_("Assign a Product for late payments in Settings Enrolled Students."))
		
		details = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.name, "paid": 0})

		if len(details) == 0:
			frappe.throw(_("You don´t have pending payments."))
		
		now = datetime.now()
		amount = 0
		qty = 0
		mora = 0
		mora_qty = 0		

		for detail in details:
			if amount == 0:
				amount = detail.amount
			
			if datetime.strptime(str(detail.date).split(" ")[0], '%Y-%m-%d') <= datetime.strptime(str(now).split(" ")[0], '%Y-%m-%d'):
				qty += 1

			initial_date =  detail.date + timedelta(self.expiration_days)

			if datetime.strptime(str(initial_date).split(" ")[0], '%Y-%m-%d') < datetime.strptime(str(now).split(" ")[0], '%Y-%m-%d'):
				if mora == 0: mora = self.surcharge
				mora_qty += 1

		if qty == 0: qty = 1
		if amount == 0: amount = self.total_amount/self.dues 

		doc = frappe.new_doc('Sales Invoice')
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

		row = doc.append("items", {})
		row.item_code = self.item
		row.qty = qty
		row.rate = amount

		if mora > 0:
			row = doc.append("items", {})
			row.item_code = settings[0].item
			row.qty = mora_qty
			row.rate = mora

		doc.save()

		frappe.msgprint(_("Sales invoice {} created.".format(doc.name)))