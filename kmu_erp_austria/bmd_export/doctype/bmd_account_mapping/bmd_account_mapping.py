from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.validation import (
	overlapping_mapping_exists,
	validate_date_range,
	validate_link_company,
)


class BMDAccountMapping(Document):
	def validate(self):
		validate_date_range(self.valid_from, self.valid_to)
		validate_link_company("Account", self.erpnext_account, self.company, _("ERPNext Account"))
		validate_link_company("BMD Account", self.bmd_account, self.company, _("BMD Account"))
		if self.active and overlapping_mapping_exists(
			self,
			{
				"erpnext_account": self.erpnext_account,
				"country": self.country or ["is", "not set"],
				"tax_category": self.tax_category or ["is", "not set"],
				"item_group": self.item_group or ["is", "not set"],
			},
		):
			frappe.throw(_("An equally specific account mapping overlaps this validity period."))
