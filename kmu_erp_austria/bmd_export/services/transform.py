from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from frappe import _

from kmu_erp_austria.bmd_export.services.models import (
	BookingLine,
	NormalizedInvoice,
	NormalizedItem,
	NormalizedTax,
	ZERO,
)


CENT = Decimal("0.01")
EU_COUNTRIES = {
	"Austria",
	"Belgium",
	"Bulgaria",
	"Croatia",
	"Cyprus",
	"Czech Republic",
	"Denmark",
	"Estonia",
	"Finland",
	"France",
	"Germany",
	"Greece",
	"Hungary",
	"Ireland",
	"Italy",
	"Latvia",
	"Lithuania",
	"Luxembourg",
	"Malta",
	"Netherlands",
	"Poland",
	"Portugal",
	"Romania",
	"Slovakia",
	"Slovenia",
	"Spain",
	"Sweden",
}


class TransformError(ValueError):
	def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
		super().__init__(message)
		self.code = code
		self.context = context or {}


def money(value: Decimal) -> Decimal:
	return value.quantize(CENT, rounding=ROUND_HALF_UP)


def country_group(country: str | None, company_country: str | None = "Austria") -> str | None:
	if not country:
		return None
	if company_country and country == company_country:
		return "Domestic"
	return "EU" if country in EU_COUNTRIES else "Third Country"


def _tax_amount(mapping, tax: NormalizedTax, net: Decimal) -> Decimal:
	source = mapping.amount_source
	if source == "ERP Item Tax Detail":
		return abs(tax.amount)
	if source == "Net Amount x Rate":
		return abs(net) * abs(tax.rate) / Decimal("100")
	if source == "Zero":
		return ZERO
	raise TransformError(
		"INVALID_TAX_MAPPING", _("Unsupported tax amount source {0}.").format(repr(source))
	)


def _tax_sign(mapping, amount_sign: Decimal) -> Decimal:
	if mapping.sign_rule in {"Standard Output Tax", "Standard Input Tax"}:
		return -amount_sign
	if mapping.sign_rule == "Output-side Tax":
		return amount_sign
	if mapping.sign_rule == "Zero":
		return ZERO
	raise TransformError(
		"INVALID_TAX_MAPPING", _("Unsupported tax sign rule {0}.").format(repr(mapping.sign_rule))
	)


@dataclass(slots=True)
class _Group:
	account: str
	rate: Decimal
	tax_code: str
	sign_rule: str
	dimensions: dict[str, str]
	branch: str
	oss_target_country: str
	oss_schema: str
	oss_uid: str
	net: Decimal = ZERO
	foreign_net: Decimal = ZERO
	included_tax: Decimal = ZERO
	foreign_included_tax: Decimal = ZERO
	bmd_tax: Decimal = ZERO
	foreign_bmd_tax: Decimal = ZERO
	descriptions: list[str] = field(default_factory=list)


def _group_key(group: _Group) -> tuple:
	return (
		group.account,
		str(group.rate),
		group.tax_code,
		group.sign_rule,
		tuple(sorted(group.dimensions.items())),
		group.branch,
		group.oss_target_country,
		group.oss_schema,
		group.oss_uid,
	)


def _mapped_tax_components(invoice: NormalizedInvoice, item: NormalizedItem, resolver):
	taxes = item.taxes or (
		NormalizedTax(tax_row="", account=None, rate=ZERO, amount=ZERO, taxable_amount=abs(item.base_net_amount)),
	)
	components = []
	for tax in taxes:
		mapping = resolver.tax(
			transaction_type=invoice.transaction_type,
			rate=abs(tax.rate),
			tax_category=invoice.tax_category,
			country=invoice.country,
			erp_tax_account=tax.account,
			country_group=country_group(invoice.country),
		)
		components.append((tax, mapping, _tax_amount(mapping, tax, item.base_net_amount)))
	exported = [component for component in components if component[1].export_tax]
	if len(exported) != 1:
		raise TransformError(
			"AMBIGUOUS_TAX_COMPONENT",
			_("Every invoice item must resolve to exactly one BMD tax component."),
			{"item_row": item.row_name, "exported_components": len(exported)},
		)
	return components, exported[0]


