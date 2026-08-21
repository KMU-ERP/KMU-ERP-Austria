from __future__ import annotations

import frappe
from frappe import _

from kmu_erp_austria.bmd_export.services.documents import collect_attachments
from kmu_erp_austria.bmd_export.services.fingerprint import clean_doc, make_fingerprint
from kmu_erp_austria.bmd_export.services.mapping import MappingResolver
from kmu_erp_austria.bmd_export.services.models import InvoiceExport, ZERO
from kmu_erp_austria.bmd_export.services.normalization import load_invoice
from kmu_erp_austria.bmd_export.services.reconciliation import reconcile_gl, reconcile_invoice
from kmu_erp_austria.bmd_export.services.transform import build_booking_lines, serialize_booking_lines


MAPPING_DOCTYPES = (
	"BMD Account",
	"BMD Account Mapping",
	"BMD Party Mapping",
	"BMD Tax Mapping",
	"BMD Dimension Mapping",
)


def settings_snapshot(settings, profile) -> dict:
	return {"settings": clean_doc(settings), "profile": clean_doc(profile)}


def mapping_snapshot(names: set[str]) -> list[dict]:
	result = []
	for doctype in MAPPING_DOCTYPES:
		for name in sorted(names):
			if frappe.db.exists(doctype, name):
				result.append({"doctype": doctype, **clean_doc(frappe.get_doc(doctype, name))})
	return sorted(result, key=lambda row: (row["doctype"], row.get("name", "")))


def export_invoice(
	doctype: str,
	name: str,
	settings,
	profile,
	used_document_names: set[str],
	*,
	check_permissions: bool = True,
) -> InvoiceExport:
	invoice = load_invoice(doctype, name, check_permissions=check_permissions)
	if invoice.company != settings.company:
		raise ValueError(_("{0} {1} belongs to another company.").format(_(doctype), name))
	resolver = MappingResolver(invoice.company, invoice.posting_date)
	lines = build_booking_lines(invoice, settings, resolver)
	reconcile_invoice(invoice, lines)
	reconcile_gl(invoice)
	working_document_names = set(used_document_names)
	attachments = collect_attachments(
		invoice,
		settings,
		profile.encoding,
		profile.delimiter,
		working_document_names,
	)
	rows = serialize_booking_lines(lines, [attachment.export_name for attachment in attachments])
	mappings = mapping_snapshot(resolver.used)
	documents = [
		{
			"source_file": attachment.source_file,
			"export_name": attachment.export_name,
			"sha256": attachment.sha256,
			"mime_type": attachment.mime_type,
		}
		for attachment in attachments
	]
	fingerprint = make_fingerprint(invoice, settings_snapshot(settings, profile), mappings, documents)
	used_document_names.update(working_document_names)
	return InvoiceExport(
		invoice=invoice,
		rows=rows,
		attachments=attachments,
		used_mappings=set(resolver.used),
		net_total=sum((line.net_amount for line in lines), ZERO),
		tax_total=sum((line.tax_amount for line in lines), ZERO),
		gross_total=sum((line.gross_amount for line in lines), ZERO),
		fingerprint=fingerprint,
	)
