from __future__ import annotations

import frappe

from kmu_erp_austria.bmd_export.services.constants import DEFAULT_COLUMNS


ROLES = ("BMD Export User", "BMD Export Manager")
STANDARD_PROFILE = "BMD NTCS Standard"


def ensure_bmd_export_defaults() -> None:
	"""Create app-owned defaults without overwriting user configuration."""
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert()

	if not frappe.db.exists("BMD Export Profile", STANDARD_PROFILE):
		profile = frappe.get_doc(
			{
				"doctype": "BMD Export Profile",
				"profile_name": STANDARD_PROFILE,
				"is_standard": 1,
				"is_active": 1,
				"delimiter": ";",
				"encoding": "utf-8-sig",
				"decimal_separator": ".",
				"date_format": "%d.%m.%Y",
				"line_ending": "CRLF",
				"columns": [{"field_name": field_name} for field_name in DEFAULT_COLUMNS],
			}
		)
		profile.flags.bmd_setup = True
		profile.insert(ignore_permissions=True)