def _belegnr(invoice: NormalizedInvoice, settings) -> str:
	if (
		invoice.doctype == "Purchase Invoice"
		and settings.purchase_belegnr_source == "Supplier Invoice Number"
	):
		if not invoice.bill_no:
			raise TransformError(
				"MISSING_SUPPLIER_INVOICE_NUMBER",
				_("Supplier Invoice Number is configured as BMD voucher number, but bill_no is empty."),
			)
		return invoice.bill_no
	return invoice.name


def _apply_rounding(groups: list[_Group], invoice: NormalizedInvoice) -> None:
	if not groups:
		raise TransformError("EMPTY_INVOICE", _("Invoice contains no exportable booking groups."))
	raw_net = sum((group.net for group in groups), ZERO)
	raw_gross = sum((group.net + group.included_tax for group in groups), ZERO)
	rounding_tolerance = CENT * max(1, len(groups))
	if abs(abs(invoice.base_net_total) - raw_net) > rounding_tolerance:
		raise TransformError(
			"NET_RECONCILIATION_FAILED",
			_("Item groups differ from the invoice net total by {0}.").format(
				abs(invoice.base_net_total) - raw_net
			),
		)
	if abs(abs(invoice.base_grand_total) - raw_gross) > rounding_tolerance:
		raise TransformError(
			"GROSS_RECONCILIATION_FAILED",
			_("Mapped gross amount differs from the invoice total by {0}.").format(
				abs(invoice.base_grand_total) - raw_gross
			),
		)
	if invoice.currency != invoice.company_currency:
		raw_foreign_gross = sum(
			(group.foreign_net + group.foreign_included_tax for group in groups), ZERO
		)
		if abs(abs(invoice.grand_total) - raw_foreign_gross) > rounding_tolerance:
			raise TransformError(
				"FOREIGN_GROSS_RECONCILIATION_FAILED",
				_("Mapped foreign amount differs from the invoice total by {0}.").format(
					abs(invoice.grand_total) - raw_foreign_gross
				),
			)

	for group in groups:
		group.net = money(group.net)
		group.included_tax = money(group.included_tax)
		group.bmd_tax = money(group.bmd_tax)
		group.foreign_net = money(group.foreign_net)
		group.foreign_included_tax = money(group.foreign_included_tax)
		group.foreign_bmd_tax = money(group.foreign_bmd_tax)

	# ERPNext totals are authoritative. Residual cents are assigned to the largest group,
	# with the stable group key as tie breaker.
	largest = sorted(groups, key=lambda group: (-abs(group.net), _group_key(group)))[0]
	net_residual = money(abs(invoice.base_net_total)) - sum((group.net for group in groups), ZERO)
	largest.net += net_residual
	gross_target = money(abs(invoice.base_grand_total))
	gross_current = sum((group.net + group.included_tax for group in groups), ZERO)
	gross_residual = gross_target - gross_current
	largest.included_tax += gross_residual

	if invoice.currency != invoice.company_currency:
		foreign_gross_target = money(abs(invoice.grand_total))
		foreign_current = sum(
			(group.foreign_net + group.foreign_included_tax for group in groups), ZERO
		)
		foreign_residual = foreign_gross_target - foreign_current
		largest.foreign_included_tax += foreign_residual


