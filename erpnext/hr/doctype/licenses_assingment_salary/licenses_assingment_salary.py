# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class LicensesAssingmentSalary(Document):
	def validate(self):
		self.status = self.get_status()
	
	def on_update(self):		
		if self.docstatus == 0:
			self.generate_total_registers()	
			self.reload()		
	
	def get_status(self):
		if self.docstatus == 0:
			status = "Saved"
		elif self.docstatus == 1:
			self.validate_assignment_Salary_Component()
			status = "Finished"
		return status
	
	def on_cancel(self):
		self.eliminate_salary_component()
		if self.docstatus == 2:
			self.status = "Cancelled"
	
	def validate_assignment_Salary_Component(self):
		employees = frappe.get_all("Employee Detail Salary Component Licenses", ["employee","amount_deduction", "amount_earning", "parent"], filters = {"parent": self.name})
		
		licenseClassification = frappe.get_doc('License Classification', self.license_classification)

		for item in employees:
			salary_slip = frappe.get_all("Salary Slip", ["name"], filters={"payroll_entry":self.payroll_entry, "employee":item.employee})
			
			for salary in salary_slip:
				doc = frappe.get_doc("Salary Slip", salary.name)
				row = doc.append("earnings", {})
				row.salary_component = licenseClassification.earning_salary_component
				row.amount = item.amount_earning
				doc.save()

				doc_de = frappe.get_doc("Salary Slip", salary.name)
				row = doc_de.append("deductions", {})
				row.salary_component = licenseClassification.deduction_salary_component
				row.amount = item.amount_deduction
				doc_de.save()
	
	def eliminate_salary_component(self):	

		employees = frappe.get_all("Employee Detail Salary Component Licenses", ["employee","moneda", "parent"], filters = {"parent": self.name})
		
		for item in employees:
			salary_slip = frappe.get_all("Salary Slip", ["name"], filters={"payroll_entry":self.payroll_entry, "employee":item.employee})
			
			licenseClassification = frappe.get_doc('License Classification', self.license_classification)

			for salary in salary_slip:
				doc = frappe.get_doc("Salary Slip", salary.name)

				type_component = ""

				type_component = doc.earnings

				for component in type_component:
					if component.salary_component == licenseClassification.earning_salary_component:
						salary_detail = frappe.get_all("Salary Detail", ["name"], filters = {"salary_component":licenseClassification.earning_salary_component, "parent":salary.name})
						frappe.delete_doc("Salary Detail", salary_detail[0].name)

				type_component = doc.deductions

				for component in type_component:
					if component.salary_component == licenseClassification.deduction_salary_component:
						salary_detail = frappe.get_all("Salary Detail", ["name"], filters = {"salary_component":licenseClassification.deduction_salary_component, "parent":salary.name})
						frappe.delete_doc("Salary Detail", salary_detail[0].name)

				self.update_data(salary.name)
					
	def update_data(self, salary_name):
		doc = frappe.get_doc("Salary Slip", salary_name)

		total_earnings = 0
		total_deductions = 0

		for item in doc.earnings:
			total_earnings += item.amount
		
		for item in doc.deductions:
			total_deductions += item.amount
		
		net_pay = total_earnings - total_deductions
		rounded_total = round(net_pay)
		
		doc.gross_pay = total_earnings
		doc.total_deduction = total_deductions
		doc.net_pay = net_pay
		doc.rounded_total = rounded_total

		doc.save()
		
	def generate_total_registers(self):
		total = 0
		
		configRRHH = frappe.get_single('HR Settings')

		licenseClassification = frappe.get_doc('License Classification', self.license_classification)

		earningsalarayComponent = frappe.get_doc('Salary Component', licenseClassification.earning_salary_component)

		deductionsalarayComponent = frappe.get_doc('Salary Component', licenseClassification.deduction_salary_component)

		factorEarning = 1
		factorDduction = 1

		if configRRHH.business_days == None:
			frappe.throw(_('Assign Business Days For Pay in HR Settings'))

		if configRRHH.daily_hours == None:
			frappe.throw(_('Assign Daily Hours in HR Settings'))

		if earningsalarayComponent.factor > 0:
			factorEarning = earningsalarayComponent.factor

		if deductionsalarayComponent.factor > 0:
			factorDduction = deductionsalarayComponent.factor

		for d in self.get("employees"):
			register = frappe.get_doc('Employee Detail Salary Component Licenses', d.name)
			employee = d.employee + ": " + d.employee_name

			base = frappe.get_all('Salary Structure Assignment', ['base'], filters = {'employee': d.employee})

			if(len(base) == 0):
				frappe.throw(_('This employee {} no have a Salary Structure Assignment').format(employee))

			# register.amount_deduction = (base[0].base/configRRHH.business_days)*factorDduction*d.time

			# if(d.standard_time != ''): register.amount_deduction += (base[0].base/configRRHH.business_days)*1*d.standard_time

			# register.amount_earning = (base[0].base/configRRHH.business_days)*factorEarning*d.time 

			# if(d.standard_time != ''): register.amount_earning += (base[0].base/configRRHH.business_days)*1*d.standard_time 

			# dias no subsidiados * salaridiario * 100% -- Primeros 3 dias de incapacidad
			register.total_company = d.standard_time * (base[0].base/configRRHH.business_days) * 1
			
			# dias subsidiados * salario diario * porcentaje empresa de la clasificacion -- Valor a pagar incapacidad
			register.total_company += d.time * (base[0].base/configRRHH.business_days) * (licenseClassification.daily_base_company/100)

			# salario diario empresa - salario diario ihss * dias ihss * porcentaje -- Valor de incapacidad no pagado por el IHSS
			register.total_company += ((base[0].base/configRRHH.business_days) - (licenseClassification.salary_base/configRRHH.business_days)) * d.time * (licenseClassification.daily_base_ihss/100)
			
			# (dias subsidiados + dias no subsidiados) * salario base -- monto a deducir
			register.amount_deduction = (d.time + d.standard_time) * (base[0].base/configRRHH.business_days)

			# monto a deducir - total pagado por compania -- monto del seguro
			register.total_ihss = register.amount_deduction - register.total_company

			# total compania + total seguro -- Monto de percepcion
			register.amount_earning = register.total_company

			register.save()

			total += register.amount_earning

		self.total = total
		self.db_set('total', total, update_modified=False)
