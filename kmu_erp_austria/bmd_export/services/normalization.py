from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate

from kmu_erp_austria.bmd_export.services.models import (
	NormalizedInvoice,
	NormalizedItem,
	NormalizedTax,
)


def decimal_value(value) -> Decimal:
	return Decimal(str(value or 0))


def _address_country(address_name: str | None) -> str | None:
	if not address_name:
		return None
	return frappe.db.get_value("Address", address_name, "country")


def load_invoice(doctype: str, name: str, *, check_permissions: bool = True) -> NormalizedInvoice:
	if doctype not in {"Sales Invoice", "Purchase Invoice"}:
		raise ValueError(_("Unsupported voucher type {0}.").format(repr(doctype)))
	doc = frappe.get_doc(doctype, name)
	if check_permissions and not doc.has_permission("read"):
		raise frappe.PermissionError
	if doc.docstatus != 1:
		raise ValueError(_("{0} {1} is not submitted.").format(_(doctype), name))

	is_sales = doctype == "Sales Invoice"
	party_type = "Customer" if is_sales else "Supplier"
	party = doc.customer if is_sales else doc.supplier
	party_name = doc.customer_name if is_sales else doc.supplier_name
	address = doc.get("customer_address") if is_sales else doc.get("supplier_address")
	company_currency = frappe.get_cached_value("Company", doc.company, "default_currency")
	conversion_rate = decimal_value(doc.conversion_rate or 1)
	if conversion_rate <= 0:
		raise ValueError(_("{0} {1} has an invalid conversion rate.").format(_(doctype), name))

	tax_rows = {row.name: row for row in doc.get("taxes") or []}
	item_rows = {row.name for row in doc.items}
	accounting_dimension_fields = frappe.get_all(
		"Accounting Dimension", filters={"disabled": 0}, pluck="fieldname"
	)
	taxes_by_item: dict[str, list[NormalizedTax]] = defaultdict(list)
	for detail in doc.get("item_wise_tax_details") or []:
		tax_row = tax_rows.get(detail.tax_row)
		if detail.item_row not in item_rows or not tax_row:
			raise ValueError(
				_("{0} {1} contains an invalid item-wise tax reference ({2}, {3}).").format(
					_(doctype), name, repr(detail.item_row), repr(detail.tax_row)
				)
			)
		taxes_by_item[detail.item_row].append(
			NormalizedTax(
				tax_row=detail.tax_row,
				account=tax_row.account_head,
				rate=decimal_value(detail.rate),
				amount=decimal_value(detail.amount),
				taxable_amount=decimal_value(detail.taxable_amount),
			)
		)

	items = []
	for row in doc.items:
		account = row.income_account if is_sales else row.expense_account
		if not account:
			raise ValueError(
				_("Invoice item {0} has no {1} account.").format(
					row.idx, _("income") if is_sales else _("expense")
				)
			)
		items.append(
			NormalizedItem(
				row_name=row.name,
				item_code=row.item_code,
				item_group=row.get("item_group")
				or (frappe.get_cached_value("Item", row.item_code, "item_group") if row.item_code else None),
				account=account,
				net_amount=decimal_value(row.net_amount),
				base_net_amount=decimal_value(row.base_net_amount),
				cost_center=row.cost_center,
				project=row.project,
				description=(row.description or row.item_name or row.item_code or doc.name).strip(),
				taxes=tuple(taxes_by_item.get(row.name, [])),
				accounting_dimensions=tuple(
					(fieldname, row.get(fieldname))
					for fieldname in accounting_dimension_fields
					if row.get(fieldname)
				),
			)
		)

	belegdatum: date = getdate(doc.posting_date)
	if not is_sales and doc.get("bill_date"):
		belegdatum = getdate(doc.bill_date)
	return NormalizedInvoice(
		doctype=doctype,
		name=doc.name,
		company=doc.company,
		posting_date=getdate(doc.posting_date),
		belegdatum=belegdatum,
		party_type=party_type,
		party=party,
		party_name=party_name or party,
		control_account=doc.debit_to if is_sales else doc.credit_to,
		country=_address_country(address),
		tax_category=doc.get("tax_category"),
		currency=doc.currency,
		company_currency=company_currency,
		conversion_rate=conversion_rate,
		base_net_total=decimal_value(doc.base_net_total),
		base_grand_total=decimal_value(doc.base_grand_total),
		grand_total=decimal_value(doc.grand_total),
		is_return=bool(doc.is_return),
		return_against=doc.return_against,
		return_against_posting_date=(
			getdate(frappe.db.get_value(doctype, doc.return_against, "posting_date"))
			if doc.return_against
			else None
		),
		bill_no=doc.get("bill_no"),
		modified=str(doc.modified),
		remarks=(doc.remarks or doc.name).strip(),
		items=tuple(items),
	)
