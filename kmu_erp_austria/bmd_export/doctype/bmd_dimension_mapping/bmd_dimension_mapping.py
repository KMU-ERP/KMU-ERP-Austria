from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.validation import (
	overlapping_mapping_exists,
	validate_date_range,
)


class BMDDimensionMapping(Document):
	def validate(self):
		validate_date_range(self.valid_from, self.valid_to)
		self.source_value = (self.source_value or "").strip()
		self.source_field = (self.source_field or "").strip()
		self.bmd_value = (self.bmd_value or "").strip()
		if not self.source_value or not self.bmd_value:
			frappe.throw(_("Source and BMD dimension values are required."))
		if len(self.bmd_value) > 20:
			frappe.throw(_("BMD dimension values may contain at most 20 characters."))
		if self.source_type == "Accounting Dimension" and not self.source_field:
			frappe.throw(_("Accounting Dimension Field is required."))
		if self.source_type != "Accounting Dimension":
			self.source_field = ""
		if self.active and overlapping_mapping_exists(
			self,
			{
				"source_type": self.source_type,
				"source_field": self.source_field or ["is", "not set"],
				"source_value": self.source_value,
				"target_field": self.target_field,
			},
		):
			frappe.throw(_("An equally ranked dimension mapping overlaps this validity period."))
