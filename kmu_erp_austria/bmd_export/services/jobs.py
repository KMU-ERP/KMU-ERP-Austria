from __future__ import annotations

import traceback

import frappe
from frappe import _
from frappe.utils.file_manager import save_file

from kmu_erp_austria.bmd_export.security import require_batch
from kmu_erp_austria.bmd_export.services.csv_renderer import render_csv
from kmu_erp_austria.bmd_export.services.exporter import (
	export_invoice,
	mapping_snapshot,
	settings_snapshot,
)
from kmu_erp_austria.bmd_export.services.fingerprint import canonical_json
from kmu_erp_austria.bmd_export.services.models import ZERO
from kmu_erp_austria.bmd_export.services.package import build_zip, sha256
from kmu_erp_austria.bmd_export.services.selection import select_invoices


def _error(exc: Exception) -> dict:
	return {
		"code": getattr(exc, "code", exc.__class__.__name__),
		"message": str(exc),
		"context": getattr(exc, "context", {}),
	}


def _settings(company: str):
	settings = frappe.get_doc("BMD Export Settings", company)
	if not settings.enabled:
		raise ValueError(_("BMD Export is disabled for {0}.").format(company))
	profile = frappe.get_doc("BMD Export Profile", settings.export_profile)
	if not profile.is_active:
		raise ValueError(_("BMD Export Profile {0} is inactive.").format(profile.name))
	return settings, profile


def _insert_item(values: dict):
	doc = frappe.get_doc({"doctype": "BMD Export Batch Item", **values})
	doc.flags.bmd_internal_update = True
	doc.insert(ignore_permissions=True)
	return doc


def _clear_items(batch_name: str) -> None:
	for name in frappe.get_all("BMD Export Batch Item", filters={"batch": batch_name}, pluck="name"):
		frappe.delete_doc("BMD Export Batch Item", name, ignore_permissions=True)


def _progress(batch, value: float) -> None:
	batch.db_set("progress", value, update_modified=False)
	frappe.publish_realtime(
		"bmd_export_progress",
		{"batch": batch.name, "progress": value, "status": batch.status},
		user=batch.requested_by,
		after_commit=False,
	)


def _notify_status(batch) -> None:
	frappe.publish_realtime(
		"bmd_export_progress",
		{"batch": batch.name, "progress": batch.progress, "status": batch.status},
		user=batch.requested_by,
		after_commit=True,
	)


def validate_batch(batch_name: str, *, allow_reexport: bool = False) -> dict:
	batch = frappe.get_doc("BMD Export Batch", batch_name)
	require_batch(batch)
	if batch.status not in {"Draft", "Invalid", "Ready", "Failed"}:
		frappe.throw(
			_("Batch {0} cannot be validated in status {1}.").format(batch.name, _(batch.status))
		)
	batch.transition("Validating", progress=0, error_message="")
	_clear_items(batch.name)
	try:
		settings, profile = _settings(batch.company)
		if allow_reexport and batch.supersedes:
			vouchers = [
				(row.voucher_type, row.voucher_name)
				for row in frappe.get_all(
					"BMD Export Batch Item",
					filters={"batch": batch.supersedes, "status": "Exported"},
					fields=["voucher_type", "voucher_name", "posting_date"],
					order_by="posting_date asc, voucher_type asc, voucher_name asc",
				)
			]
		else:
			vouchers = select_invoices(
				batch.company,
				batch.from_date,
				batch.to_date,
				bool(batch.include_sales_invoices),
				bool(batch.include_purchase_invoices),
				allow_reexport=allow_reexport,
			)
	except Exception as exc:
		errors = [_error(exc)]
		batch.validation_log = canonical_json(errors)
		batch.transition("Invalid", progress=100, error_message=str(exc))
		frappe.db.commit()
		return {"batch": batch.name, "status": batch.status, "errors": errors, "voucher_count": 0}
	used_names: set[str] = {settings.csv_filename.casefold()}
	used_mappings: set[str] = set()
	errors = []
	exports = []
	for index, (doctype, name) in enumerate(vouchers, start=1):
		try:
			export = export_invoice(doctype, name, settings, profile, used_names)
			exports.append(export)
			used_mappings.update(export.used_mappings)
			_insert_item(
				{
					"batch": batch.name,
					"company": batch.company,
					"voucher_type": doctype,
					"voucher_name": name,
					"posting_date": export.invoice.posting_date,
					"status": "Valid",
					"booking_line_count": sum(row.get("satzart") == 0 for row in export.rows),
					"document_line_count": sum(row.get("satzart") == 5 for row in export.rows),
					"net_total": export.net_total,
					"tax_total": export.tax_total,
					"gross_total": export.gross_total,
					"fingerprint": export.fingerprint,
					"document_hashes_json": canonical_json(
						[
							{
								"source_file": item.source_file,
								"export_name": item.export_name,
								"sha256": item.sha256,
							}
							for item in export.attachments
						]
					),
					"errors_json": "[]",
					"warnings_json": canonical_json(export.warnings),
				}
			)
		except Exception as exc:
			error = {"voucher_type": doctype, "voucher_name": name, **_error(exc)}
			errors.append(error)
			posting_date = frappe.db.get_value(doctype, name, "posting_date")
			_insert_item(
				{
					"batch": batch.name,
					"company": batch.company,
					"voucher_type": doctype,
					"voucher_name": name,
					"posting_date": posting_date,
					"status": "Invalid",
					"errors_json": canonical_json([error]),
					"warnings_json": "[]",
				}
			)
		_progress(batch, (index / max(len(vouchers), 1)) * 100)

	if not vouchers:
		errors.append(
			{"code": "NO_VOUCHERS", "message": _("No unexported invoices match the selection.")}
		)
	booking_line_count = sum(sum(row.get("satzart") == 0 for row in export.rows) for export in exports)
	if booking_line_count > int(settings.max_booking_rows):
		errors.append(
			{
				"code": "ROW_LIMIT_EXCEEDED",
				"message": _("The batch contains {0} Satzart 0 rows; maximum is {1}.").format(
					booking_line_count, settings.max_booking_rows
				),
			}
		)

	batch.settings_snapshot_json = canonical_json(settings_snapshot(settings, profile))
	batch.mapping_snapshot_json = canonical_json(mapping_snapshot(used_mappings))
	batch.validation_log = canonical_json(errors)
	batch.booking_line_count = booking_line_count
	batch.document_line_count = sum(
		sum(row.get("satzart") == 5 for row in export.rows) for export in exports
	)
	batch.document_count = sum(len(export.attachments) for export in exports)
	batch.net_total = sum((export.net_total for export in exports), ZERO)
	batch.tax_total = sum((export.tax_total for export in exports), ZERO)
	batch.gross_total = sum((export.gross_total for export in exports), ZERO)
	batch.sales_total = sum(
		(abs(export.gross_total) for export in exports if export.invoice.doctype == "Sales Invoice"), ZERO
	)
	batch.purchase_total = sum(
		(abs(export.gross_total) for export in exports if export.invoice.doctype == "Purchase Invoice"), ZERO
	)
	batch.transition("Invalid" if errors else "Ready", progress=100)
	frappe.db.commit()
	return {"batch": batch.name, "status": batch.status, "errors": errors, "voucher_count": len(vouchers)}


