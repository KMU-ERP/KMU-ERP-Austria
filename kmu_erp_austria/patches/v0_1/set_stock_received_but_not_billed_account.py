import frappe

def execute():
	companies = frappe.get_all("Company", pluck="name")

	for company_name in companies:
		company = frappe.get_doc("Company", company_name)

		account_name = frappe.db.get_value(
			"Account",
			{
				"account_name": "Erhaltene, noch nicht fakturierte Lieferungen",
				"account_number": "3305",
				"company": company.name,
			},
			"name",
		)

		if not account_name:
			parent_account = (
				"3 - Rückstellungen, Verbindlichkeiten, passive Rechnungsabgrenzungsposten - "
				+ company.abbr
			)

			account = frappe.get_doc({
				"doctype": "Account",
				"account_name": "Erhaltene, noch nicht fakturierte Lieferungen",
				"account_number": "3305",
				"company": company.name,
				"account_currency": "EUR",
				"parent_account": parent_account,
				"account_type": "Stock Received But Not Billed",
			}).insert(ignore_permissions=True)

			account_name = account.name

		if not company.stock_received_but_not_billed:
			frappe.db.set_value(
				"Company",
				company.name,
				"stock_received_but_not_billed",
				account_name,
			)

	frappe.db.commit()
