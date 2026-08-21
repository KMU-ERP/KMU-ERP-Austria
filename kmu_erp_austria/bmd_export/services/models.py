from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class NormalizedTax:
	tax_row: str
	account: str | None
	rate: Decimal
	amount: Decimal
	taxable_amount: Decimal


@dataclass(frozen=True, slots=True)
class NormalizedItem:
	row_name: str
	item_code: str | None
	item_group: str | None
	account: str
	net_amount: Decimal
	base_net_amount: Decimal
	cost_center: str | None
	project: str | None
	description: str
	taxes: tuple[NormalizedTax, ...]
	accounting_dimensions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class NormalizedInvoice:
	doctype: str
	name: str
	company: str
	posting_date: date
	belegdatum: date
	party_type: str
	party: str
	party_name: str
	control_account: str
	country: str | None
	tax_category: str | None
	currency: str
	company_currency: str
	conversion_rate: Decimal
	base_net_total: Decimal
	base_grand_total: Decimal
	grand_total: Decimal
	is_return: bool
	return_against: str | None
	return_against_posting_date: date | None
	bill_no: str | None
	modified: str
	remarks: str
	items: tuple[NormalizedItem, ...]

	@property
	def transaction_type(self) -> str:
		return "Sales" if self.doctype == "Sales Invoice" else "Purchase"

	@property
	def voucher_type_code(self) -> str:
		if self.doctype == "Sales Invoice":
			return "GU" if self.is_return else "AR"
		return "EG" if self.is_return else "ER"

	@property
	def amount_sign(self) -> Decimal:
		if self.transaction_type == "Sales":
			return Decimal("-1") if self.is_return else Decimal("1")
		return Decimal("1") if self.is_return else Decimal("-1")


@dataclass(slots=True)
class BookingLine:
	values: dict[str, Any]
	net_amount: Decimal
	gross_amount: Decimal
	tax_amount: Decimal
	foreign_net_amount: Decimal = ZERO
	foreign_gross_amount: Decimal = ZERO
	foreign_tax_amount: Decimal = ZERO
	kore_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AttachmentPayload:
	export_name: str
	content: bytes
	sha256: str
	source_file: str
	mime_type: str


@dataclass(slots=True)
class InvoiceExport:
	invoice: NormalizedInvoice
	rows: list[dict[str, Any]]
	attachments: list[AttachmentPayload]
	used_mappings: set[str]
	net_total: Decimal
	tax_total: Decimal
	gross_total: Decimal
	fingerprint: str = ""
	warnings: list[dict[str, Any]] = field(default_factory=list)
