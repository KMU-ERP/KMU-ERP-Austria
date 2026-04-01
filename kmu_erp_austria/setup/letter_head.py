"""
Automatically creates a letter head based on the selected company.
Executed during app setup or changes on the current Company.
"""

import frappe
import click

def import_letter_head():
	companies = frappe.get_all("Company", pluck="name")

	if not companies:
		click.echo(click.style("  NOTE: No company found - letter head skipped", fg="yellow"))
		return

	for company in companies:
		click.echo(f"  Creating letter head for '{company}' ...")
		_create_or_update_letter_head(company)

def _create_or_update_letter_head(company_name) -> str:
	"""
	Creates or updates the letter head for the given company.
	Returns the name of the Letter Head.
	"""
	letter_head_name = f"{company_name} - ERP Austria"

	company = frappe.get_doc("Company", company_name)

	# Load HTML content from template
	click.echo("  Creating letter head content ...")
	html_content = _build_letter_head(company)
	click.echo("  Creating footer content ...")
	footer_content = _build_footer_html(company)

	if frappe.db.exists("Letter Head", letter_head_name):
		click.echo(click.style(f"  NOTE: Letter head for '{company.name}' already exists.", fg="yellow"))
		click.echo("  Reloading content ...")
		letter_head = frappe.get_doc("Letter Head", letter_head_name)
		letter_head.content = html_content
		letter_head.footer = footer_content
		letter_head.save(ignore_permissions=True)
		click.echo(click.style(f"  Letter head for '{company.name}' has been replaced.", fg="green"))
	else:
		is_default = 0

		default_letter_head = frappe.get_all("Letter Head", filters={"is_default": 1})
		if not default_letter_head:
			is_default = 1

		letter_head = frappe.get_doc(
			{
				"doctype": "Letter Head",
				"letter_head_name": letter_head_name,
				"source": "HTML",
				"content": html_content,
				"footer": footer_content,
				"company": company,
				"is_default": is_default
			})
		letter_head.insert(ignore_permissions=True)
		click.echo(click.style(f"  Letter head for '{company.name}' has been created.", fg="green"))

	return letter_head_name

def _build_letter_head(company) -> str:
	"""
	Generates the letter head HTML string from the company data.
	All fields come directly from the Company document.
	"""
	# Fetch address
	address = _get_company_address(company.name)

	# Logo tag (base64 or URL)
	logo_html = _build_logo_html(company)

	# Address lines
	addr_lines = []
	if address:
		if address.address_line1:
			addr_lines.append(address.address_line1)
		if address.address_line2:
			addr_lines.append(address.address_line2)
		city_line = " ".join(filter(None, [address.pincode, address.city]))
		if city_line:
			addr_lines.append(city_line)

	contact_parts = []
	if company.phone_no:
		contact_parts.append(f"Tel: {company.phone_no}")
	if company.email:
		contact_parts.append(f"E-Mail: {company.email}")
	if company.website:
		contact_parts.append(company.website)

	addr_html = "<br>".join(addr_lines)
	contact_html = " &nbsp;|&nbsp; ".join(contact_parts)

	return f"""
<table style="width:100%;border-collapse:collapse;font-family:Helvetica Neue,Arial,sans-serif;">
  <tr>
    <td style="padding:32px 44px 28px;vertical-align:top;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="vertical-align:top;">
            <div style="display:block;width:28px;height:2px;background:#2d4a3e;opacity:0.55;margin-bottom:11px;"></div>
            <div style="font-size:17pt;font-weight:400;color:#1c1c1a;letter-spacing:0.01em;margin:0 0 3px;">
              {company.company_name}
            </div>
            <div style="font-size:8.5pt;font-weight:300;color:#6b6962;line-height:1.85;">
              {addr_html}<br>{contact_html}
            </div>
          </td>
          <td style="text-align:right;vertical-align:top;padding-left:16px;">
            {logo_html}
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="padding:0 44px;">
      <div style="height:1px;background:#2d4a3e;opacity:0.3;"></div>
    </td>
  </tr>
</table>
"""

def _build_footer_html(company) -> str:
	"""
	Generates the letter head footer with two blocks:
	Left: bank details | Right: contact
	"""
	bank_account = _get_default_bank_account(company.name)

	label = '<span style="font-weight:500;color:#5a5a56;display:inline-block;min-width:38px;margin-right:4px;">{}</span>'

	# --- Left block: bank details ---
	bank_lines = []
	if bank_account:
		bank = frappe.get_doc("Bank", bank_account.bank)
		if bank_account.account_name:
			bank_lines.append(f"{label.format('Konto')}{bank_account.account_name}")
		if bank_account.bank:
			bank_lines.append(f"{label.format('Bank')}{bank_account.bank}")
		if bank.swift_number:
			bank_lines.append(f"{label.format('BIC')}{bank.swift_number}")
		if bank_account.iban:
			bank_lines.append(f"{label.format('IBAN')}{bank_account.iban}")

	bank_html = "<br>".join(bank_lines) if bank_lines else ""

	# --- Right block: contact ---
	contact_lines = [f"{label.format(company.name)}"]
	if company.phone_no:
		contact_lines.append(f"{label.format('Tel.')}{company.phone_no}")
	if company.email:
		contact_lines.append(f"{label.format('E-Mail')}{company.email}")
	if company.tax_id:
		contact_lines.append(f"{label.format('UID')}{company.tax_id}")

	contact_html = "<br>".join(contact_lines) if contact_lines else ""

	base = "font-size:7pt;font-weight:300;color:#9a9890;vertical-align:top;line-height:1.9;"

	return f"""
<table style="width:100%;border-collapse:collapse;font-family:Helvetica Neue,Arial,sans-serif;">
  <tr>
    <td style="padding:0 44px;">
      <div style="height:1px;background:#2d4a3e;opacity:0.3;"></div>
    </td>
  </tr>
  <tr>
    <td style="{base}padding:10px 44px 12px;" width="40%">{bank_html}</td>
    <td style="{base}padding:10px 44px 12px;text-align:right;" width="30%">{contact_html}</td>
  </tr>
</table>
"""

def _build_logo_html(company) -> str:
	"""Returns the logo tag — image or initial fallback."""
	if company.company_logo:
		return (
			f'<img src="{company.company_logo}" '
			'style="max-height:90px;max-width:90px;object-fit:contain;" '
			f'alt="{company.company_name} Logo">'
		)
	# Fallback: first letter of the company name
	initial = company.company_name[0].upper()
	return (
		f'<div style="width:54px;height:54px;border:1px solid #e2e0da;'
		'display:flex;align-items:center;justify-content:center;'
		f'font-size:20pt;font-weight:300;color:#2d4a3e;">{initial}</div>'
	)

def _get_company_address(company_name: str):
	"""Fetches the primary address of the company."""
	addr_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Company", "link_name": company_name, "parenttype": "Address"},
		"parent",
	)
	if addr_name:
		return frappe.get_doc("Address", addr_name)
	return None

def _get_default_bank_account(company_name: str):
	"""Fetches the default bank account of the company."""
	bank_acc_name = frappe.db.get_value(
		"Bank Account", {"company": company_name, "is_default": 1}, "name"
	)
	if bank_acc_name:
		return frappe.get_doc("Bank Account", bank_acc_name)
	return None

# --- When company data is changed or new information is added, the letter head is also updated
def on_company_update(doc, method=None):
	_create_or_update_letter_head(doc.name)
