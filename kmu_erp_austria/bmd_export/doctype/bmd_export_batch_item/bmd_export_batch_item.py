from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class BMDExportBatchItem(Document):
	def validate(self):
		batch_company = frappe.db.get_value("BMD Export Batch", self.batch, "company")
		if batch_company and batch_company != self.company:
			frappe.throw(_("Batch item company must match the export batch."))
		if not self.is_new():
			batch_status = frappe.db.get_value("BMD Export Batch", self.batch, "status")
			if batch_status in {"Completed", "Superseded"} and not self.flags.bmd_internal_update:
				frappe.throw(_("Items of completed BMD export batches are immutable."))

	def on_trash(self):
		if frappe.db.get_value("BMD Export Batch", self.batch, "status") in {"Completed", "Superseded"}:
			frappe.throw(_("Items of completed BMD export batches cannot be deleted."))
