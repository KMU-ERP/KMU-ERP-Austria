import click
import frappe

# ──────────────────────────────────────────────────────────────────────────────
# Österreich – Steuersätze gemäß UStG (Umsatzsteuergesetz)
# ──────────────────────────────────────────────────────────────────────────────
#   20 % – Normalsteuersatz        §10 Abs. 1 UStG
#   13 % – Besonderer Steuersatz   §10 Abs. 3 UStG  (z.B. Beherbergung, Kunst)
#   10 % – Ermäßigter Steuersatz   §10 Abs. 2 UStG  (z.B. Lebensmittel, Bücher)
#    0 % – Steuerfrei              §6 UStG
#
# Deutschland – Steuersätze gemäß UStG (für DE-Firmen oder EU-Geschäfte)
# ──────────────────────────────────────────────────────────────────────────────
#   19 % – Regelsteuersatz         §12 Abs. 1 UStG
#    7 % – Ermäßigter Steuersatz   §12 Abs. 2 UStG
# ──────────────────────────────────────────────────────────────────────────────

AT_SALES_TEMPLATES = [
	{"title": "AT USt 20% – Normalsteuersatz",        "rate": 20, "account_number": "3500"},
	{"title": "AT USt 13% – Besonderer Steuersatz",   "rate": 13, "account_number": "3500"},
	{"title": "AT USt 10% – Ermäßigter Steuersatz",   "rate": 10, "account_number": "3500"},
	{"title": "AT USt 0% – Steuerfrei",               "rate":  0, "account_number": "3500"},
]

AT_PURCHASE_TEMPLATES = [
	{"title": "AT VSt 20% – Normalsteuersatz",        "rate": 20, "account_number": "2500"},
	{"title": "AT VSt 13% – Besonderer Steuersatz",   "rate": 13, "account_number": "2500"},
	{"title": "AT VSt 10% – Ermäßigter Steuersatz",   "rate": 10, "account_number": "2500"},
	{"title": "AT VSt 0% – Steuerfrei",               "rate":  0, "account_number": "2500"},
]

AT_ITEM_TAX_TEMPLATES = [
	{"title": "AT USt 20%", "rate": 20, "account_number": "3500"},
	{"title": "AT USt 13%", "rate": 13, "account_number": "3500"},
	{"title": "AT USt 10%", "rate": 10, "account_number": "3500"},
	{"title": "AT USt 0%",  "rate":  0, "account_number": "3500"},
]

DE_SALES_TEMPLATES = [
	{"title": "DE MwSt 19% – Regelsteuersatz",        "rate": 19, "account_number": "3500"},
	{"title": "DE MwSt 7% – Ermäßigter Steuersatz",   "rate":  7, "account_number": "3500"},
	{"title": "DE MwSt 0% – Steuerfrei",              "rate":  0, "account_number": "3500"},
]

DE_PURCHASE_TEMPLATES = [
	{"title": "DE VSt 19% – Regelsteuersatz",         "rate": 19, "account_number": "2500"},
	{"title": "DE VSt 7% – Ermäßigter Steuersatz",    "rate":  7, "account_number": "2500"},
	{"title": "DE VSt 0% – Steuerfrei",               "rate":  0, "account_number": "2500"},
]

DE_ITEM_TAX_TEMPLATES = [
	{"title": "DE MwSt 19%", "rate": 19, "account_number": "3500"},
	{"title": "DE MwSt 7%",  "rate":  7, "account_number": "3500"},
	{"title": "DE MwSt 0%",  "rate":  0, "account_number": "3500"},
]


def import_tax_templates():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  HINWEIS: Keine Firma gefunden – Steuervorlagen übersprungen.", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Erstelle Steuervorlagen für '{company}' ...")
		_create_templates_for_company(company)
		frappe.db.commit()
		click.echo(click.style(f"  Steuervorlagen für '{company}' erfolgreich erstellt.", fg="green"))


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

	account = _get_account(company, tpl["account_number"])
	if not account:
		return

	doc = frappe.get_doc({
		"doctype": "Sales Taxes and Charges Template",
		"title": tpl["title"],
		"company": company,
		"taxes": [{
			"doctype": "Sales Taxes and Charges",
			"charge_type": "On Net Total",
			"account_head": account,
			"rate": tpl["rate"],
			"description": tpl["title"],
		}],
	})
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_purchase_template(company, tpl):
	if frappe.db.exists("Purchase Taxes and Charges Template", {"title": tpl["title"], "company": company}):
		return

	account = _get_account(company, tpl["account_number"])
	if not account:
		return

	doc = frappe.get_doc({
		"doctype": "Purchase Taxes and Charges Template",
		"title": tpl["title"],
		"company": company,
		"taxes": [{
			"doctype": "Purchase Taxes and Charges",
			"charge_type": "On Net Total",
			"account_head": account,
			"rate": tpl["rate"],
			"description": tpl["title"],
		}],
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
