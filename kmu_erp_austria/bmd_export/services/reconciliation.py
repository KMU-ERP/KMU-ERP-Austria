from __future__ import annotations

from decimal import Decimal

import frappe
from frappe import _

from kmu_erp_austria.bmd_export.services.models import BookingLine, NormalizedInvoice, ZERO
from kmu_erp_austria.bmd_export.services.transform import CENT, TransformError, money


def reconcile_invoice(invoice: NormalizedInvoice, lines: list[BookingLine]) -> None:
	if not lines:
		raise TransformError("EMPTY_INVOICE", _("Invoice produced no Satzart 0 rows."))
	expected_gross = money(abs(invoice.base_grand_total) * invoice.amount_sign)
	actual_gross = sum((line.gross_amount for line in lines), ZERO)
	if money(actual_gross) != expected_gross:
		raise TransformError(
			"INVOICE_RECONCILIATION_FAILED",
			_("BMD gross {0} does not match invoice gross {1}.").format(
				actual_gross, expected_gross
			),
		)
	for line in lines:
		kore_total = sum(
			(Decimal(str(row.get("kobetrag") or 0)) for row in line.kore_rows), ZERO
		)
		if line.kore_rows and money(kore_total) != money(line.net_amount):
			raise TransformError(
				"KORE_RECONCILIATION_FAILED",
				_("Satzart 1 amounts do not equal the preceding booking line net amount."),
			)


def reconcile_gl(invoice: NormalizedInvoice) -> None:
	rows = frappe.get_all(
		"GL Entry",
		filters={
			"voucher_type": invoice.doctype,
			"voucher_no": invoice.name,
			"account": invoice.control_account,
			"is_cancelled": 0,
		},
		fields=["debit", "credit"],
	)
	if not rows:
		raise TransformError(
			"GL_RECONCILIATION_FAILED",
			_("No control-account GL Entry exists for {0} {1}.").format(
				_(invoice.doctype), invoice.name
			),
		)
	actual = money(
		sum((Decimal(str(row.debit or 0)) - Decimal(str(row.credit or 0)) for row in rows), ZERO)
	)
	expected = money(abs(invoice.base_grand_total) * invoice.amount_sign)
	if actual != expected:
		raise TransformError(
			"GL_RECONCILIATION_FAILED",
			_("Control-account GL amount {0} does not match invoice amount {1}.").format(
				actual, expected
			),
		)
