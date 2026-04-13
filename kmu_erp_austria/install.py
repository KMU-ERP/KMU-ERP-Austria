import sys

import click
import frappe

from kmu_erp_austria.setup.account_plan import import_account_plan_for_companies, register_account_plan_in_wizard
from kmu_erp_austria.setup.payment_terms import import_payment_terms
from kmu_erp_austria.setup.tax_rules import import_tax_rules
from kmu_erp_austria.setup.tax_templates import import_tax_templates
from kmu_erp_austria.setup.letter_head import import_letter_head
from kmu_erp_austria.setup.item_group_accounts_assignment import import_item_group_accounts_assignment


def before_install():
	if "erpnext" not in frappe.get_installed_apps():
		click.echo(click.style("ERROR: ERPNext must be installed before kmu_erp_austria.", fg="red", bold=True))
		click.echo(click.style("Please run 'bench get-app erpnext --branch <VERSION>' first.", fg="red"))
		click.echo(click.style("Then run 'bench --site <SITE-NAME> install-app erpnext'.", fg="red"))
		sys.exit(1)


def after_install():
	if frappe.is_setup_complete():
		click.echo(click.style(
			"  NOTE: Setup wizard has already been completed – importing Chart of Accounts ...",
			fg="yellow"
		))
		import_account_plan_for_companies()
		import_tax_templates()
		import_tax_rules()
		import_payment_terms()
		import_letter_head()
	else:
		click.echo(click.style(
			"  NOTE: Setup wizard has not been completed yet. "
			"Making Chart of Accounts available in wizard ...",
			fg="yellow"
		))
		register_account_plan_in_wizard()

def after_sync():
	if frappe.is_setup_complete():
		import_item_group_accounts_assignment()

def after_migrate():
	if frappe.is_setup_complete():
		import_item_group_accounts_assignment()
