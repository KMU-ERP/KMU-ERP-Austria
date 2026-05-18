import sys

import click
import frappe

from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from kmu_erp_austria.setup.account_plan import import_account_plan_for_companies, register_account_plan_in_wizard
from kmu_erp_austria.setup.payment_terms import import_payment_terms
from kmu_erp_austria.setup.tax_templates import import_tax_templates
from kmu_erp_austria.setup.letter_head import import_letter_head
from kmu_erp_austria.setup.item_group_defaults import import_item_group_defaults
from kmu_erp_austria.setup.company_address import create_company_address
from kmu_erp_austria.setup.default_settings import import_default_settings
from kmu_erp_austria.setup.default_accounts import set_default_accounts_to_company

def auto_erpnext_setup(args):
	"""
	Handles auto setup of kmu_erp_austria app.
	The Wizard will be filled out programmatically.
	Tax Templates, Tax rules, Letter Head, Item Group Accounts Assignment will be imported.
	:param args: Arguments for Completion of Wizard
	"""
	if "erpnext" not in frappe.get_installed_apps():
		click.echo(click.style("ERROR: ERPNext must be installed before kmu_erp_austria.", fg="red", bold=True))
		click.echo(click.style("Please run 'bench get-app erpnext --branch <VERSION>' first.", fg="red"))
		click.echo(click.style("Then run 'bench --site <SITE-NAME> install-app erpnext'.", fg="red"))
		sys.exit(1)

	register_account_plan_in_wizard()
	click.echo("  Filling out the wizard ...")
	setup_complete(args)
	click.echo(click.style("  Wizard completed successfully.", fg="green"))

	company_name = args.get("company_name")

	click.echo(f"  Setting tax id for company '{company_name}' ...")
	if args.get("tax_id") and company_name:
		frappe.db.set_value("Company", company_name, "tax_id", args.get("tax_id"))
		frappe.db.commit()
		click.echo(click.style(f"  Tax id for company '{company_name}' set successfully.", fg="green"))

	create_company_address(args, company_name)

	_import_configurations()
	set_default_accounts_to_company(company_name)

def app_setup():
	"""
	Handles app setup after completion of the wizard. For the use case that the app is installed after some time using ERPNext.
	"""
	_import_account_plan()
	_import_configurations()

	companies = frappe.get_all("Company", pluck="name")
	for company in companies:
		set_default_accounts_to_company(company)

def _import_configurations():
	import_tax_templates()
	import_payment_terms()
	import_letter_head()
	import_item_group_defaults()
	import_default_settings()

def _import_account_plan():
	register_account_plan_in_wizard()
	import_account_plan_for_companies()

def after_migrate():
	"""
	Important for fixtures. If the bench command `bench migrate` is used, the system will automatically
	take the json files of the fixtures as they are and import them. The json file of the Item Groups does not have
	the revenue and expense accounts, as they are assigned later. So it is important to import Item Group Accounts Assignment
	after the migration.
	"""
	if frappe.is_setup_complete():
		import_item_group_defaults()
