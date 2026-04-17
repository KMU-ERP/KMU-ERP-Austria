import click
import frappe

# ──────────────────────────────────────────────────────────────────────────────
# Tax Rules – automatic tax template selection
#
# Logic: The more fields filled in, the more specific the rule.
# Empty fields = wildcard (applies to all values).
# At equal specificity, priority decides (higher = preferred).
#
# Domestic (Austria):
#   Sales    + Austria  → AT USt 20% – Normalsteuersatz
#   Purchase + Austria  → AT VSt 20% – Normalsteuersatz
#
# EU abroad (Germany):
#   Sales    + Germany  → DE MwSt 19% – Regelsteuersatz
#   Purchase + Germany  → DE VSt 19% – Regelsteuersatz
# ──────────────────────────────────────────────────────────────────────────────

TAX_RULES = [
	{
		"name":                 "Österreich - Verkaufssteuerregel",
		"tax_type":             "Sales",
		"billing_country":      "Austria",
		"tax_category":         "Österreich",
		"sales_tax_template":   "Österreich - Verkauf",
		"priority":             1,
	},
	{
		"name":                 "Österreich - Einkaufssteuerregel",
		"tax_type":             "Purchase",
		"billing_country":      "Austria",
		"tax_category":         "Österreich",
		"purchase_tax_template": "Österreich - Einkauf",
		"priority":             1,
	},
	{
		"name":                 "Deutschland - Verkaufssteuerregel",
		"tax_type":             "Sales",
		"billing_country":      "Germany",
		"tax_category":         "Deutschland",
		"sales_tax_template":   "Deutschland - Verkauf",
		"priority":             1,
	},
	{
		"name":                 "Deutschland - Einkaufssteuerregel",
		"tax_type":             "Purchase",
		"billing_country":      "Germany",
		"tax_category":         "Deutschland",
		"purchase_tax_template": "Deutschland - Einkauf",
		"priority":             1,
	},
]


def import_tax_rules():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  NOTE: No company found – tax rules skipped.", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Creating tax rules for '{company}' ...")
		_create_rules_for_company(company)
		click.echo(click.style(f"  Tax rules for '{company}' successfully created.", fg="green"))


def _create_rules_for_company(company):
	for rule in TAX_RULES:
		template_title = rule.get("sales_tax_template") or rule.get("purchase_tax_template")
		template_name = _get_template_name(company, rule["tax_type"], template_title)

		if not template_name:
			click.echo(click.style(
				f"    Template '{template_title}' not found – tax rule skipped.",
				fg="yellow"
			))
			continue

		sales_template = template_name if rule["tax_type"] == "Sales" else None
		purchase_template = template_name if rule["tax_type"] == "Purchase" else None

		if _rule_exists(company, rule, sales_template, purchase_template):
			continue

		doc = frappe.get_doc({
			"doctype":                "Tax Rule",
			"tax_type":               rule["tax_type"],
			"company":                company,
			"billing_country":        rule.get("billing_country"),
			"sales_tax_template":     sales_template,
			"purchase_tax_template":  purchase_template,
			"priority":               rule.get("priority", 1),
		})
		doc.flags.ignore_permissions = True
		doc.insert()

		frappe.rename_doc("Tax Rule", doc.name, rule["name"], force=True, show_alert=False)


def _get_template_name(company, tax_type, title):
	if tax_type == "Sales":
		return frappe.db.get_value(
			"Sales Taxes and Charges Template", {"title": title, "company": company}, "name"
		)
	return frappe.db.get_value(
		"Purchase Taxes and Charges Template", {"title": title, "company": company}, "name"
	)


def _rule_exists(company, rule, sales_template, purchase_template):
	return frappe.db.exists("Tax Rule", rule["name"])
