import click
import frappe

# ──────────────────────────────────────────────────────────────────────────────
# Payment terms for Austria and Germany
#
# Structure:
#   Payment Term    – single payment condition (due date, discount)
#   Payment Terms Template – template with one or more Payment Terms
#
# Common terms in AT/DE:
#   Immediate payment (Sofortzahlung)     – due upon receipt of invoice
#   7 / 14 / 30 / 60 days 				  – standard net due dates
#   Advance payment (Vorauskasse)         – prepayment before delivery
#   End of month (Ende Monatszahlung)     – due at end of invoice month
#   30 days after end of month
#   14 days 2% discount / 30 days net  	  – standard discount AT/DE
#   10 days 2% discount / 30 days net
# ──────────────────────────────────────────────────────────────────────────────

PAYMENT_TERMS = [
	{
		"payment_term_name":          "Sofortzahlung",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                0,
		"description":                "Zahlung sofort fällig",
	},
	{
		"payment_term_name":          "7 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                7,
		"description":                "Zahlung innerhalb von 7 Tagen",
	},
	{
		"payment_term_name":          "14 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                14,
		"description":                "Zahlung innerhalb von 14 Tagen",
	},
	{
		"payment_term_name":          "30 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                30,
		"description":                "Zahlung innerhalb von 30 Tagen",
	},
	{
		"payment_term_name":          "60 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                60,
		"description":                "Zahlung innerhalb von 60 Tagen",
	},
	{
		"payment_term_name":          "Vorkasse",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                0,
		"description":                "Vorauszahlung vor Lieferung",
	},
	{
		"payment_term_name":          "Monatsende",
		"invoice_portion":            100,
		"due_date_based_on":          "Month(s) after the end of the invoice month",
		"credit_months":              0,
		"description":                "Zahlung bis Ende des Rechnungsmonats",
	},
	{
		"payment_term_name":          "30 Tage nach Monatsende",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after the end of the invoice month",
		"credit_days":                30,
		"description":                "Zahlung 30 Tage nach Monatsende",
	},
	{
		"payment_term_name":          "14 Tage 2% Skonto / 30 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                30,
		"discount_type":              "Percentage",
		"discount":                   2,
		"discount_validity_based_on": "Day(s) after invoice date",
		"discount_validity":          14,
		"description":                "2% Skonto bei Zahlung innerhalb von 14 Tagen, sonst 30 Tage netto",
	},
	{
		"payment_term_name":          "10 Tage 2% Skonto / 30 Tage netto",
		"invoice_portion":            100,
		"due_date_based_on":          "Day(s) after invoice date",
		"credit_days":                30,
		"discount_type":              "Percentage",
		"discount":                   2,
		"discount_validity_based_on": "Day(s) after invoice date",
		"discount_validity":          10,
		"description":                "2% Skonto bei Zahlung innerhalb von 10 Tagen, sonst 30 Tage netto",
	},
]


def import_payment_terms():
	click.echo("  Creating payment terms ...")

	for term in PAYMENT_TERMS:
		_create_payment_term(term)
		_create_payment_terms_template(term)

	click.echo(click.style("  Payment terms successfully created.", fg="green"))


def _create_payment_term(term):
	if frappe.db.exists("Payment Term", term["payment_term_name"]):
		return

	doc = frappe.get_doc({"doctype": "Payment Term", **term})
	doc.flags.ignore_permissions = True
	doc.insert()


def _create_payment_terms_template(term):
	name = term["payment_term_name"]

	if frappe.db.exists("Payment Terms Template", name):
		return

	doc = frappe.get_doc({
		"doctype":       "Payment Terms Template",
		"template_name": name,
		"terms": [{
			"doctype":           "Payment Terms Template Detail",
			"payment_term":      name,
			"invoice_portion":   term["invoice_portion"],
			"due_date_based_on": term["due_date_based_on"],
			"credit_days":       term.get("credit_days", 0),
			"credit_months":     term.get("credit_months", 0),
			"discount_type":     term.get("discount_type", "Percentage"),
			"discount":          term.get("discount", 0),
			"discount_validity_based_on": term.get("discount_validity_based_on", "Day(s) after invoice date"),
			"discount_validity": term.get("discount_validity", 0),
		}],
	})
	doc.flags.ignore_permissions = True
	doc.insert()
