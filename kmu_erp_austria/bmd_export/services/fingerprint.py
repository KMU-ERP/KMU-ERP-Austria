from __future__ import annotations

import hashlib
import json
from typing import Any


SYSTEM_FIELDS = {
	"doctype",
	"creation",
	"modified_by",
	"owner",
	"docstatus",
	"idx",
	"parent",
	"parentfield",
	"parenttype",
}


def canonical_json(value: Any) -> str:
	return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def clean_doc(doc) -> dict:
	return {
		key: value
		for key, value in doc.as_dict().items()
		if key not in SYSTEM_FIELDS and not key.startswith("_")
	}


def make_fingerprint(
	invoice,
	settings_snapshot: dict,
	mapping_snapshot: list[dict],
	document_hashes: list[dict],
) -> str:
	payload = {
		"voucher": {
			"doctype": invoice.doctype,
			"name": invoice.name,
			"modified": invoice.modified,
			"base_net_total": str(invoice.base_net_total),
			"base_grand_total": str(invoice.base_grand_total),
			"grand_total": str(invoice.grand_total),
			"currency": invoice.currency,
			"conversion_rate": str(invoice.conversion_rate),
		},
		"settings": settings_snapshot,
		"mappings": mapping_snapshot,
		"documents": document_hashes,
	}
	return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
