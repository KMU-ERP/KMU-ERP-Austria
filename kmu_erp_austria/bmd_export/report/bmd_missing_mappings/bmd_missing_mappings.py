from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_months, getdate, nowdate

from kmu_erp_austria.bmd_export.security import require_company, require_export_role
from kmu_erp_austria.bmd_export.services.mapping import MappingResolutionError, MappingResolver
from kmu_erp_austria.bmd_export.services.normalization import load_invoice
from kmu_erp_austria.bmd_export.services.selection import select_invoices
from kmu_erp_austria.bmd_export.services.transform import TransformError, build_booking_lines


def execute(filters=None):
	filters = frappe._dict(filters or {})
	require_export_role()
	require_company(filters.company)
	from_date = getdate(filters.from_date or add_months(nowdate(), -1))
	to_date = getdate(filters.to_date or nowdate())
	settings = frappe.get_doc("BMD Export Settings", filters.company)
	include_sales = filters.voucher_type in {None, "", "Sales Invoice"}
	include_purchase = filters.voucher_type in {None, "", "Purchase Invoice"}
	rows = []
	for doctype, name in select_invoices(
		filters.company,
		from_date,
		to_date,
		include_sales,
		include_purchase,
		allow_reexport=True,
	):
		try:
			invoice = load_invoice(doctype, name)
			resolver = MappingResolver(invoice.company, invoice.posting_date)
			build_booking_lines(invoice, settings, resolver)
		except (MappingResolutionError, TransformError) as exc:
			rows.append(
				{
					"voucher_type": doctype,
					"voucher_name": name,
					"posting_date": frappe.db.get_value(doctype, name, "posting_date"),
					"error_code": exc.code,
					"message": str(exc),
					"context": json.dumps(exc.context, ensure_ascii=False, default=str),
				}
			)
	return _columns(), rows


def _columns():
	return [
		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 140},
		{
			"fieldname": "voucher_name",
			"label": _("Voucher"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180,
		},
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "error_code", "label": _("Error Code"), "fieldtype": "Data", "width": 180},
		{"fieldname": "message", "label": _("Message"), "fieldtype": "Data", "width": 320},
		{"fieldname": "context", "label": _("Context"), "fieldtype": "Data", "width": 320},
	]
