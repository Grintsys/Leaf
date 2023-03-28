# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class ReportSalaryRegisterDetail(Document):
	def validate(self):
		employee = "Total"
		day_of_payment = 0
		salary_base = 0
		adjustment_retactive = 0
		extra_hours = 0
		base = 0
		cobertura = 0
		plus = 0
		work_days = 0
		extra_income = 0
		pago_bruto = 0
		days_not_work = 0
		payment_adjustment_salary_slip = 0
		ihss = 0
		isr = 0
		optica = 0
		ondontology = 0
		neighborhood_tax = 0
		prestamos = 0
		university_ujn = 0
		cafe = 0
		salary_advance = 0
		ladylee = 0
		coperative_elga = 0
		missing = 0
		rap = 0
		salary_slip_adjusment_payment = 0
		uncorresponding_disability_payment = 0
		total_deduction = 0
		net_pay = 0

		self.delete_rows()
		data_list = self.data()

		for data in data_list:
			row = self.append("employees", {})
			row.employee = data[0]
			row.day_of_payment = data[1]
			row.salary_base = data[2]
			row.adjustment_retactive = data[3]
			row.extra_hours = data[4]
			row.base = data[5]
			row.cobertura = data[6]
			row.plus = data[7]
			row.work_days = data[8]
			row.extra_income = data[9]
			row.pago_bruto = data[10]
			row.days_not_work = data[11]
			row.payment_adjustment_salary_slip = data[12]
			row.ihss = data[13]
			row.isr = data[14]
			row.optica = data[15]
			row.ondontology = data[16]
			row.neighborhood_tax = data[17]
			row.prestamos = data[18]
			row.university_ujn = data[19]
			row.cafe = data[20]
			row.salary_advance = data[21]
			row.ladylee = data[22]
			row.coperative_elga = data[23]
			row.missing = data[24]
			row.rap = data[25]
			row.salary_slip_adjusment_payment = data[26]
			row.uncorresponding_disability_payment = data[27]
			row.total_deduction = data[28]
			row.net_pay = data[29]

			day_of_payment += data[1]
			salary_base += data[2]
			adjustment_retactive += data[3]
			extra_hours += data[4]
			base += data[5]
			cobertura += data[6]
			plus += data[7]
			work_days += data[8]
			extra_income += data[9]
			pago_bruto += data[10]
			days_not_work += data[11]
			payment_adjustment_salary_slip += data[12]
			ihss += data[13]
			isr += data[14]
			optica += data[15]
			ondontology += data[16]
			neighborhood_tax += data[17]
			prestamos += data[18]
			university_ujn += data[19]
			cafe += data[20]
			salary_advance += data[21]
			ladylee += data[22]
			coperative_elga += data[23]
			missing += data[24]
			rap += data[25]
			salary_slip_adjusment_payment += data[26]
			uncorresponding_disability_payment += data[27]
			total_deduction += data[28]
			net_pay += data[29]

		row = self.append("employees", {})
		row.employee = employee
		row.day_of_payment = day_of_payment
		row.salary_base = salary_base
		row.adjustment_retactive = adjustment_retactive
		row.extra_hours = extra_hours
		row.base = base
		row.cobertura = cobertura
		row.plus = plus
		row.work_days = work_days
		row.extra_income = extra_income
		row.pago_bruto = pago_bruto
		row.days_not_work = days_not_work
		row.payment_adjustment_salary_slip = payment_adjustment_salary_slip
		row.ihss = ihss
		row.isr = isr
		row.optica = optica
		row.ondontology = ondontology
		row.neighborhood_tax = neighborhood_tax
		row.prestamos = prestamos
		row.university_ujn = university_ujn
		row.cafe = cafe
		row.salary_advance = salary_advance
		row.ladylee = ladylee
		row.coperative_elga = coperative_elga
		row.missing = missing
		row.rap = rap
		row.salary_slip_adjusment_payment = salary_slip_adjusment_payment
		row.uncorresponding_disability_payment = uncorresponding_disability_payment
		row.total_deduction = total_deduction
		row.net_pay = net_pay
		
	def delete_rows(self):
		rows = frappe.get_all("Report Salary Register Detail Table", ["name"], filters = {"parent": self.name})

		for row in rows:
			frappe.delete_doc("Report Salary Register Detail Table", row.name)

	def data(self):
		salary_components_Earning = frappe.get_all("Salary Component", ["name"], filters = {"type": "Earning"})
		salary_components_deduction = frappe.get_all("Salary Component", ["name"], filters = {"type": "Deduction"})
		data = []

		if self.from_date: from_date = self.from_date
		if self.to_date: to_date = self.to_date
		conditions = self.get_conditions(from_date, to_date)

		confidential_list = []

		roles_arr = []

		confidential_payroll = frappe.get_all("Confidential Payroll Employee", ["*"])

		if len(confidential_payroll) > 0:

			employees = frappe.get_all("Confidential Payroll Detail", ["*"], filters = {"parent": confidential_payroll[0].name})

			for employee in employees:
				confidential_list.append(employee.employee)
			
			user = frappe.session.user

			users = frappe.get_all("User", ["*"], filters = {"name": user})

			roles = frappe.get_all("Has Role", ["*"], filters = {"parent": users[0].name})

			for role in roles:
				roles_arr.append(role.role)		

		salary_slips = frappe.get_all("Salary Slip", ["name", "employee", "gross_pay", "total_deduction", "net_pay", "employee_name", "payment_days"], filters = conditions)
		
		for ss in salary_slips:
			Employee = frappe.get_all("Salary Structure Assignment", ["name", "employee","employee_name", "base"], filters = {"employee": ss.employee})

			salary_detail = frappe.get_all("Salary Detail", ["name", "salary_component", "amount"], filters = {"parent":ss.name})

			row = [ss.employee_name, ss.payment_days]

			if len(Employee) > 0:		
				row += [Employee[0].base]
			else:
				row += [0]

			for sc in salary_components_Earning:
				salarydetail = frappe.get_all("Salary Detail", ["name", "salary_component", "amount"], filters = {"salary_component":sc.name})
				if len(salarydetail) > 0:
					value_component = 0
					for sdd in salary_detail:
						if sc.name == sdd.salary_component:
							value_component = sdd.amount
					
					row += [value_component]

			incomes = 0

			income_list = frappe.get_all("Salary Detail", ["*"], filters = {"parent": ss.name})

			for inc in income_list:
				component = frappe.get_doc("Salary Component", inc.salary_component)

				if component.type == "Earning" and component.name != "Base":
					incomes += inc.amount

			row += [incomes]

			row += [ss.gross_pay]
			
			for coldata in salary_components_deduction:			
				salarydetail = frappe.get_all("Salary Detail", ["name", "salary_component", "amount"], filters = {"salary_component":coldata.name})
				if len(salarydetail) > 0:
					value_component = 0
					for sdd in salary_detail:
						if coldata.name == sdd.salary_component:
							value_component = sdd.amount
					
					row += [value_component]	

			row += [ss.total_deduction, ss.net_pay]

			if ss.employee in confidential_list:
				if confidential_payroll[0].rol in roles_arr:
					if self.department:
						employee_data = frappe.get_doc("Employee", ss.employee)
						if employee_data.department == self.department:
							data.append(row)
					else:
						data.append(row)
			else:
				if self.department:
					employee_data = frappe.get_doc("Employee", ss.employee)
					if employee_data.department == self.department:
						data.append(row)
				else:
						data.append(row)

		return data

	def get_conditions(self, from_date, to_date):
		conditions = ''
		doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

		conditions += "{"
		conditions += '"posting_date": ["between", ["{}", "{}"]]'.format(from_date, to_date)
		if self.docstatusvalue:
			conditions += ', "docstatus": {0}, '.format(doc_status[self.docstatusvalue])

		
		if self.company: conditions += '"company": "{}"'.format(self.company)
		if self.employee: conditions += ', "employee": "{}"'.format(self.mployee)
		conditions += "}"

		return conditions
