"""
Automatically assigns default expense and revenue accounts to item groups based on item_group_accounts_assignments.csv.
"""

import frappe
import csv
import click

def import_item_group_accounts_assignment():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  NOTE: No company found - item group accounts assignments skipped", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Assigning default accounts to item groups for company: {company}")
		_assign_default_accounts(company)

def _assign_default_accounts(company):
	abbr = frappe.db.get_value("Company", company, "abbr")
	csv_path = frappe.get_app_path("kmu_erp_austria", "data", "item_group_accounts_assignments.csv")

	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f, delimiter=";")
		for row in reader:
			item_group_name = row["Item Group"].strip()
			income_account = row["Revenue Account"].strip() + f" - {abbr}"
			expense_account = row["Expense Account"].strip() + f" - {abbr}"

			# Skip if csv row is empty
			if not item_group_name:
				continue

			# Skip if item group does not exist
			if not frappe.db.exists("Item Group", item_group_name):
				click.echo(click.style(f"  NOTE: Item Group '{item_group_name}' not found - skipping", fg="yellow"))
				continue

			# Skip if revenue account does not exist
			if not frappe.db.exists("Account", income_account):
				click.echo(click.style(f"  WARNING: Revenue Account '{income_account}' not found - inserting failed", fg="red"))
				continue

			# Skip if expense account does not exist
			if not frappe.db.exists("Account", expense_account):
				click.echo(click.style(f"  WARNING: Expense Account '{expense_account}' not found - inserting failed", fg="red"))
				continue

			# Skip if entry for this company already exists
			if frappe.db.exists("Item Default", {"parent": item_group_name, "company": company}):
				click.echo(click.style(f"  NOTE: Entry for company '{company}' already exists - skipping", fg="yellow"))
				continue

			doc = frappe.get_doc("Item Group", item_group_name)
			doc.append("item_group_defaults", {
				"company": company,
				"income_account": income_account,
				"expense_account": expense_account,
			})
			doc.save(ignore_permissions=True)

	click.echo(click.style(f"  Completed assigning default accounts to item groups for company: {company}", fg="green"))