def enqueue_batch(batch_name: str) -> None:
	batch = frappe.get_doc("BMD Export Batch", batch_name)
	require_batch(batch)
	if batch.status != "Ready":
		frappe.throw(_("Batch {0} must be Ready before generation.").format(batch.name))
	batch.transition("Generating", progress=0, error_message="")
	frappe.enqueue(
		"kmu_erp_austria.bmd_export.services.jobs.generate_batch",
		queue="long",
		timeout=3600,
		enqueue_after_commit=True,
		job_id=f"bmd-export-{batch.name}",
		deduplicate=True,
		batch_name=batch.name,
	)


def _current_exports(batch, settings, profile):
	items = frappe.get_all(
		"BMD Export Batch Item",
		filters={"batch": batch.name, "status": "Valid"},
		fields=["name", "voucher_type", "voucher_name", "fingerprint"],
		order_by="posting_date asc, voucher_type asc, voucher_name asc",
		limit_page_length=0,
	)
	used_names: set[str] = {settings.csv_filename.casefold()}
	result = []
	for index, item in enumerate(items, start=1):
		export = export_invoice(item.voucher_type, item.voucher_name, settings, profile, used_names)
		if export.fingerprint != item.fingerprint:
			raise ValueError(
				_("Preview fingerprint changed for {0} {1}; validate again.").format(
					_(item.voucher_type), item.voucher_name
				)
			)
		result.append((item, export))
		_progress(batch, (index / max(len(items), 1)) * 80)
	return result


def generate_batch(batch_name: str) -> None:
	batch = frappe.get_doc("BMD Export Batch", batch_name)
	request_user = batch.requested_by
	original_user = frappe.session.user
	lock = frappe.cache.lock(f"bmd-export:{batch.name}", timeout=3700, blocking_timeout=1)
	acquired = False
	try:
		acquired = lock.acquire(blocking=True)
		if not acquired:
			raise RuntimeError(_("BMD batch {0} is already being generated.").format(batch.name))
		frappe.set_user(request_user)
		batch = frappe.get_doc("BMD Export Batch", batch_name)
		require_batch(batch)
		if batch.status != "Generating":
			raise ValueError(_("Batch {0} is not in Generating status.").format(batch.name))
		settings, profile = _settings(batch.company)
		exports = _current_exports(batch, settings, profile)
		rows = [row for _item, export in exports for row in export.rows]
		attachments = [attachment for _item, export in exports for attachment in export.attachments]
		csv_content = render_csv(rows, profile)
		zip_content = build_zip(settings.csv_filename, csv_content, attachments)
		csv_file = save_file(settings.csv_filename, csv_content, batch.doctype, batch.name, is_private=1)
		zip_file = save_file(f"{batch.name}.zip", zip_content, batch.doctype, batch.name, is_private=1)

		for item, _export in exports:
			item_doc = frappe.get_doc("BMD Export Batch Item", item.name)
			item_doc.status = "Exported"
			item_doc.flags.bmd_internal_update = True
			item_doc.save(ignore_permissions=True)
		batch.csv_file = csv_file.file_url
		batch.zip_file = zip_file.file_url
		batch.csv_sha256 = sha256(csv_content)
		batch.zip_sha256 = sha256(zip_content)
		batch.transition("Completed", progress=100)
		_notify_status(batch)
		if batch.supersedes:
			old_batch = frappe.get_doc("BMD Export Batch", batch.supersedes)
			if old_batch.status == "Completed":
				old_batch.transition("Superseded")
		frappe.db.commit()
	except Exception as exc:
		frappe.db.rollback()
		try:
			batch = frappe.get_doc("BMD Export Batch", batch_name)
			if batch.status == "Generating":
				batch.transition("Failed", error_message=str(exc), validation_log=canonical_json([_error(exc)]))
				_notify_status(batch)
				frappe.db.commit()
		except Exception:
			frappe.log_error(traceback.format_exc(), f"BMD export batch {batch_name} failure")
		raise
	finally:
		frappe.set_user(original_user)
		if acquired:
			lock.release()
