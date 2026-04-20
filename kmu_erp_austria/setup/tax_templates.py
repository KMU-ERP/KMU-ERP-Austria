import click
import frappe

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# Austria – VAT rates according to UStG (VAT Act)
# ─────────────────────────────────────────────────────────────────────────────────────────────────
#   20 % – Standard rate (Normalsteuersatz)         §10 para. 1 UStG
#   13 % – Special rate (Besonderer Steuersatz)     §10 para. 3 UStG  (e.g. accommodation, art)
#   10 % – Reduced rate (Ermäßigter Steuersatz)     §10 para. 2 UStG  (e.g. food, books)
#    0 % – Tax exempt (Steuerfrei)             		§6 UStG
#
# Germany – VAT rates according to UStG (for DE companies or EU transactions)
# ─────────────────────────────────────────────────────────────────────────────────────────────────
#   19 % – Standard rate (Regelsteuersatz)          §12 para. 1 UStG
#    7 % – Reduced rate (Ermäßigter Steuersatz)     §12 para. 2 UStG
# ─────────────────────────────────────────────────────────────────────────────────────────────────

AT_SALES_TEMPLATES = [
	{"title": "Österreich - Verkaufssteuern", "rates": [
		{"rate": 20, "account_number": "35020"},
		{"rate": 13, "account_number": "35013"},
		{"rate": 10, "account_number": "35010"},
		{"rate":  0, "account_number": "35000"},
	]},
]

AT_PURCHASE_TEMPLATES = [
	{"title": "Österreich - Einkaufssteuern", "rates": [
		{"rate": 20, "account_number": "25020"},
		{"rate": 13, "account_number": "25013"},
		{"rate": 10, "account_number": "25010"},
		{"rate":  0, "account_number": "25000"},
	]},
]

AT_ITEM_TAX_TEMPLATES = [
	{"title": "AT USt 20%", "rate": 20, "account_number": "35020"},
	{"title": "AT USt 13%", "rate": 13, "account_number": "35013"},
	{"title": "AT USt 10%", "rate": 10, "account_number": "35010"},
	{"title": "AT USt 0%",  "rate":  0, "account_number": "35000"},
]

DE_SALES_TEMPLATES = [
	{"title": "Deutschland - Verkaufssteuern", "rates": [
		{"rate": 19, "account_number": "35019"},
	    {"rate":  7, "account_number": "35007"},
	    {"rate":  0, "account_number": "35000"},
	]},
]

DE_PURCHASE_TEMPLATES = [
	{"title": "Deutschland - Einkaufssteuern", "rates": [
		{"rate": 19, "account_number": "25019"},
		{"rate":  7, "account_number": "25007"},
		{"rate":  0, "account_number": "25000"},
	]},
]

DE_ITEM_TAX_TEMPLATES = [
	{"title": "DE MwSt 19%", "rate": 19, "account_number": "35019"},
	{"title": "DE MwSt 7%",  "rate":  7, "account_number": "35007"},
	{"title": "DE MwSt 0%",  "rate":  0, "account_number": "35000"},
]


def import_tax_templates():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  NOTE: No company found – tax templates skipped.", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Creating tax templates for '{company}' ...")
		_create_templates_for_company(company)
		click.echo(click.style(f"  Tax templates for '{company}' successfully created.", fg="green"))


def _create_templates_for_company(company):
	for tpl in AT_SALES_TEMPLATES:
		_create_sales_template(company, tpl)

	for tpl in AT_PURCHASE_TEMPLATES:
		_create_purchase_template(company, tpl)

	for tpl in AT_ITEM_TAX_TEMPLATES:
		_create_item_tax_template(company, tpl)

	for tpl in DE_SALES_TEMPLATES:
		_create_sales_template(company, tpl)

	for tpl in DE_PURCHASE_TEMPLATES:
		_create_purchase_template(company, tpl)

	for tpl in DE_ITEM_TAX_TEMPLATES:
		_create_item_tax_template(company, tpl)


def _get_account(company, account_number):
	return frappe.db.get_value("Account", {"company": company, "account_number": account_number}, "name")


def _create_sales_template(company, tpl):
	if frappe.db.exists("Sales Taxes and Charges Template", {"title": tpl["title"], "company": company}):
		return

	tax_rows = []
	for rate_entry in tpl["rates"]:
		account = _get_account(company, rate_entry["account_number"])
		if not account:
			continue
		tax_rows.append({
			"doctype": "Sales Taxes and Charges",
			"charge_type": "On Net Total",
			"account_head": account,
			"rate": 0,
			"description": tpl["title"],
		})

	if not tax_rows:
		return

	doc = frappe.get_doc({
		"doctype": "Sales Taxes and Charges Template",
		"title": tpl["title"],
		"company": company,
		"taxes": tax_rows,
	})
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_purchase_template(company, tpl):
	if frappe.db.exists("Purchase Taxes and Charges Template", {"title": tpl["title"], "company": company}):
		return

	tax_rows = []
	for rate_entry in tpl["rates"]:
		account = _get_account(company, rate_entry["account_number"])
		if not account:
			continue
		tax_rows.append({
			"doctype": "Purchase Taxes and Charges",
			"charge_type": "On Net Total",
			"account_head": account,
			"rate": 0,
			"description": tpl["title"],
		})

	if not tax_rows:
		return

	doc = frappe.get_doc({
		"doctype": "Purchase Taxes and Charges Template",
		"title": tpl["title"],
		"company": company,
		"taxes": tax_rows,
	})
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_item_tax_template(company, tpl):
	if frappe.db.exists("Item Tax Template", {"title": tpl["title"], "company": company}):
		return

	account = _get_account(company, tpl["account_number"])
	if not account:
		return

	doc = frappe.get_doc({
		"doctype": "Item Tax Template",
		"title": tpl["title"],
		"company": company,
		"taxes": [{
			"doctype": "Item Tax Template Detail",
			"tax_type": account,
			"tax_rate": tpl["rate"],
		}],
	})
	doc.flags.ignore_permissions = True
	doc.insert()
