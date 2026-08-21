from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import get_datetime, now_datetime

from kmu_erp_austria.bmd_export.services.fingerprint import canonical_json


def cleanup_expired_artifacts() -> None:
	"""Delete only expired private artifacts while retaining hashes and an audit log."""
	for batch in frappe.get_all(
		"BMD Export Batch",
		filters={"status": ["in", ["Completed", "Superseded"]]},
		fields=["name", "company", "completed_at", "csv_file", "zip_file", "retention_log"],
		limit_page_length=0,
	):
		if not batch.completed_at or (not batch.csv_file and not batch.zip_file):
			continue
		retention_days = frappe.db.get_value("BMD Export Settings", batch.company, "retention_days")
		if not retention_days:
			continue
		if get_datetime(batch.completed_at) + timedelta(days=int(retention_days)) > now_datetime():
			continue
		deleted = []
		for fieldname in ("csv_file", "zip_file"):
			file_url = batch.get(fieldname)
			if not file_url:
				continue
			file_name = frappe.db.get_value(
				"File",
				{
					"file_url": file_url,
					"attached_to_doctype": "BMD Export Batch",
					"attached_to_name": batch.name,
					"is_private": 1,
				},
				"name",
			)
			if file_name:
				frappe.delete_doc("File", file_name, ignore_permissions=True)
				deleted.append({"field": fieldname, "file": file_name, "file_url": file_url})
		if deleted:
			log = frappe.parse_json(batch.retention_log) if batch.retention_log else []
			log.append({"deleted_at": str(now_datetime()), "artifacts": deleted})
			frappe.db.set_value(
				"BMD Export Batch",
				batch.name,
				{"csv_file": None, "zip_file": None, "retention_log": canonical_json(log)},
				update_modified=False,
			)
	frappe.db.commit()
