import frappe
import click

def import_default_settings():
	click.echo("  Importing default settings...")
	frappe.db.set_single_value("System Settings", "date_format", "dd.mm.yyyy")
	frappe.db.set_single_value("System Settings", "number_format", "#.###,##")
	frappe.db.commit()
	click.echo(click.style("  Default settings imported.", fg="green"))
