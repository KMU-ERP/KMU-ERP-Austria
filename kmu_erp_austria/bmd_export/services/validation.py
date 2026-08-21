from __future__ import annotations

from datetime import date

import frappe
from frappe import _
from frappe.utils import getdate


def validate_date_range(valid_from: date | None, valid_to: date | None) -> None:
	if valid_from and valid_to and valid_from > valid_to:
		frappe.throw(_("Valid From must not be later than Valid To."))


def validate_account_number(value: str, label: str = "BMD account") -> str:
	value = (value or "").strip()
	if not value or len(value) > 10 or not value.isdigit():
		frappe.throw(_("{0} must contain 1 to 10 digits.").format(label))
	return value


def validate_link_company(doctype: str, name: str | None, company: str, field_label: str) -> None:
	if not name:
		return
	linked_company = frappe.db.get_value(doctype, name, "company")
	if linked_company and linked_company != company:
		frappe.throw(_("{0} belongs to another company.").format(field_label))


def overlapping_mapping_exists(doc, identifying_filters: dict) -> bool:
	filters = {
		"name": ["!=", doc.name or ""],
		"company": doc.company,
		"active": 1,
		"priority": doc.priority or 0,
		**identifying_filters,
	}
	for row in frappe.get_all(doc.doctype, filters=filters, fields=["valid_from", "valid_to"]):
		left_start = getdate(doc.valid_from) if doc.valid_from else date.min
		left_end = getdate(doc.valid_to) if doc.valid_to else date.max
		right_start = getdate(row.valid_from) if row.valid_from else date.min
		right_end = getdate(row.valid_to) if row.valid_to else date.max
		if left_start <= right_end and right_start <= left_end:
			return True
	return False
