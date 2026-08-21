from __future__ import annotations

from dataclasses import dataclass


DEFAULT_COLUMNS = (
	"satzart",
	"konto",
	"gkonto",
	"belegnr",
	"buchdatum",
	"belegdatum",
	"buchsymbol",
	"buchcode",
	"prozent",
	"steuercode",
	"betrag",
	"steuer",
	"kost",
	"filiale",
	"extbelegnr",
	"fwbetrag",
	"fwsteuer",
	"waehrung",
	"fwkurs",
	"uva-korrperiode",
	"oss-zielland",
	"oss-schema",
	"oss-uidnr",
	"dokument",
	"kobetrag",
	"kotraeger",
	"koabteilung",
	"kodimension",
	"kogeschaeftsbereich",
	"komenge",
	"komengenr",
	"text",
)

REQUIRED_COLUMNS = {
	"satzart",
	"konto",
	"gkonto",
	"belegnr",
	"belegdatum",
	"buchsymbol",
	"buchcode",
	"betrag",
	"text",
}


@dataclass(frozen=True, slots=True)
class BMDField:
	field_type: str = "text"
	max_length: int | None = None
	precision: int | None = None


FIELD_REGISTRY = {
	"satzart": BMDField("integer", 2),
	"konto": BMDField("text", 10),
	"gkonto": BMDField("text", 10),
	"belegnr": BMDField("text", 60),
	"buchdatum": BMDField("date"),
	"belegdatum": BMDField("date"),
	"buchsymbol": BMDField("text", 4),
	"buchcode": BMDField("integer", 2),
	"prozent": BMDField("decimal", precision=3),
	"steuercode": BMDField("text", 4),
	"betrag": BMDField("decimal", precision=2),
	"steuer": BMDField("decimal", precision=2),
	"kost": BMDField("text", 20),
	"filiale": BMDField("text", 9),
	"extbelegnr": BMDField("text", 60),
	"fwbetrag": BMDField("decimal", precision=2),
	"fwsteuer": BMDField("decimal", precision=2),
	"waehrung": BMDField("text", 4),
	"fwkurs": BMDField("decimal", precision=8),
	"uva-korrperiode": BMDField("period", 6),
	"oss-zielland": BMDField("text", 4),
	"oss-schema": BMDField("text", 1),
	"oss-uidnr": BMDField("text", 20),
	# Satzart 5 is limited to 255 even though Satzart 0 documents allow 2000.
	"dokument": BMDField("text", 255),
	"kobetrag": BMDField("decimal", precision=2),
	"kotraeger": BMDField("text", 20),
	"koabteilung": BMDField("text", 20),
	"kodimension": BMDField("text", 20),
	"kogeschaeftsbereich": BMDField("text", 20),
	"komenge": BMDField("decimal", precision=6),
	"komengenr": BMDField("text", 18),
	"text": BMDField("text", 255),
}

DEFAULT_DOCUMENT_FILENAME_TEMPLATE = (
	"{{ voucher_type_code }}-{{ voucher_name }}_{{ attachment_no }}"
)
SUPPORTED_ENCODINGS = {"utf-8-sig", "cp1252"}
SUPPORTED_DELIMITERS = {";", ",", "\t"}
