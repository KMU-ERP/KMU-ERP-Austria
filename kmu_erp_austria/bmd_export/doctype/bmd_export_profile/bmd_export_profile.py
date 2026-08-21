from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kmu_erp_austria.bmd_export.services.constants import (
	FIELD_REGISTRY,
	REQUIRED_COLUMNS,
	SUPPORTED_DELIMITERS,
	SUPPORTED_ENCODINGS,
)


class BMDExportProfile(Document):
	def autoname(self):
		self.name = self.profile_name

	def validate(self):
		if self.is_new() and self.is_standard and not self.flags.bmd_setup:
			frappe.throw(_("Standard BMD profiles can only be created by the app setup."))
		if not self.is_new():
			previous = frappe.db.get_value(
				self.doctype,
				self.name,
				[
					"is_standard", "is_active", "delimiter", "encoding", "decimal_separator", "date_format", "line_ending",
					"money_precision", "tax_rate_precision", "exchange_rate_precision", "quantity_precision",
				],
				as_dict=True,
			)
			if previous and previous.is_standard:
				old_columns = frappe.get_all(
					"BMD Export Profile Column",
					filters={"parent": self.name},
					pluck="field_name",
					order_by="idx asc",
				)
				new_columns = [row.field_name.strip().lower() for row in self.columns]
				format_changed = any(
					self.get(fieldname) != previous.get(fieldname)
					for fieldname in (
						"delimiter", "encoding", "decimal_separator", "date_format", "line_ending",
						"money_precision", "tax_rate_precision", "exchange_rate_precision", "quantity_precision",
					)
				)
				if format_changed or old_columns != new_columns or not self.is_standard or not self.is_active:
					frappe.throw(_("The app-provided BMD standard profile is immutable; create a copy instead."))
		if self.delimiter not in SUPPORTED_DELIMITERS:
			frappe.throw(_("Unsupported BMD delimiter."))
		if self.encoding not in SUPPORTED_ENCODINGS:
			frappe.throw(_("Unsupported BMD encoding."))
		if self.decimal_separator not in {".", ","}:
			frappe.throw(_("Decimal separator must be a dot or comma."))
		if self.decimal_separator == self.delimiter:
			frappe.throw(_("Decimal separator and field delimiter must differ."))
		for fieldname in (
			"money_precision",
			"tax_rate_precision",
			"exchange_rate_precision",
			"quantity_precision",
		):
			if not 0 <= int(self.get(fieldname)) <= 12:
				frappe.throw(_("BMD decimal precision must be between 0 and 12."))

		columns = [row.field_name.strip().lower() for row in self.columns]
		if len(columns) != len(set(columns)):
			frappe.throw(_("BMD export profile contains duplicate columns."))
		unknown = sorted(set(columns) - set(FIELD_REGISTRY))
		if unknown:
			frappe.throw(_("Unsupported BMD columns: {0}").format(", ".join(unknown)))
		missing = sorted(REQUIRED_COLUMNS - set(columns))
		if missing:
			frappe.throw(_("Required BMD columns are missing: {0}").format(", ".join(missing)))
		if columns[-1:] != ["text"]:
			frappe.throw(_("The BMD text column must be the last export column."))
		for row, field_name in zip(self.columns, columns, strict=True):
			row.field_name = field_name
