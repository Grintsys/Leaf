from __future__ import unicode_literals
from frappe import _

def get_data():
    return [
      {
			"label": _("Inscriptions Students"),
			"icon": "fa fa-microchip ",
			"items": [
				{
					"type": "doctype",
					"name": "Admin Enrolled Students",
					"description": _("List Admin Enrolled Students")
				},
				{
					"type": "doctype",
					"name": "Enrolled Student",
					"description": _("List Enrolled Student"),
				},
				{
					"type": "doctype",
					"name": "Withdraw Course",
					"description": _("List Withdraw Course"),
				},
				# {
				# 	"type": "doctype",
				# 	"name": "Frecuency Enrolled Students",
				# 	"description": _("List Frecuency Enrolled Students")
				# },
				{
					"type": "doctype",
					"name": "Settings Enrolled Students",
					"description": _("List Settings Enrolled Students"),
				},
				{
					"type": "doctype",
					"name": "Update Biometric Data Students",
					"description": _("List Update Biometric Data Students"),
				},
				{
					"type": "report",
					"name": "Details Enrolled Students",
					"doctype": "Enrolled Student",
					"is_query_report": True
				}
            ]
      }
  ]
