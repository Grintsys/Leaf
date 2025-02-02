# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _, get_all

def execute(filters=None):
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	if not salary_slips: return [], []

	columns, earning_types = get_columns(salary_slips)
	ss_earning_map = get_ss_earning_map(salary_slips)
	ss_ded_map = get_ss_ded_map(salary_slips)
	doj_map = get_employee_doj_map()

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

	data = []
	for ss in salary_slips:
		# row = [ss.name, ss.employee, ss.employee_name, doj_map.get(ss.employee), ss.branch, ss.department, ss.designation,ss.company, ss.start_date, ss.end_date, ss.leave_without_pay, ss.payment_days]
		# 	ss.company, ss.start_date, ss.end_date, ss.leave_without_pay, ss.payment_days]	

		# if not ss.branch == None:columns[3] = columns[3].replace('-1','120')
		# if not ss.department  == None: columns[4] = columns[4].replace('-1','120')
		# if not ss.designation  == None: columns[5] = columns[5].replace('-1','120')
		# if not ss.leave_without_pay  == None: columns[9] = columns[9].replace('-1','130')

		# for e in earning_types:
		# 	row.append(e.)
		split = ss.name.split("/")
		name = split[1]
		Employee = frappe.get_all("Salary Structure Assignment", ["name", "employee","employee_name", "base"], filters = {"employee": ss.employee})


		row = [ss.employee_name, ss.payment_days]
		
		if len(Employee) > 0:
			row += [Employee[0].base]
		else:
			row += [0]

		incomes = 0

		income_list = frappe.get_all("Salary Detail", ["*"], filters = {"parent": ss.name})

		for inc in income_list:
			component = frappe.get_doc("Salary Component", inc.salary_component)

			if component.type == "Earning" and component.name != "Base":
				incomes += inc.amount

		row += [incomes]

		row += [ss.gross_pay]

		row += [ss.total_deduction, ss.net_pay]

		if ss.employee in confidential_list:
			if confidential_payroll[0].rol in roles_arr:
				if filters.get("department"):
					employee_data = frappe.get_doc("Employee", ss.employee)
					if employee_data.department == filters.get("department"):
						data.append(row)
				else:
					data.append(row)
		else:
			if filters.get("department"):
				employee_data = frappe.get_doc("Employee", ss.employee)
				if employee_data.department == filters.get("department"):
					data.append(row)
			else:
				data.append(row)
	
	row = ["ELABORADO POR:", "","","","","",""]
	data.append(row)

	row = ["REVISADO POR:", "","","","","",""]
	data.append(row)

	return columns, data

def get_columns(salary_slips):
	"""
	columns = [
		_("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140",
		_("Date of Joining") + "::80", _("Branch") + ":Link/Branch:120", _("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120", _("Company") + ":Link/Company:120", _("Start Date") + "::80",
		_("End Date") + "::80", _("Leave Without Pay") + ":Float:130", _("Payment Days") + ":Float:120"
	]
	"""
	columns = [
		_("Employee Name") + "::140", _("Payment Days") + "::140", _("Salary Base") + ":Currency:120",
		_("Extra Income") + ":Currency:120", _("Gross Pay") + ":Currency:120",_("Total Deduction") + ":Currency:120", _("Net Pay") + ":Currency:120"
	]

	# columns = [
	# 	_("Employee Name") + "::140", _("Payment Days") + "::140", _("Salary Base") + "::140",
	# 	_("Gross Pay") + "::140", _("Total Deduction") + "::140", _("Net Pay") + ":::140"
	# ]

	salary_components = {_("Earning"): [], _("Deduction"): []}

	# for component in frappe.db.sql("""select distinct sd.salary_component, sc.type
	# 	from `tabSalary Detail` sd, `tabSalary Component` sc
	# 	where sc.name=sd.salary_component and sd.amount != 0 and sd.parent in (%s)""" %
	# 	(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1):
	# 	salary_components[_(component.type)].append(component.salary_component)

	# columns = columns + [(e + ":Currency:120") for e in salary_components[_("Earning")]] + \
	# 	[_("Gross Pay") + ":Currency:120"] + [(d + ":Currency:120") for d in salary_components[_("Deduction")]] + \
	# 	[_("Loan Repayment") + ":Currency:120", _("Total Deduction") + ":Currency:120", _("Net Pay") + ":Currency:120"]

	#return columns, salary_components[_("Earning")], salary_components[_("Deduction")]
	return columns, salary_components[_("Earning")]

def get_salary_slips(filters):
	filters.update({"from_date": filters.get("from_date"), "to_date":filters.get("to_date")})
	conditions, filters = get_conditions(filters)
	salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where %s
		order by employee""" % conditions, filters, as_dict=1)

	return salary_slips or []

def get_conditions(filters):
	conditions = ""
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	if filters.get("docstatus"):
		conditions += "docstatus = {0}".format(doc_status[filters.get("docstatus")])

	if filters.get("from_date"): conditions += " and start_date >= %(from_date)s"
	if filters.get("to_date"): conditions += " and end_date <= %(to_date)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"

	return conditions, filters

def get_employee_doj_map():
	return	frappe._dict(frappe.db.sql("""
				SELECT
					employee,
					date_of_joining
				FROM `tabEmployee`
				"""))

def get_ss_earning_map(salary_slips):
	ss_earnings = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_earning_map = {}
	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map

def get_ss_ded_map(salary_slips):
	ss_deductions = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_ded_map = {}
	for d in ss_deductions:
		ss_ded_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_ded_map
