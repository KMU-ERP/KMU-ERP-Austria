import sys

import click
import frappe

from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from kmu_erp_austria.setup.account_plan import import_account_plan_for_companies, register_account_plan_in_wizard
from kmu_erp_austria.setup.payment_terms import import_payment_terms
from kmu_erp_austria.setup.tax_rules import import_tax_rules
from kmu_erp_austria.setup.tax_templates import import_tax_templates
from kmu_erp_austria.setup.letter_head import import_letter_head
from kmu_erp_austria.setup.item_group_accounts_assignment import import_item_group_accounts_assignment

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
	setup_complete(args)
	_import_configurations()

def app_setup():
	_import_account_plan()
	_import_configurations()

def _import_configurations():
	import_tax_templates()
	import_tax_rules()
	import_payment_terms()
	import_letter_head()
	import_item_group_accounts_assignment()

def _import_account_plan():
	register_account_plan_in_wizard()
	import_account_plan_for_companies()

def after_migrate():
	if frappe.is_setup_complete():
		import_item_group_accounts_assignment()
