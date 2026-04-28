import frappe
import click

DEFAULT_ACCOUNTS = [
	{
		"field_name": "default_cash_account",
		"account_name": "2700 - Kassenbestand in Euro TC"
	},
	{
		"field_name": "default_receivable_account",
		"account_name": "2000 - Forderungen aus Lieferungen und Leistungen Inland - TC"
	},
	{
		"field_name": "default_payable_account",
		"account_name": "3300 - Verbindlichkeiten aus Lieferungen und Leistungen Inland - TC"
	},
	{
		"field_name": "default_expense_account",
		"account_name": "5050 - Wareneinsatz - TC"
	},
	{
		"field_name": "default_income_account",
		"account_name": "4000 - Erlöse 20 % - TC"
	},
	{
		"field_name": "default_discount_account",
		"account_name": "4480 - Kundenboni und Rabatte 20 % - TC"
	},
	{
		"field_name": "exchange_gain_loss_account",
		"account_name": "7850 - Kursdifferenzen - TC"
	},
]

def set_default_accounts_to_company(company_name):
	click.echo(f"  Setting default accounts to company {company_name} ...")

	if not frappe.db.exists("Company", company_name):
		click.echo(click.style(f"  Company {company_name} doesn't exist", fg="red"))
		return

	for account in DEFAULT_ACCOUNTS:
		field_name = account["field_name"]
		account_name = account["account_name"]

		frappe.db.set_value("Company", company_name, field_name, account_name)

	frappe.db.commit()
	click.echo(click.style(f"  Default accounts for company {company_name} successfully set!", fg="green"))
