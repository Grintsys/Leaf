# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class WithdrawCourse(Document):
	def validate(self):
		if self.docstatus == 1:
			details = frappe.get_all("details of quotas", ["*"], filters = {"parent": self.enrolled_student, "paid": 0}, order_by='date asc')

			if len(details) == 0:
				frappe.throw(_("You don´t have pending payments for Enrolled Student {}.".format(self.enrolled_student)))

			for detail in details:
				doc = frappe.get_doc("details of quotas", detail.name)
				doc.paid = 1
				doc.db_set('paid', 1, update_modified=False)
				doc.db_set('coments', "RETIRED", update_modified=False)
				doc.save()
