from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.constants import DEFAULT_DOCUMENT_FILENAME_TEMPLATE
from kmu_erp_austria.bmd_export.services.naming import validate_filename_template


class BMDExportSettings(Document):
	def autoname(self):
		self.name = self.company

	def validate(self):
		if frappe.db.exists("BMD Export Settings", {"company": self.company, "name": ["!=", self.name]}):
			frappe.throw(_("Only one BMD Export Settings record is allowed per company."))
		if not self.document_filename_template:
			self.document_filename_template = DEFAULT_DOCUMENT_FILENAME_TEMPLATE
		validate_filename_template(self.document_filename_template)
		self.csv_filename = (self.csv_filename or "buchungen.csv").strip()
		if (
			"/" in self.csv_filename
			or "\\" in self.csv_filename
			or self.csv_filename in {".", ".."}
			or len(self.csv_filename) > 255
			or re.search(r'[:*?"<>|\x00-\x1f\x7f]', self.csv_filename)
			or not self.csv_filename.lower().endswith(".csv")
		):
			frappe.throw(_("CSV filename must be a plain filename ending in .csv."))
		if self.max_booking_rows <= 0 or self.max_booking_rows > 20000:
			frappe.throw(_("Maximum booking rows must be between 1 and 20,000."))
		if self.max_file_size_mb <= 0:
			frappe.throw(_("Maximum attachment size must be greater than zero."))
		if self.retention_days <= 0:
			frappe.throw(_("Artifact retention must be greater than zero days."))

		profile = frappe.get_doc("BMD Export Profile", self.export_profile)
		if not profile.is_active:
			frappe.throw(_("The selected BMD export profile is inactive."))
		try:
			self.csv_filename.encode(profile.encoding)
		except UnicodeEncodeError:
			frappe.throw(_("CSV filename cannot be represented in the selected profile encoding."))

	@property
	def normalized_extensions(self) -> set[str]:
		return {
			value.strip().lower().lstrip(".")
			for value in (self.allowed_extensions or "").replace("\n", ",").split(",")
			if value.strip()
		}

	@property
	def normalized_mime_types(self) -> set[str]:
		return {
			value.strip().lower()
			for value in (self.allowed_mime_types or "").replace("\n", ",").split(",")
			if value.strip()
		}
