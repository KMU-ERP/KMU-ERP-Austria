import sys

import click
import frappe

from kmu_erp_austria.setup.account_plan import import_account_plan_for_companies, register_account_plan_in_wizard
from kmu_erp_austria.setup.payment_terms import import_payment_terms
from kmu_erp_austria.setup.tax_rules import import_tax_rules
from kmu_erp_austria.setup.tax_templates import import_tax_templates


def before_install():
	if "erpnext" not in frappe.get_installed_apps():
		click.echo(click.style("FEHLER: ERPNext muss vor kmu_erp_austria installiert sein.", fg="red", bold=True))
		click.echo(click.style("Bitte zuerst 'bench get-app erpnext --branch <VERSION>' ausführen.", fg="red"))
		click.echo(click.style("Danach 'bench --site <SITE-NAME> install-app erpnext' ausführen.", fg="red"))
		sys.exit(1)


def after_install():
	if frappe.is_setup_complete():
		click.echo(click.style(
			"  HINWEIS: Setup-Wizard wurde bereits ausgeführt – importiere Kontenplan ...",
			fg="yellow"
		))
		import_account_plan_for_companies()
		import_tax_templates()
		import_tax_rules()
		import_payment_terms()
	else:
		click.echo(click.style(
			"  HINWEIS: Setup-Wizard noch nicht ausgeführt. "
			"Stelle Kontenplan in Wizard zur Verfügung ...",
			fg="yellow"
		))
		register_account_plan_in_wizard()