def build_booking_lines(invoice: NormalizedInvoice, settings, resolver) -> list[BookingLine]:
	person_account = resolver.party(invoice.party_type, invoice.party)
	groups_by_key: dict[tuple, _Group] = {}

	for item in invoice.items:
		account = resolver.account(
			item.account,
			country=invoice.country,
			tax_category=invoice.tax_category,
			item_group=item.item_group,
		)
		dimensions = resolver.dimensions(
			item.cost_center, item.project, item.accounting_dimensions
		)
		components, (export_tax, export_mapping, export_amount) = _mapped_tax_components(
			invoice, item, resolver
		)
		branch = export_mapping.default_branch or settings.default_branch or ""
		prototype = _Group(
			account=account,
			rate=abs(export_tax.rate),
			tax_code=export_mapping.bmd_tax_code or "",
			sign_rule=export_mapping.sign_rule,
			dimensions=dimensions,
			branch=branch,
			oss_target_country=export_mapping.oss_target_country or "",
			oss_schema=export_mapping.oss_schema or "",
			oss_uid=export_mapping.oss_uid or "",
		)
		key = _group_key(prototype)
		group = groups_by_key.setdefault(key, prototype)
		base_net = abs(item.base_net_amount)
		foreign_net = abs(item.net_amount)
		group.net += base_net
		group.foreign_net += foreign_net
		for tax, mapping, amount in components:
			if mapping.tax_included_in_gross:
				group.included_tax += amount
				group.foreign_included_tax += amount / invoice.conversion_rate
		if export_mapping.export_tax:
			group.bmd_tax += export_amount
			group.foreign_bmd_tax += export_amount / invoice.conversion_rate
		if item.description not in group.descriptions:
			group.descriptions.append(item.description)

	groups = [groups_by_key[key] for key in sorted(groups_by_key)]
	_apply_rounding(groups, invoice)
	amount_sign = invoice.amount_sign
	belegnr = _belegnr(invoice, settings)
	lines: list[BookingLine] = []
	for group in groups:
		gross = money(group.net + group.included_tax)
		tax_sign = _tax_sign(group, amount_sign)
		values: dict[str, Any] = {
			"satzart": 0,
			"konto": person_account,
			"gkonto": group.account,
			"belegnr": belegnr,
			"buchdatum": invoice.posting_date if settings.include_booking_date else None,
			"belegdatum": invoice.belegdatum,
			"buchsymbol": invoice.voucher_type_code,
			"buchcode": 1 if invoice.transaction_type == "Sales" else 2,
			"prozent": group.rate,
			"steuercode": group.tax_code,
			"betrag": money(gross * amount_sign),
			"steuer": money(group.bmd_tax * tax_sign),
			"filiale": group.branch,
			"extbelegnr": invoice.bill_no or "",
			"oss-zielland": group.oss_target_country,
			"oss-schema": group.oss_schema,
			"oss-uidnr": group.oss_uid,
			"text": " | ".join(group.descriptions),
		}
		if group.oss_target_country and invoice.is_return:
			correction_date = invoice.return_against_posting_date or invoice.posting_date
			values["uva-korrperiode"] = correction_date.strftime("%Y%m")
		if invoice.currency != invoice.company_currency:
			values.update(
				{
					"fwbetrag": money(
						(group.foreign_net + group.foreign_included_tax) * amount_sign
					),
					"fwsteuer": money(group.foreign_bmd_tax * tax_sign),
					"waehrung": invoice.currency,
				}
			)
			if settings.include_exchange_rate:
				values["fwkurs"] = invoice.conversion_rate

		kore_rows: list[dict[str, Any]] = []
		if settings.use_kore_allocation_rows and group.dimensions:
			kore_rows.append(
				{"satzart": 1, "kobetrag": money(group.net * amount_sign), **group.dimensions}
			)
		else:
			values.update(group.dimensions)
			if not values.get("kost") and settings.default_cost_center:
				values["kost"] = settings.default_cost_center
		lines.append(
			BookingLine(
				values=values,
				net_amount=money(group.net * amount_sign),
				gross_amount=values["betrag"],
				tax_amount=values["steuer"],
				foreign_net_amount=money(group.foreign_net * amount_sign),
				foreign_gross_amount=values.get("fwbetrag", ZERO),
				foreign_tax_amount=values.get("fwsteuer", ZERO),
				kore_rows=kore_rows,
			)
		)
	return lines


def serialize_booking_lines(lines: list[BookingLine], document_names: list[str]) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	for index, line in enumerate(lines):
		row = dict(line.values)
		if index == 0 and len(document_names) == 1:
			row["dokument"] = document_names[0]
		rows.append(row)
		if index == 0 and len(document_names) > 1:
			rows.extend({"satzart": 5, "dokument": name} for name in document_names)
		rows.extend(dict(kore_row) for kore_row in line.kore_rows)
	return rows
