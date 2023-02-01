# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint, throw
from frappe.utils import getdate, nowdate
from frappe.model.document import Document
from datetime import datetime, timedelta, date
from frappe.model.naming import parse_naming_series

class CreditNoteCXC(Document):
	def validate(self):
		self.verificate_references_and_amount()
		self.calculate_total()
		if self.docstatus == 1:
			self.verificate_amount()
			self.update_accounts_status()
			self.apply_gl_entry()
			self.update_dashboard_customer()
	
	def on_cancel(self):
		self.update_dashboard_customer_cancel()
	
	def update_dashboard_customer(self):
		customers = frappe.get_all("Dashboard Customer",["*"], filters = {"customer": self.customer, "company": self.company})

		if len(customers) > 0:
			customer = frappe.get_doc("Dashboard Customer", customers[0].name)
			customer.total_unpaid -= self.amount_total
			customer.save()
		else:
			new_doc = frappe.new_doc("Dashboard Customer")
			new_doc.customer = self.customer
			new_doc.company = self.company
			new_doc.billing_this_year = 0
			new_doc.total_unpaid = self.amount_total * -1
			new_doc.insert()
	
	def update_dashboard_customer_cancel(self):
		customers = frappe.get_all("Dashboard Customer",["*"], filters = {"customer": self.customer, "company": self.company})

		if len(customers) > 0:
			customer = frappe.get_doc("Dashboard Customer", customers[0].name)
			customer.total_unpaid += self.amount_total
			customer.save()

	def calculate_total(self):
		if not self.get("references"):
			frappe.throw(_(" Required references"))
		total_reference = 0
		for d in self.get("references"):
			total_reference += d.total_amount
			self.total_references = total_reference

		if self.total_exempt > self.total_references:
			frappe.throw(_("Amount cannot be greater than the total references"))

		self.calculate_isv()
		total_base = 0
		if len(self.get("references")) > 0:
			if self.total_exempt != None:
				if not self.get("taxes"):
					self.amount_total = self.total_exempt
				else:
					for taxes_list in self.get("taxes"):
						total_base += taxes_list.base_isv
						if self.total_exempt != None:
							self.amount_total = total_base + self.total_exempt
						else:
							self.amount_total = total_base
						if self.isv_15 != None:
							self.amount_total = total_base + self.total_exempt + self.isv_15
						elif self.isv_18 != None:
							self.amount_total = total_base + self.total_exempt + self.isv_18
	
	def calculate_isv(self):
		for taxes_list in self.get("taxes"):
			item_tax_template = frappe.get_all("Item Tax Template", ["name"], filters = {"name": taxes_list.isv})
			for tax_template in item_tax_template:
				tax_details = frappe.get_all("Item Tax Template Detail", ["name", "tax_rate"], filters = {"parent": tax_template.name})
				for tax in tax_details:
					if tax.tax_rate == 15:
						tx_base = taxes_list.base_isv * (tax.tax_rate/100)
						self.isv_15 = tx_base
					elif tax.tax_rate == 18:
						tx_base = taxes_list.base_isv * (tax.tax_rate/100)
						self.isv_18 = tx_base

	def verificate_references_and_amount(self):
		if len(self.get("references")) > 1:
			order_by = sorted(self.references, key=lambda item: item.total_amount)
			remaining_amount = self.amount
			for d in order_by:
				if remaining_amount <= d.total_amount:
					result = d.total_amount - remaining_amount
					if result <= 0:
						frappe.throw(_("The amount can not be accepted to pay the bills, the amount must pay the bills or pay one and advance another."))

	def verificate_amount(self):
		remaining = 0
		amount_total = self.amount_total
		if len(self.get("references")) > 1:
			for d in sorted(self.references, key=lambda item: item.total_amount):
				sales_invoice = frappe.get_doc("Sales Invoice", d.reference_name)
				if amount_total > d.total_amount:
					amount_total -= d.total_amount
					if sales_invoice.outstanding_amount == d.total_amount:
						sales_invoice.status = "Paid"
					sales_invoice.outstanding_amount -= d.total_amount
				else:
					if amount_total <= d.total_amount:
						if sales_invoice.outstanding_amount == amount_total:
							sales_invoice.status = "Paid"
						sales_invoice.outstanding_amount -= amount_total
				sales_invoice.save()
		else: 
			for x in self.get("references"):
				if amount_total <= x.total_amount:
					sales_invoice = frappe.get_doc("Sales Invoice", x.reference_name)
					if sales_invoice.outstanding_amount == self.amount_total:
						sales_invoice.status = "Paid"
					sales_invoice.outstanding_amount -= self.amount_total
				sales_invoice.save()
	
	def update_accounts_status(self):
		customer = frappe.get_doc("Customer", self.customer)
		if customer:
			customer.credit += self.amount_total
			customer.remaining_balance -= self.amount_total
			customer.save()
	
	def assign_cai(self):
		cai = frappe.get_all("CAI", ["initial_number", "final_number", "name_cai", "cai", "issue_deadline", "prefix"], filters = { "status": "Active", "prefix": self.naming_series})
		if len(cai) == 0:
			frappe.throw(_("This secuence no assing cai"))
		current_value = self.get_current(cai[0].prefix)

		if current_value == None:
			current_value = 0

		now = datetime.now()

		date = now.date()

		if current_value + 1 <= int(cai[0].final_number) and str(date) <= str(cai[0].issue_deadline):
			self.assing_data(cai[0].cai, cai[0].issue_deadline, cai[0].initial_number, cai[0].final_number, cai[0].prefix)

			amount = int(cai[0].final_number) - current_value

			self.alerts(cai[0].issue_deadline, amount)
		else:
			cai_secondary = frappe.get_all("CAI", ["initial_number", "final_number", "name_cai", "cai", "issue_deadline", "prefix"], filters = { "status": "Pending", "prefix": self.naming_series})
			
			if len(cai_secondary) > 0:
				final = int(cai[0].final_number) + 1
				initial = int(cai_secondary[0].initial_number)
				if final == initial:
					self.assing_data(cai_secondary[0].cai, cai_secondary[0].issue_deadline, cai_secondary[0].initial_number, cai_secondary[0].final_number, cai_secondary[0].prefix)
					doc = frappe.get_doc("CAI", cai[0].name_cai)
					doc.status = "Inactive"
					doc.save()

					doc_sec = frappe.get_doc("CAI", cai_secondary[0].name_cai)
					doc_sec.status = "Active"
					doc_sec.save()

					new_current = int(cai_secondary[0].initial_number) - 1
					name = self.parse_naming_series(cai_secondary[0].prefix)

					frappe.db.set_value("Series", name, "current", new_current, update_modified=False)
				else:
					self.assing_data(cai[0].cai, cai[0].issue_deadline, cai[0].initial_number, cai[0].final_number, cai[0].prefix)
					frappe.throw("The CAI you are using is expired.")
			else:
				self.assing_data(cai[0].cai, cai[0].issue_deadline, cai[0].initial_number, cai[0].final_number, cai[0].prefix)
				frappe.throw("The CAI you are using is expired.")
	
	def get_current(self, prefix):
		pre = self.parse_naming_series(prefix)
		current_value = frappe.db.get_value("Series",
		pre, "current", order_by = "name")
		return current_value

	def parse_naming_series(self, prefix):
		parts = prefix.split('.')
		if parts[-1] == "#" * len(parts[-1]):
			del parts[-1]

		pre = parse_naming_series(parts)
		return pre
	
	def assing_data(self, cai, issue_deadline, initial_number, final_number, prefix):
		pre = self.parse_naming_series(prefix)

		self.cai = cai

		self.due_date_cai = issue_deadline

		self.authorized_range = "{}{} al {}{}".format(pre, self.serie_number(int(initial_number)), pre, self.serie_number(int(final_number)))

	
	def serie_number(self, number):

		if number >= 1 and number < 10:
			return("0000000" + str(number))
		elif number >= 10 and number < 100:
			return("000000" + str(number))
		elif number >= 100 and number < 1000:
			return("00000" + str(number))
		elif number >= 1000 and number < 10000:
			return("0000" + str(number))
		elif number >= 10000 and number < 100000:
			return("000" + str(number))
		elif number >= 100000 and number < 1000000:
			return("00" + str(number))
		elif number >= 1000000 and number < 10000000:
			return("0" + str(number))
		elif number >= 10000000:
			return(str(number))
	

	def before_naming(self):
		if self.docstatus == 0:
			self.assign_cai()
	
	def alerts(self, date, amount):
		gcai_setting = frappe.get_all("Cai Settings", ["expired_days", "expired_amount"])

		if len(gcai_setting) > 0:
			if amount <= gcai_setting[0].expired_amount:
				amount_rest = amount - 1
				frappe.msgprint(_("There are only {} numbers available for this CAI.".format(amount_rest)))
		
			now = date.today()
			days = timedelta(days=int(gcai_setting[0].expired_days))

			sum_dates = now+days

			if str(date) <= str(sum_dates):
				for i in range(int(gcai_setting[0].expired_days)):		
					now1 = date.today()
					days1 = timedelta(days=i)

					sum_dates1 = now1+days1
					if str(date) == str(sum_dates1):
						frappe.msgprint(_("This CAI expires in {} days.".format(i)))
						break
	
	def apply_gl_entry(self):
		currentDateTime = datetime.now()
		date = currentDateTime.date()
		year = date.strftime("%Y")

		fecha_inicial = '01-01-{}'.format(year)
		fecha_final = '31-12-{}'.format(year)
		fecha_i = datetime.strptime(fecha_inicial, '%d-%m-%Y')
		fecha_f = datetime.strptime(fecha_final, '%d-%m-%Y')

		fiscal_year = frappe.get_all("Fiscal Year", ["*"], filters = {"year_start_date": [">=", fecha_i], "year_end_date": ["<=", fecha_f]})

		doc = frappe.new_doc("GL Entry")
		doc.posting_date = self.posting_date
		doc.transaction_date = None
		doc.account = self.account_to_debit
		doc.party_type = "Customer"
		doc.party = self.customer
		doc.cost_center = self.cost_center
		doc.debit = self.amount_total
		doc.credit = 0
		doc.account_currency = self.currency
		doc.debit_in_account_currency = self.amount_total
		doc.credit_in_account_currency = 0
		doc.against = self.account_to_credit
		doc.against_voucher_type = self.doctype
		doc.against_voucher = self.name
		doc.voucher_type =  self.doctype
		doc.voucher_no = self.name
		doc.voucher_detail_no = None
		doc.project = None
		doc.remarks = 'No Remarks'
		doc.is_opening = "No"
		doc.is_advance = "No"
		doc.fiscal_year = fiscal_year[0].name
		doc.company = self.company
		doc.finance_book = None
		doc.to_rename = 1
		doc.due_date = None
		# doc.docstatus = 1
		doc.insert()

		doc = frappe.new_doc("GL Entry")
		doc.posting_date = self.posting_date
		doc.transaction_date = None
		doc.account = self.account_to_credit
		doc.party_type = "Customer"
		doc.party = self.customer
		doc.cost_center = self.cost_center
		doc.debit = 0
		doc.credit = self.amount_total
		doc.account_currency = self.currency
		doc.debit_in_account_currency = 0
		doc.credit_in_account_currency = self.amount_total
		doc.against = self.account_to_debit
		doc.against_voucher_type = self.doctype
		doc.against_voucher = self.name
		doc.voucher_type =  self.doctype
		doc.voucher_no = self.name
		doc.voucher_detail_no = None
		doc.project = None
		doc.remarks = 'No Remarks'
		doc.is_opening = "No"
		doc.is_advance = "No"
		doc.fiscal_year = fiscal_year[0].name
		doc.company = self.company
		doc.finance_book = None
		doc.to_rename = 1
		doc.due_date = None
		# doc.docstatus = 1
		doc.insert()