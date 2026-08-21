from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from frappe import _

from kmu_erp_austria.bmd_export.services.constants import FIELD_REGISTRY


_CONTROL_WHITESPACE = re.compile(r"[\r\n\t]+")


class CSVRenderError(ValueError):
	def __init__(self, code: str, message: str, context: dict | None = None):
		super().__init__(message)
		self.code = code
		self.context = context or {}


def profile_columns(profile) -> list[str]:
	return [row.field_name for row in profile.columns]


def sanitize_text(value: Any, delimiter: str) -> str:
	text = _CONTROL_WHITESPACE.sub(" ", str(value))
	text = " ".join(text.split())
	return text.replace(delimiter, ",")


def _decimal(value: Any, precision: int, decimal_separator: str) -> str:
	number = value if isinstance(value, Decimal) else Decimal(str(value))
	quantum = Decimal(1).scaleb(-precision)
	rendered = f"{number.quantize(quantum, rounding=ROUND_HALF_UP):.{precision}f}"
	return rendered.replace(".", decimal_separator)


def render_value(field_name: str, value: Any, profile) -> str:
	if value is None or value == "":
		return ""
	definition = FIELD_REGISTRY[field_name]
	if definition.field_type == "date":
		if isinstance(value, datetime):
			value = value.date()
		if not isinstance(value, date):
			raise CSVRenderError("INVALID_DATE", _("{0} is not a date.").format(field_name))
		result = value.strftime(profile.date_format)
	elif definition.field_type == "decimal":
		precision_field = {
			"prozent": "tax_rate_precision",
			"fwkurs": "exchange_rate_precision",
			"komenge": "quantity_precision",
		}.get(field_name, "money_precision")
		configured_precision = getattr(profile, precision_field, None)
		precision = int(
			configured_precision if configured_precision is not None else (definition.precision or 2)
		)
		result = _decimal(value, precision, profile.decimal_separator)
	elif definition.field_type == "integer":
		result = str(int(value))
	elif definition.field_type == "period":
		result = str(value)
		if not re.fullmatch(r"\d{6}", result):
			raise CSVRenderError(
				"INVALID_PERIOD", _("{0} must use the BMD JJJJMM format.").format(field_name)
			)
	else:
		result = sanitize_text(value, profile.delimiter)

	if definition.max_length and len(result) > definition.max_length:
		raise CSVRenderError(
			"FIELD_TOO_LONG",
			_("BMD field {0} exceeds {1} characters.").format(
				field_name, definition.max_length
			),
			{"field": field_name, "length": len(result)},
		)
	return result


def render_csv(rows: Iterable[dict[str, Any]], profile) -> bytes:
	columns = profile_columns(profile)
	unknown = set(columns) - set(FIELD_REGISTRY)
	if unknown:
		raise CSVRenderError(
			"UNKNOWN_FIELD", _("Unknown BMD fields: {0}").format(", ".join(sorted(unknown)))
		)
	delimiter = "\t" if profile.delimiter == "\\t" else profile.delimiter
	line_ending = "\r\n" if profile.line_ending == "CRLF" else "\n"
	stream = io.StringIO(newline="")
	writer = csv.writer(
		stream,
		delimiter=delimiter,
		lineterminator=line_ending,
		quoting=csv.QUOTE_MINIMAL,
	)
	writer.writerow(columns)
	for row_number, row in enumerate(rows, start=2):
		try:
			writer.writerow([render_value(column, row.get(column), profile) for column in columns])
		except (CSVRenderError, ArithmeticError, ValueError) as exc:
			if isinstance(exc, CSVRenderError):
				exc.context.setdefault("row", row_number)
				raise
			raise CSVRenderError(
				"INVALID_VALUE",
				_("Unable to render BMD row {0}: {1}").format(row_number, exc),
				{"row": row_number},
			) from exc
	try:
		return stream.getvalue().encode(profile.encoding)
	except UnicodeEncodeError as exc:
		raise CSVRenderError(
			"ENCODING_ERROR",
			_("CSV content cannot be represented using {0}.").format(profile.encoding),
		) from exc
