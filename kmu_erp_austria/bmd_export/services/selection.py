from __future__ import annotations

from datetime import date

import frappe


SUPPORTED_VOUCHERS = ("Sales Invoice", "Purchase Invoice")


def completed_vouchers(company: str) -> set[tuple[str, str]]:
	batches = frappe.get_all(
		"BMD Export Batch",
		filters={"company": company, "status": ["in", ["Completed", "Superseded"]]},
		pluck="name",
	)
	if not batches:
		return set()
	return {
		(row.voucher_type, row.voucher_name)
		for row in frappe.get_all(
			"BMD Export Batch Item",
			filters={"batch": ["in", batches], "status": "Exported"},
			fields=["voucher_type", "voucher_name"],
			limit_page_length=0,
		)
	}


def select_invoices(
	company: str,
	from_date: date,
	to_date: date,
	include_sales: bool = True,
	include_purchase: bool = True,
	allow_reexport: bool = False,
) -> list[tuple[str, str]]:
	voucher_types = []
	if include_sales:
		voucher_types.append("Sales Invoice")
	if include_purchase:
		voucher_types.append("Purchase Invoice")
	already_exported = set() if allow_reexport else completed_vouchers(company)
	result = []
	for doctype in voucher_types:
		for row in frappe.get_list(
			doctype,
			filters={
				"company": company,
				"docstatus": 1,
				"posting_date": ["between", [from_date, to_date]],
			},
			fields=["name", "posting_date"],
			order_by="posting_date asc, name asc",
			limit_page_length=0,
		):
			key = (doctype, row.name)
			if key not in already_exported:
				result.append((doctype, row.name))
	return sorted(
		result,
		key=lambda item: (
			frappe.db.get_value(item[0], item[1], "posting_date"),
			item[0],
			item[1],
		),
	)
