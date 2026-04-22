import frappe
import click

def create_company_address(args, company_name):
	street = args.get("address_line1")
	city = args.get("city")
	pincode = args.get("pincode")

	click.echo(f"  Creating company address for '{company_name}' ...")
	if not (company_name and (street or city or pincode)):
		click.echo(click.style(f"  NOTE: Skipping company address creation for '{company_name}' due to missing required fields.", fg="yellow"))
		return

	address = frappe.new_doc("Address")
	address.address_title = company_name
	address.address_type = "Billing"
	address.address_line1 = street or ""
	address.city = city or ""
	address.pincode = pincode or ""
	address.country = args.get("country", "")
	address.is_your_company_address = 1
	address.append("links", {
		"link_doctype": "Company",
		"link_name": company_name
	})
	address.save(ignore_permissions=True)
	click.echo(click.style(f"  Company address for '{company_name}' created successfully.", fg="green"))
