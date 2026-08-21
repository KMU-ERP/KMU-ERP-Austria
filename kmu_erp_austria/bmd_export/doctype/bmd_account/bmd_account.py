from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.validation import validate_account_number


class BMDAccount(Document):
	def autoname(self):
		self.name = frappe.generate_hash(length=10)

	def validate(self):
		self.account_number = validate_account_number(self.account_number)
		if frappe.db.exists(
			"BMD Account",
			{"company": self.company, "account_number": self.account_number, "name": ["!=", self.name]},
		):
			frappe.throw(_("BMD account {0} already exists for this company.").format(self.account_number))
