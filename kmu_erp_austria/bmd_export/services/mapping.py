from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate


class MappingResolutionError(ValueError):
	def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
		super().__init__(message)
		self.code = code
		self.context = context or {}


def _is_valid(row, posting_date: date) -> bool:
	return (not row.valid_from or getdate(row.valid_from) <= posting_date) and (
		not row.valid_to or getdate(row.valid_to) >= posting_date
	)


def _choose(rows: list, label: str, context: dict[str, Any], condition_fields: tuple[str, ...]):
	if not rows:
		raise MappingResolutionError(
			"MISSING_MAPPING", _("Missing {0} mapping.").format(_(label)), context
		)
	ranked: list[tuple[tuple[int, int], Any]] = []
	for row in rows:
		specificity = sum(bool(row.get(fieldname)) for fieldname in condition_fields)
		ranked.append(((specificity, int(row.priority or 0)), row))
	best_rank = max(rank for rank, _row in ranked)
	winners = [row for rank, row in ranked if rank == best_rank]
	if len(winners) != 1:
		raise MappingResolutionError(
			"AMBIGUOUS_MAPPING",
			_("Multiple equally ranked {0} mappings match.").format(_(label)),
			{**context, "mappings": [row.name for row in winners]},
		)
	return winners[0]


class MappingResolver:
	def __init__(self, company: str, posting_date: date):
		self.company = company
		self.posting_date = posting_date
		self.used: set[str] = set()

	def party(self, party_type: str, party: str) -> str:
		rows = frappe.get_all(
			"BMD Party Mapping",
			filters={
				"company": self.company,
				"party_type": party_type,
				"party": party,
				"active": 1,
			},
			fields="*",
		)
		row = _choose(
			[row for row in rows if _is_valid(row, self.posting_date)],
			"party",
			{"party_type": party_type, "party": party},
			(),
		)
		self.used.add(row.name)
		return row.bmd_person_account

	def account(
		self,
		erpnext_account: str,
		*,
		country: str | None,
		tax_category: str | None,
		item_group: str | None,
	) -> str:
		rows = frappe.get_all(
			"BMD Account Mapping",
			filters={"company": self.company, "erpnext_account": erpnext_account, "active": 1},
			fields="*",
		)
		matching = [
			row
			for row in rows
			if _is_valid(row, self.posting_date)
			and (not row.country or row.country == country)
			and (not row.tax_category or row.tax_category == tax_category)
			and (not row.item_group or row.item_group == item_group)
		]
		row = _choose(
			matching,
			"account",
			{
				"erpnext_account": erpnext_account,
				"country": country,
				"tax_category": tax_category,
				"item_group": item_group,
			},
			("country", "tax_category", "item_group"),
		)
		bmd_account = frappe.get_cached_doc("BMD Account", row.bmd_account)
		if bmd_account.company != self.company or not bmd_account.active:
			raise MappingResolutionError(
				"INVALID_MAPPING",
				_("BMD account mapping {0} points to an inactive account.").format(row.name),
			)
		self.used.update({row.name, bmd_account.name})
		return bmd_account.account_number

	def tax(
		self,
		*,
		transaction_type: str,
		rate: Decimal,
		tax_category: str | None,
		country: str | None,
		erp_tax_account: str | None,
		country_group: str | None = None,
	):
		rows = frappe.get_all(
			"BMD Tax Mapping",
			filters={"company": self.company, "active": 1},
			fields="*",
		)
		matching = []
		for row in rows:
			if not _is_valid(row, self.posting_date):
				continue
			if row.transaction_type not in {transaction_type, "Both"}:
				continue
			if Decimal(str(row.tax_rate or 0)).quantize(Decimal("0.001")) != rate.quantize(
				Decimal("0.001")
			):
				continue
			if row.tax_category and row.tax_category != tax_category:
				continue
			if row.country and row.country != country:
				continue
			if row.country_group and row.country_group != country_group:
				continue
			if row.erp_tax_account and row.erp_tax_account != erp_tax_account:
				continue
			matching.append(row)
		row = _choose(
			matching,
			"tax",
			{
				"transaction_type": transaction_type,
				"rate": str(rate),
				"tax_category": tax_category,
				"country": country,
				"erp_tax_account": erp_tax_account,
			},
			("tax_category", "country", "country_group", "erp_tax_account"),
		)
		self.used.add(row.name)
		return row

	def dimensions(
		self,
		cost_center: str | None,
		project: str | None,
		accounting_dimensions: tuple[tuple[str, str], ...] = (),
	) -> dict[str, str]:
		result: dict[str, str] = {}
		sources = [
			("Cost Center", "", cost_center),
			("Project", "", project),
			*(("Accounting Dimension", fieldname, value) for fieldname, value in accounting_dimensions),
		]
		for source_type, source_field, source_value in sources:
			if not source_value:
				continue
			rows = frappe.get_all(
				"BMD Dimension Mapping",
				filters={
					"company": self.company,
					"source_type": source_type,
					"source_value": source_value,
					"active": 1,
				},
				fields="*",
			)
			valid_rows = [row for row in rows if _is_valid(row, self.posting_date)]
			valid_rows = [
				row
				for row in valid_rows
				if source_type != "Accounting Dimension" or row.source_field == source_field
			]
			if not valid_rows:
				raise MappingResolutionError(
					"MISSING_MAPPING",
					_("Missing {0} dimension mapping.").format(_(source_type)),
					{
						"source_type": source_type,
						"source_field": source_field,
						"source_value": source_value,
					},
				)
			for target_field in {row.target_field for row in valid_rows}:
				candidates = [
					row
					for row in valid_rows
					if row.target_field == target_field
				]
				row = _choose(
					candidates,
					"dimension",
					{
						"source_type": source_type,
						"source_field": source_field,
						"source_value": source_value,
						"target": target_field,
					},
					(),
				)
				if target_field in result and result[target_field] != row.bmd_value:
					raise MappingResolutionError(
						"AMBIGUOUS_DIMENSION",
						_("Multiple source dimensions resolve to {0}.").format(target_field),
					)
				result[target_field] = row.bmd_value
				self.used.add(row.name)
		return result
