from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.validation import (
	overlapping_mapping_exists,
	validate_account_number,
	validate_date_range,
)


class BMDPartyMapping(Document):
	def validate(self):
		validate_date_range(self.valid_from, self.valid_to)
		self.bmd_person_account = validate_account_number(self.bmd_person_account, _("BMD person account"))
		if self.party_type not in {"Customer", "Supplier"}:
			frappe.throw(_("Party Type must be Customer or Supplier."))
		if self.active and overlapping_mapping_exists(
			self, {"party_type": self.party_type, "party": self.party}
		):
			frappe.throw(_("An equally ranked party mapping overlaps this validity period."))
