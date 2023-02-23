# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint, _

class SettingItemWise(Document):
	def validate(self):
		register = frappe.get_all("Setting Item Wise", ["*"])

		if len(register):
			if register[0].name != self.name:
				frappe.throw(_("Already exist a Settign Item Wise."))
