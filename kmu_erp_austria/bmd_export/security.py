from __future__ import annotations

import frappe
from frappe import _


EXPORT_ROLES = {"BMD Export User", "BMD Export Manager"}
MANAGER_ROLES = {"BMD Export Manager", "System Manager"}


def require_export_role() -> None:
	if frappe.session.user == "Administrator":
		return
	if not EXPORT_ROLES.intersection(frappe.get_roles()):
		frappe.throw(_("BMD Export role required."), frappe.PermissionError)


def require_manager_role() -> None:
	if frappe.session.user == "Administrator":
		return
	if not MANAGER_ROLES.intersection(frappe.get_roles()):
		frappe.throw(_("BMD Export Manager role required."), frappe.PermissionError)


def require_company(company: str) -> None:
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Unknown company."), frappe.DoesNotExistError)
	frappe.has_permission("Company", ptype="read", doc=company, throw=True)


def require_batch(batch) -> None:
	require_export_role()
	require_company(batch.company)
	if not batch.has_permission("read"):
		frappe.throw(_("Not permitted to access this BMD export batch."), frappe.PermissionError)
