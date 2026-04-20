"""
Automatically assigns default expense and revenue accounts and item tax templates
to item groups based on item_group_defaults.csv.
"""

import frappe
import csv
import click


def import_item_group_defaults():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  NOTE: No company found - item group accounts assignments skipped", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Assigning default accounts and tax templates to item groups for company: {company}")
		_assign_defaults(company)
		click.echo(click.style(f"  Completed assigning defaults to item groups for company: {company}", fg="green"))


def _assign_defaults(company):
	abbr = frappe.db.get_value("Company", company, "abbr")
	csv_path = frappe.get_app_path("kmu_erp_austria", "data", "item_group_defaults.csv")

	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f, delimiter=";")
		for row in reader:
			item_group_name = row["Item Group"].strip()

			# Skip if csv row is empty
			if not item_group_name:
				continue

			# Skip if item group does not exist
			if not frappe.db.exists("Item Group", item_group_name):
				click.echo(click.style(f"  NOTE: Item Group '{item_group_name}' not found - skipping", fg="yellow"))
				continue

			doc = frappe.get_doc("Item Group", item_group_name)
			modified = False

			# --- Accounts block ---
			income_account = row["Revenue Account"].strip() + f" - {abbr}"
			expense_account = row["Expense Account"].strip() + f" - {abbr}"

			if not frappe.db.exists("Item Default", {"parent": item_group_name, "company": company}):
				if not frappe.db.exists("Account", income_account):
					click.echo(click.style(f"  WARNING: Revenue Account '{income_account}' not found - skipping accounts for '{item_group_name}'", fg="red"))
				elif not frappe.db.exists("Account", expense_account):
					click.echo(click.style(f"  WARNING: Expense Account '{expense_account}' not found - skipping accounts for '{item_group_name}'", fg="red"))
				else:
					doc.append("item_group_defaults", {
						"company": company,
						"income_account": income_account,
						"expense_account": expense_account,
					})
					modified = True

			# --- Tax AT block ---
			tax_at = row["Tax AT"].strip() + f" - {abbr}"
			if not frappe.db.exists("Item Tax", {"parent": item_group_name, "item_tax_template": tax_at}):
				if not frappe.db.exists("Item Tax Template", tax_at):
					click.echo(click.style(f"  WARNING: Item Tax Template '{tax_at}' not found - skipping AT tax for '{item_group_name}'", fg="red"))
				else:
					doc.append("taxes", {
						"item_tax_template": tax_at,
						"tax_category": "Österreich",
					})
					modified = True

			# --- Tax DE block ---
			tax_de = row["Tax DE"].strip() + f" - {abbr}"
			if not frappe.db.exists("Item Tax", {"parent": item_group_name, "item_tax_template": tax_de}):
				if not frappe.db.exists("Item Tax Template", tax_de):
					click.echo(click.style(f"  WARNING: Item Tax Template '{tax_de}' not found - skipping DE tax for '{item_group_name}'", fg="red"))
				else:
					doc.append("taxes", {
						"item_tax_template": tax_de,
						"tax_category": "Deutschland",
					})
					modified = True

			if modified:
				doc.save(ignore_permissions=True)
