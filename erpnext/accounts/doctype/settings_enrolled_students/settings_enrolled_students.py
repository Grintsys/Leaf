# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class SettingsEnrolledStudents(Document):
	def validate(self):
		if self.docstatus == 0:
			registers = frappe.get_all("Settings Enrolled Students", {"name"})

			if len(registers) > 0:
				if registers[0].name != self.name:
					frappe.throw(_("Exist a register for configurate Settings Enrolled Students."))
	
	def get_prefix(self, arg=None):
		prefixes = ""
		options = ""
		try:
			options = self.get_options('Sales Invoice')
		except frappe.DoesNotExistError:
			frappe.msgprint(_('Unable to find DocType {0}').format(d))

		if options:
			prefixes = prefixes + "\n" + options

		prefixes.replace("\n\n", "\n")
		prefixes = prefixes.split("\n")
		prefixes = "\n".join(sorted(prefixes))

		return {
			"prefix": prefixes
		}

	def get_options(self, arg=None):
		if frappe.get_meta(arg or self.select_doc_for_series).get_field("naming_series"):
			return frappe.get_meta(arg or self.select_doc_for_series).get_field("naming_series").options
