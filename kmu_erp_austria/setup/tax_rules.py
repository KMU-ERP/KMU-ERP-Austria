import click
import frappe

# ──────────────────────────────────────────────────────────────────────────────
# Tax Rules – automatische Steuervorlagenwahl
#
# Logik: Je mehr Felder ausgefüllt, desto spezifischer die Regel.
# Leere Felder = Wildcard (gilt für alle Werte).
# Bei gleicher Spezifität entscheidet die Priorität (höher = bevorzugt).
#
# Inland (Österreich):
#   Sales    + Austria  → AT USt 20% – Normalsteuersatz
#   Purchase + Austria  → AT VSt 20% – Normalsteuersatz
#
# EU-Ausland (Deutschland):
#   Sales    + Germany  → DE MwSt 19% – Regelsteuersatz
#   Purchase + Germany  → DE VSt 19% – Regelsteuersatz
# ──────────────────────────────────────────────────────────────────────────────

TAX_RULES = [
	{
		"name":                 "Verkauf AT USt 20% – Normalsteuersatz",
		"tax_type":             "Sales",
		"billing_country":      "Austria",
		"sales_tax_template":   "AT USt 20% – Normalsteuersatz",
		"priority":             1,
	},
	{
		"name":                 "Einkauf AT VSt 20% – Normalsteuersatz",
		"tax_type":             "Purchase",
		"billing_country":      "Austria",
		"purchase_tax_template": "AT VSt 20% – Normalsteuersatz",
		"priority":             1,
	},
	{
		"name":                 "Verkauf DE MwSt 19% – Regelsteuersatz",
		"tax_type":             "Sales",
		"billing_country":      "Germany",
		"sales_tax_template":   "DE MwSt 19% – Regelsteuersatz",
		"priority":             1,
	},
	{
		"name":                 "Einkauf DE VSt 19% – Regelsteuersatz",
		"tax_type":             "Purchase",
		"billing_country":      "Germany",
		"purchase_tax_template": "DE VSt 19% – Regelsteuersatz",
		"priority":             1,
	},
]


def import_tax_rules():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  HINWEIS: Keine Firma gefunden – Steuerregeln übersprungen.", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Erstelle Steuerregeln für '{company}' ...")
		_create_rules_for_company(company)
		frappe.db.commit()
		click.echo(click.style(f"  Steuerregeln für '{company}' erfolgreich erstellt.", fg="green"))


def _create_rules_for_company(company):
	for rule in TAX_RULES:
		template_title = rule.get("sales_tax_template") or rule.get("purchase_tax_template")
		template_name = _get_template_name(company, rule["tax_type"], template_title)

		if not template_name:
			click.echo(click.style(
				f"    Vorlage '{template_title}' nicht gefunden – Tax Rule übersprungen.",
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
