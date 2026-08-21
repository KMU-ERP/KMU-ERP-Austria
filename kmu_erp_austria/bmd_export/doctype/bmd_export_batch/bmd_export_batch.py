from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, now_datetime


STATUS_TRANSITIONS = {
	"Draft": {"Validating"},
	"Validating": {"Invalid", "Ready", "Failed"},
	"Invalid": {"Validating"},
	"Ready": {"Validating", "Generating"},
	"Generating": {"Completed", "Failed"},
	"Failed": {"Validating", "Generating"},
	"Completed": {"Superseded"},
	"Superseded": set(),
}

IMMUTABLE_AFTER_COMPLETION = {
	"company",
	"from_date",
	"to_date",
	"include_sales_invoices",
	"include_purchase_invoices",
	"requested_by",
	"requested_at",
	"revision",
	"supersedes",
	"settings_snapshot_json",
	"mapping_snapshot_json",
	"csv_file",
	"zip_file",
	"csv_sha256",
	"zip_sha256",
	"sales_total",
	"purchase_total",
	"net_total",
	"tax_total",
	"gross_total",
	"booking_line_count",
	"document_line_count",
	"document_count",
	"validation_log",
	"error_message",
}


class BMDExportBatch(Document):
	def before_insert(self):
		self.status = "Draft"
		self.requested_by = frappe.session.user
		self.requested_at = now_datetime()
		if self.supersedes and not self.flags.bmd_internal_reexport:
			frappe.throw(_("Re-exports must be created through the BMD manager workflow."))
		self.revision = self.revision if self.flags.bmd_internal_reexport else 1

	def validate(self):
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw(_("From Date must not be later than To Date."))
		if not self.include_sales_invoices and not self.include_purchase_invoices:
			frappe.throw(_("Select at least one invoice type."))

		previous = None
		if not self.is_new():
			previous = frappe.db.get_value(
				self.doctype, self.name, ["status", *sorted(IMMUTABLE_AFTER_COMPLETION)], as_dict=True
			)
		if previous and previous.status != self.status:
			if not self.flags.bmd_internal_transition:
				frappe.throw(_("BMD batch status can only be changed by the export workflow."))
			allowed = STATUS_TRANSITIONS.get(previous.status, set())
			if self.status not in allowed:
				frappe.throw(
					_("Invalid BMD batch status transition from {0} to {1}.").format(
						previous.status, self.status
					)
				)
		if previous and previous.status in {"Completed", "Superseded"}:
			for fieldname in IMMUTABLE_AFTER_COMPLETION:
				if self.get(fieldname) != previous.get(fieldname):
					frappe.throw(_("Completed BMD export batches are immutable."))

		for fieldname in (
			"settings_snapshot_json",
			"mapping_snapshot_json",
			"validation_log",
			"retention_log",
		):
			value = self.get(fieldname)
			if value:
				try:
					json.loads(value)
				except (TypeError, json.JSONDecodeError):
					frappe.throw(_("{0} must contain valid JSON.").format(self.meta.get_label(fieldname)))

	def transition(self, status: str, **values):
		if status not in STATUS_TRANSITIONS:
			frappe.throw(_("Unknown BMD export status {0}.").format(status))
		self.status = status
		self.update(values)
		if status == "Generating" and not self.started_at:
			self.started_at = now()
		if status == "Completed":
			self.completed_at = now()
			self.progress = 100
		self.flags.bmd_internal_transition = True
		try:
			self.save()
		finally:
			self.flags.bmd_internal_transition = False

	def on_trash(self):
		if self.status in {"Completed", "Superseded"}:
			frappe.throw(_("Completed BMD export batches cannot be deleted."))
