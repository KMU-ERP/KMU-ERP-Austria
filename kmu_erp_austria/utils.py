import frappe
from bs4 import BeautifulSoup
import re

@frappe.whitelist(allow_guest=False)
def get_tax_breakup(other_charges_calculation):
	soup = BeautifulSoup(other_charges_calculation, 'html.parser')
	rows = soup.find_all('tr')
	tax_groups = {}
	for row in rows:
		cells = row.find_all('td')
		if len(cells) >= 3:
			tax_cell = cells[2].get_text(strip=True)
			rate_match = re.search(r'\(([\d.]+)%\)', tax_cell)
			amount_match = re.search(r'€\s*([\d,]+)', tax_cell)
			if rate_match and amount_match:
				rate = rate_match.group(1)
				amount = float(amount_match.group(1).replace(',', '.'))
				tax_groups[rate] = tax_groups.get(rate, 0) + amount
	return tax_groups
