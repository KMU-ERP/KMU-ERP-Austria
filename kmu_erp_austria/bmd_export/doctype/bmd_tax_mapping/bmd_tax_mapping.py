from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.validation import (
	overlapping_mapping_exists,
	validate_date_range,
	validate_link_company,
)


class BMDTaxMapping(Document):
	def validate(self):
		validate_date_range(self.valid_from, self.valid_to)
		validate_link_company("Account", self.erp_tax_account, self.company, _("ERPNext Tax Account"))
		self.bmd_tax_code = (self.bmd_tax_code or "").strip()
		if self.export_tax and (not self.bmd_tax_code or len(self.bmd_tax_code) > 4):
			frappe.throw(_("BMD tax code is required and may contain at most four characters."))
		if self.oss_target_country and len(self.oss_target_country) > 4:
			frappe.throw(_("OSS target country may contain at most four characters."))
		if self.active and overlapping_mapping_exists(
			self,
			{
				"transaction_type": self.transaction_type,
				"tax_rate": self.tax_rate,
				"tax_category": self.tax_category or ["is", "not set"],
				"country": self.country or ["is", "not set"],
				"country_group": self.country_group or ["is", "not set"],
				"erp_tax_account": self.erp_tax_account or ["is", "not set"],
			},
		):
			frappe.throw(_("An equally specific tax mapping overlaps this validity period."))
