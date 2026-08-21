from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from kmu_erp_austria.bmd_export.services.models import NormalizedInvoice, NormalizedItem, NormalizedTax
from kmu_erp_austria.bmd_export.services.transform import build_booking_lines, serialize_booking_lines


class Resolver:
	def __init__(self, mapping):
		self.mapping = mapping

	def party(self, party_type, party):
		return "200000" if party_type == "Customer" else "300000"

	def account(self, account, **kwargs):
		return "4000" if "Sales" in account else "5000"

	def dimensions(self, cost_center, project, accounting_dimensions=()):
		return {"kost": "10"} if cost_center else {}

	def tax(self, **kwargs):
		return self.mapping


def settings(**values):
	defaults = {
		"purchase_belegnr_source": "ERPNext Name",
		"include_booking_date": 0,
		"default_branch": "",
		"default_cost_center": "",
		"use_kore_allocation_rows": 0,
		"include_exchange_rate": 0,
	}
	return SimpleNamespace(**{**defaults, **values})


def invoice(doctype="Sales Invoice", is_return=False, grand="120", currency="EUR"):
	tax = NormalizedTax(
		tax_row="TAX-1",
		account="VAT - C",
		rate=Decimal("20"),
		amount=Decimal("20"),
		taxable_amount=Decimal("100"),
	)
	item = NormalizedItem(
		row_name="ITEM-1",
		item_code="ITEM",
		item_group="Services",
		account="Sales - C" if doctype == "Sales Invoice" else "Expense - C",
		net_amount=Decimal("100"),
		base_net_amount=Decimal("100"),
		cost_center="Main - C",
		project=None,
		description="Rechnung",
		taxes=(tax,),
	)
	return NormalizedInvoice(
		doctype=doctype,
		name="INV-1",
		company="Company",
		posting_date=date(2026, 1, 1),
		belegdatum=date(2026, 1, 1),
		party_type="Customer" if doctype == "Sales Invoice" else "Supplier",
		party="PARTY-1",
		party_name="Musterkunde",
		control_account="Receivable - C" if doctype == "Sales Invoice" else "Payable - C",
		country="Austria",
		tax_category=None,
		currency=currency,
		company_currency="EUR",
		conversion_rate=Decimal("1"),
		base_net_total=Decimal("100"),
		base_grand_total=Decimal(grand),
		grand_total=Decimal(grand),
		is_return=is_return,
		return_against=None,
		return_against_posting_date=None,
		bill_no="SUP-1" if doctype == "Purchase Invoice" else None,
		modified="2026-01-01 00:00:00",
		remarks="Rechnung",
		items=(item,),
	)


class TestBMDTransform(unittest.TestCase):
	def mapping(self, sign_rule="Standard Output Tax", included=1, **values):
		defaults = dict(
			amount_source="ERP Item Tax Detail",
			sign_rule=sign_rule,
			export_tax=1,
			tax_included_in_gross=included,
			default_branch="",
			bmd_tax_code="1",
			oss_target_country="",
			oss_schema="",
			oss_uid="",
		)
		return SimpleNamespace(**{**defaults, **values})

	def test_official_ar_and_gu_signs(self):
		for is_return, amount, tax, symbol in (
			(False, Decimal("120.00"), Decimal("-20.00"), "AR"),
			(True, Decimal("-120.00"), Decimal("20.00"), "GU"),
		):
			line = build_booking_lines(invoice(is_return=is_return), settings(), Resolver(self.mapping()))[0]
			self.assertEqual(line.values["betrag"], amount)
			self.assertEqual(line.values["steuer"], tax)
			self.assertEqual(line.values["buchsymbol"], symbol)
			self.assertEqual(line.values["buchcode"], 1)

	def test_official_er_standard_and_output_side_tax(self):
		standard = self.mapping("Standard Input Tax", included=1)
		line = build_booking_lines(invoice("Purchase Invoice"), settings(), Resolver(standard))[0]
		self.assertEqual(line.values["betrag"], Decimal("-120.00"))
		self.assertEqual(line.values["steuer"], Decimal("20.00"))

		output_side = self.mapping("Output-side Tax", included=0)
		line = build_booking_lines(
			invoice("Purchase Invoice", grand="100"), settings(), Resolver(output_side)
		)[0]
		self.assertEqual(line.values["betrag"], Decimal("-100.00"))
		self.assertEqual(line.values["steuer"], Decimal("-20.00"))

		credit = build_booking_lines(
			invoice("Purchase Invoice", is_return=True, grand="100"),
			settings(),
			Resolver(output_side),
		)[0]
		self.assertEqual(credit.values["betrag"], Decimal("100.00"))
		self.assertEqual(credit.values["steuer"], Decimal("20.00"))

	def test_kore_and_document_order(self):
		lines = build_booking_lines(
			invoice(), settings(use_kore_allocation_rows=1), Resolver(self.mapping())
		)
		rows = serialize_booking_lines(lines, ["one.pdf", "two.pdf"])
		self.assertEqual([row["satzart"] for row in rows], [0, 5, 5, 1])
		self.assertEqual(rows[-1]["kobetrag"], Decimal("100.00"))

	def test_oss_correction_uses_original_invoice_period(self):
		original = invoice(is_return=True)
		original = replace(original, return_against="INV-OLD", return_against_posting_date=date(2026, 4, 1))
		mapping = self.mapping(oss_target_country="DE", oss_schema="1", default_branch="1")
		line = build_booking_lines(original, settings(), Resolver(mapping))[0]
		self.assertEqual(line.values["uva-korrperiode"], "202604")
		self.assertEqual(line.values["oss-zielland"], "DE")

	def test_foreign_currency_variant_one_omits_exchange_rate(self):
		foreign = invoice(currency="CHF")
		foreign_item = replace(foreign.items[0], net_amount=Decimal("98.17"))
		foreign = replace(
			foreign,
			conversion_rate=Decimal("1.01868"),
			grand_total=Decimal("117.80"),
			items=(foreign_item,),
		)
		line = build_booking_lines(foreign, settings(), Resolver(self.mapping()))[0]
		self.assertEqual(line.values["waehrung"], "CHF")
		self.assertEqual(line.values["fwbetrag"], Decimal("117.80"))
		self.assertNotIn("fwkurs", line.values)


if __name__ == "__main__":
	unittest.main()
