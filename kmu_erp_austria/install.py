import json
import os
import shutil
import sys

import click
import frappe

from kmu_erp_austria.setup.tax_templates import import_tax_templates


def before_install():
	if "erpnext" not in frappe.get_installed_apps():
		click.echo(
			click.style("FEHLER: ERPNext muss vor kmu_erp_austria installiert sein.", fg="red",
			            bold=True))
		click.echo(
			click.style("Bitte zuerst 'bench get-app erpnext --branch <VERSION>' ausführen.",
			            fg="red"))
		click.echo(click.style("Danach 'bench --site <SITE-NAME> install-app erpnext' ausführen.",
		                       fg="red"))
		sys.exit(1)


def after_install():
	if frappe.is_setup_complete():
		click.echo(click.style(
			"  HINWEIS: Setup-Wizard wurde bereits ausgeführt – importiere Kontenplan ...",
			fg="yellow"))
		import_chart_for_companies()
		import_tax_templates()
	else:
		click.echo(click.style(
			"  HINWEIS: Setup-Wizard noch nicht ausgeführt. "
			"Stelle Kontenplan in Wizard zur verfügung ...",
			fg="yellow"
		))
		register_chart_in_wizard()


def register_chart_in_wizard():
	chart_path = frappe.get_app_path("kmu_erp_austria", "data", "at_standard_kontenplan.json")
	dest_dir = frappe.get_app_path(
		"erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified"
	)
	shutil.copy(chart_path, os.path.join(dest_dir, "at_kmu_standard_kontenplan.json"))
	click.echo(click.style("  Kontenplan in Wizard-Auswahl registriert.", fg="green"))


def import_chart_for_companies():
	chart_path = frappe.get_app_path("kmu_erp_austria", "data", "at_standard_kontenplan.json")

	with open(chart_path) as f:
		chart = json.load(f)

	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style(
			"HINWEIS: Kein Unternehmen gefunden. "
			"Bitte nach dem Anlegen einer Firma 'bench execute kmu_erp_austria.install.import_chart_for_companies' ausführen.",
			fg="yellow"
		))
		return

	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
	from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
		unset_existing_data,
	)

	frappe.local.flags.allow_unverified_charts = True

	for company in companies:
		if frappe.db.exists("Account", {"company": company}):
			click.echo(f"  Bestehende Konten für '{company}' werden ersetzt ...")
			unset_existing_data(company)

		click.echo(f"  Importiere Kontenplan für '{company}' ...")
		create_charts(company, custom_chart=chart["tree"])
		frappe.db.commit()
		click.echo(
			click.style(f"  Kontenplan für '{company}' erfolgreich importiert.", fg="green"))

	frappe.local.flags.allow_unverified_charts = False
