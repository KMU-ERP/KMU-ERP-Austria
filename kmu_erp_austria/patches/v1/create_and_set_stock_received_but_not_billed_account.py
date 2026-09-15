import frappe

def execute():
	account_exists = frappe.db.exists({"doctype": "Account", "account_name": "Erhaltene, noch nicht fakturierte Lieferungen"})

	if account_exists:
		return

	companies = frappe.get_all("Company")

	for company in companies:
		company = frappe.get_doc("Company", company.name)

		account = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Erhaltene, noch nicht fakturierte Lieferungen",
			"account_number": "3305",
			"company": company.name,
			"account_currency": "EUR",
			"parent_account": "3 - Rückstellungen, Verbindlichkeiten, passive Rechnungsabgrenzungsposten - " + company.abbr,
			"account_type": "Stock Received But Not Billed",
		}).insert(ignore_permissions=True)

		frappe.db.set_value("Company", company.name, "stock_received_but_not_billed", account.name)

	frappe.db.commit()
