import frappe
import click

def import_default_settings():
	click.echo("  Importing default settings...")
	frappe.db.set_single_value("System Settings", "date_format", "dd.mm.yyyy")
	frappe.db.set_single_value("System Settings", "number_format", "#.###,##")
	frappe.db.set_single_value("System Settings", "currency_precision", "2")
	frappe.db.set_single_value("System Settings", "rounding_method", "Commercial Rounding")
	frappe.db.set_single_value("Accounts Settings", "round_row_wise_tax", 1)
	_set_default_print_formats()
	frappe.db.commit()
	click.echo(click.style("  Default settings imported.", fg="green"))

def _set_default_print_formats():
	defaults = {
		"Quotation": "Angebot - KMU ERP Austria",
		"Sales Invoice": "Ausgangsrechnung - KMU ERP Austria",
		"Delivery Note": "Lieferschein - KMU ERP Austria",
		"Sales Order": "Auftragsbestätigung - KMU ERP Austria",
	}
	for doctype, print_format in defaults.items():
		if frappe.db.exists("Print Format", print_format):
			frappe.db.set_value("DocType", doctype, "default_print_format", print_format)
