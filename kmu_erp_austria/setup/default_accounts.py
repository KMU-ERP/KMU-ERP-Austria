import frappe
import click

DEFAULT_ACCOUNTS = [
	{
		"field_name": "default_cash_account",
		"account_name": "2700 - Kassenbestand"
	},
	{
		"field_name": "default_receivable_account",
		"account_name": "2000 - Forderungen aus Lieferungen und Leistungen Inland"
	},
	{
		"field_name": "default_payable_account",
		"account_name": "3300 - Verbindlichkeiten aus Lieferungen und Leistungen Inland"
	},
	{
		"field_name": "default_expense_account",
		"account_name": "5050 - Wareneinsatz"
	},
	{
		"field_name": "default_income_account",
		"account_name": "4000 - Erlöse 20 %"
	},
	{
		"field_name": "default_discount_account",
		"account_name": "4400 - Skontoaufwand 20 %"
	},
	{
		"field_name": "exchange_gain_loss_account",
		"account_name": "5860 - Kursverluste Fremdwährungstransaktionen"
	},
	{
		"field_name": "default_deferred_revenue_account",
		"account_name": "3900 - Passive Rechnungsabgrenzungsposten"
	},
	{
		"field_name": "default_deferred_expense_account",
		"account_name": "2900 - aktive Rechnungsabgrenzungsposten"
	},
	{
		"field_name": "accumulated_depreciation_account",
		"account_name": "0695 - Kumulierte Abschreibungen Sachanlagen"
	},
	{
		"field_name": "depreciation_expense_account",
		"account_name": "7020 - Abschreibungen auf Sachanlagen"
	},
	{
		"field_name": "disposal_account",
		"account_name": "7820 - Buchwert abgegangener Anlagen"
	},
	{
		"field_name": "capital_work_in_progress_account",
		"account_name": "0710 - Anlagen in Bau"
	},
]

def set_default_accounts_to_company(company_name):
	click.echo(f"  Setting default accounts to company {company_name} ...")

	if not frappe.db.exists("Company", company_name):
		click.echo(click.style(f"  Company {company_name} doesn't exist", fg="red"))
		return

	company = frappe.get_doc("Company", company_name)

	for account in DEFAULT_ACCOUNTS:
		field_name = account["field_name"]
		account_name = account["account_name"] + " - " + company.abbr

		frappe.db.set_value("Company", company_name, field_name, account_name)

	frappe.db.commit()
	click.echo(click.style(f"  Default accounts for company {company_name} successfully set!", fg="green"))
