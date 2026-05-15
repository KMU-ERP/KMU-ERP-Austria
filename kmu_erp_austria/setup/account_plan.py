import json
import os
import shutil

import click
import frappe
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
	unset_existing_data,
)


def register_account_plan_in_wizard():
	chart_path = frappe.get_app_path("kmu_erp_austria", "data", "at_standard_kontenplan.json")
	dest_dir = frappe.get_app_path(
		"erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified"
	)
	shutil.copy(chart_path, os.path.join(dest_dir, "at_kmu_standard_kontenplan.json"))
	click.echo(click.style("  Charts of Accounts registered in wizard selection.", fg="green"))


def import_account_plan_for_companies():
	chart_path = frappe.get_app_path("kmu_erp_austria", "data", "at_standard_kontenplan.json")

	with open(chart_path) as f:
		chart = json.load(f)

	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style(
			"NOTE: No company found. "
			"Please run 'bench execute kmu_erp_austria.setup.account_plan.import_account_plan_for_companies' after creating a company.",
			fg="yellow"
		))
		return

	frappe.local.flags.allow_unverified_charts = True

	for company in companies:
		if frappe.db.exists("Account", {"company": company}):
			click.echo(f"  Replacing existing accounts for '{company}' ...")
			unset_existing_data(company)

		click.echo(f"  Importing Chart of Accounts for '{company}' ...")
		create_charts(company, custom_chart=chart["tree"])
		click.echo(click.style(f"  Chart of Account for '{company}' successfully imported.", fg="green"))

	frappe.local.flags.allow_unverified_charts = False
