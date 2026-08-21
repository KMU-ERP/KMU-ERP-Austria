from __future__ import annotations

import hashlib
import mimetypes
from pathlib import PurePath

import frappe
from frappe import _

from kmu_erp_austria.bmd_export.services.models import AttachmentPayload, NormalizedInvoice
from kmu_erp_austria.bmd_export.services.naming import (
	render_filename_stem,
	safe_extension,
	unique_export_filename,
)


class DocumentValidationError(ValueError):
	def __init__(self, code: str, message: str, context: dict | None = None):
		super().__init__(message)
		self.code = code
		self.context = context or {}


def _as_bytes(content) -> bytes:
	if isinstance(content, bytes):
		return content
	if isinstance(content, str):
		return content.encode("utf-8")
	return bytes(content)


def _detected_mime(content: bytes, filename: str) -> str:
	if content.startswith(b"%PDF-"):
		return "application/pdf"
	if content.startswith(b"\xff\xd8\xff"):
		return "image/jpeg"
	if content.startswith(b"\x89PNG\r\n\x1a\n"):
		return "image/png"
	return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _extension_matches_mime(extension: str, mime_type: str) -> bool:
	expected = {
		"pdf": {"application/pdf"},
		"jpg": {"image/jpeg"},
		"jpeg": {"image/jpeg"},
		"png": {"image/png"},
	}.get(extension.lstrip(".").lower())
	return not expected or mime_type.lower() in expected


def _source_attachments(invoice: NormalizedInvoice):
	rows = frappe.get_list(
		"File",
		filters={
			"attached_to_doctype": invoice.doctype,
			"attached_to_name": invoice.name,
			"is_folder": 0,
		},
		fields=["name", "file_name", "file_url", "file_size", "is_private", "creation"],
		order_by="creation asc, name asc",
		limit_page_length=0,
	)
	return [frappe.get_doc("File", row.name) for row in rows]


def _generated_pdf(invoice: NormalizedInvoice, settings) -> tuple[str, bytes, str]:
	try:
		content = frappe.get_print(
			invoice.doctype,
			invoice.name,
			print_format=settings.sales_invoice_print_format or None,
			as_pdf=True,
		)
	except Exception as exc:
		raise DocumentValidationError(
			"PDF_GENERATION_FAILED",
			_("Unable to generate the Sales Invoice PDF: {0}").format(exc),
		) from exc
	return f"{invoice.name}.pdf", _as_bytes(content), "Generated Sales Invoice PDF"


def _invoice_number(invoice: NormalizedInvoice, settings) -> str:
	if (
		invoice.doctype == "Purchase Invoice"
		and settings.purchase_belegnr_source == "Supplier Invoice Number"
	):
		return invoice.bill_no or invoice.name
	return invoice.name


def _context(
	invoice: NormalizedInvoice,
	settings,
	original_filename: str,
	attachment_no: int,
	extension: str,
) -> dict:
	return {
		"company": invoice.company,
		"voucher_type": invoice.doctype,
		"voucher_type_code": invoice.voucher_type_code,
		"voucher_name": invoice.name,
		"invoice_number": _invoice_number(invoice, settings),
		"external_invoice_number": invoice.bill_no or "",
		"bill_no": invoice.bill_no or "",
		"posting_date_yyyymmdd": invoice.posting_date.strftime("%Y%m%d"),
		"party": invoice.party,
		"party_name": invoice.party_name,
		"return_against": invoice.return_against or "",
		"attachment_no": attachment_no,
		"original_stem": PurePath(original_filename).stem,
		"extension": extension.lstrip(".").lower(),
	}


def collect_attachments(
	invoice: NormalizedInvoice,
	settings,
	encoding: str,
	delimiter: str,
	used_names: set[str],
) -> list[AttachmentPayload]:
	sources: list[tuple[str, bytes, str]] = []
	for file_doc in _source_attachments(invoice):
		if not file_doc.has_permission("read"):
			raise frappe.PermissionError
		try:
			content = _as_bytes(file_doc.get_content(encodings=[]))
		except Exception as exc:
			raise DocumentValidationError(
				"ATTACHMENT_UNREADABLE",
				_("Unable to read attachment {0}: {1}").format(file_doc.file_name, exc),
				{"file": file_doc.name},
			) from exc
		sources.append((file_doc.file_name, content, file_doc.name))

	if not sources and invoice.doctype == "Sales Invoice" and settings.generate_sales_invoice_pdf:
		sources.append(_generated_pdf(invoice, settings))

	required = (
		settings.require_sales_attachment
		if invoice.doctype == "Sales Invoice"
		else settings.require_purchase_attachment
	)
	if required and not sources:
		raise DocumentValidationError(
			"ATTACHMENT_REQUIRED",
			_("{0} {1} requires an attachment.").format(_(invoice.doctype), invoice.name),
		)

	allowed_extensions = settings.normalized_extensions
	allowed_mime_types = settings.normalized_mime_types
	max_size = int(settings.max_file_size_mb) * 1024 * 1024
	result: list[AttachmentPayload] = []
	for attachment_no, (original_filename, content, source_file) in enumerate(sources, start=1):
		if not content:
			raise DocumentValidationError(
				"ATTACHMENT_EMPTY", _("Attachment {0} is empty.").format(original_filename)
			)
		if len(content) > max_size:
			raise DocumentValidationError(
				"ATTACHMENT_TOO_LARGE",
				_("Attachment {0} exceeds {1} MB.").format(
					original_filename, settings.max_file_size_mb
				),
			)
		extension = safe_extension(original_filename)
		if extension.lstrip(".").lower() not in allowed_extensions:
			raise DocumentValidationError(
				"ATTACHMENT_EXTENSION_NOT_ALLOWED",
				_("Attachment extension {0} is not allowed.").format(extension),
			)
		mime_type = _detected_mime(content, original_filename)
		if mime_type.lower() not in allowed_mime_types:
			raise DocumentValidationError(
				"ATTACHMENT_MIME_NOT_ALLOWED",
				_("Attachment MIME type {0} is not allowed.").format(mime_type),
			)
		if not _extension_matches_mime(extension, mime_type):
			raise DocumentValidationError(
				"ATTACHMENT_MIME_MISMATCH",
				_("Attachment extension {0} does not match MIME type {1}.").format(
					extension, mime_type
				),
			)
		stem = render_filename_stem(
			settings.document_filename_template,
			_context(invoice, settings, original_filename, attachment_no, extension),
		)
		active_delimiter = "\t" if delimiter == "\\t" else delimiter
		stem = stem.replace(active_delimiter, "-")
		export_name = unique_export_filename(stem, extension, used_names, encoding)
		result.append(
			AttachmentPayload(
				export_name=export_name,
				content=content,
				sha256=hashlib.sha256(content).hexdigest(),
				source_file=source_file,
				mime_type=mime_type,
			)
		)
	return result
