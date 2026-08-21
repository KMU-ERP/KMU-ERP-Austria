from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from kmu_erp_austria.bmd_export.security import (
	require_batch,
	require_company,
	require_export_role,
	require_manager_role,
)
from kmu_erp_austria.bmd_export.services.jobs import enqueue_batch, validate_batch
from kmu_erp_austria.bmd_export.services.naming import (
	render_filename_stem,
	safe_extension,
	unique_export_filename,
)
from kmu_erp_austria.bmd_export.services.account_import import (
	import_accounts as import_account_rows,
	preview_accounts,
)


@frappe.whitelist()
def create_preview(
	company: str,
	from_date: str,
	to_date: str,
	include_sales_invoices: int | str = 1,
	include_purchase_invoices: int | str = 1,
) -> dict:
	require_export_role()
	require_company(company)
	batch = frappe.get_doc(
		{
			"doctype": "BMD Export Batch",
			"company": company,
			"from_date": getdate(from_date),
			"to_date": getdate(to_date),
			"include_sales_invoices": int(include_sales_invoices),
			"include_purchase_invoices": int(include_purchase_invoices),
		}
	).insert()
	return validate_batch(batch.name)


@frappe.whitelist()
def refresh_preview(batch_name: str) -> dict:
	batch = frappe.get_doc("BMD Export Batch", batch_name)
	require_batch(batch)
	return validate_batch(batch.name, allow_reexport=bool(batch.supersedes))


@frappe.whitelist()
def start_export(batch_name: str) -> dict:
	batch = frappe.get_doc("BMD Export Batch", batch_name)
	require_batch(batch)
	enqueue_batch(batch.name)
	return {"batch": batch.name, "status": "Generating"}


@frappe.whitelist()
def create_reexport(batch_name: str) -> dict:
	require_manager_role()
	old = frappe.get_doc("BMD Export Batch", batch_name)
	require_batch(old)
	if old.status not in {"Completed", "Superseded"}:
		frappe.throw(_("Only completed BMD batches can be re-exported."))
	batch = frappe.get_doc(
		{
			"doctype": "BMD Export Batch",
			"company": old.company,
			"from_date": old.from_date,
			"to_date": old.to_date,
			"include_sales_invoices": old.include_sales_invoices,
			"include_purchase_invoices": old.include_purchase_invoices,
			"revision": int(old.revision or 1) + 1,
			"supersedes": old.name,
		}
	)
	batch.flags.bmd_internal_reexport = True
	batch.insert()
	return validate_batch(batch.name, allow_reexport=True)


@frappe.whitelist()
def preview_document_filename(
	template: str,
	original_filename: str = "test.pdf",
	context_json: str | None = None,
	encoding: str = "utf-8-sig",
) -> str:
	require_manager_role()
	context = frappe.parse_json(context_json) if context_json else {}
	context = {
		"company": "Muster GmbH",
		"voucher_type": "Sales Invoice",
		"voucher_type_code": "AR",
		"voucher_name": "AR-2026-0042",
		"invoice_number": "AR-2026-0042",
		"external_invoice_number": "",
		"bill_no": "",
		"posting_date_yyyymmdd": "20260821",
		"party": "CUST-0001",
		"party_name": "Musterkunde",
		"return_against": "",
		"attachment_no": 1,
		"original_stem": "test",
		"extension": "pdf",
		**context,
	}
	extension = safe_extension(original_filename)
	stem = render_filename_stem(template, context)
	return unique_export_filename(stem, extension.lower(), set(), encoding)


@frappe.whitelist()
def preview_account_import(company: str, file_url: str) -> list[dict]:
	require_manager_role()
	require_company(company)
	return preview_accounts(company, file_url)


@frappe.whitelist()
def import_accounts(company: str, file_url: str, source: str = "") -> dict:
	require_manager_role()
	require_company(company)
	return import_account_rows(company, file_url, source)
