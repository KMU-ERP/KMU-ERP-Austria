from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase


@unittest.skipUnless(getattr(frappe.local, "site", None), "requires an initialized Frappe site")
class TestBMDControllers(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit=1)[0]

	def make_batch(self, **values):
		return frappe.get_doc(
			{
				"doctype": "BMD Export Batch",
				"company": self.company,
				"from_date": "2026-01-01",
				"to_date": "2026-01-31",
				"include_sales_invoices": 1,
				"include_purchase_invoices": 1,
				**values,
			}
		).insert()

	def test_insert_cannot_spoof_completed_status_or_requester(self):
		batch = self.make_batch(status="Completed", requested_by="Guest")
		self.assertEqual(batch.status, "Draft")
		self.assertEqual(batch.requested_by, "Administrator")

	def test_status_changes_require_workflow_and_follow_state_machine(self):
		batch = self.make_batch()
		batch.status = "Validating"
		with self.assertRaises(frappe.ValidationError):
			batch.save()
		batch.reload()
		batch.transition("Validating")
		self.assertEqual(batch.status, "Validating")
		batch.transition("Invalid")
		self.assertEqual(batch.status, "Invalid")
		with self.assertRaises(frappe.ValidationError):
			batch.transition("Completed")

	def test_app_standard_profile_is_immutable(self):
		profile = frappe.get_doc("BMD Export Profile", "BMD NTCS Standard")
		profile.delimiter = ","
		with self.assertRaises(frappe.ValidationError):
			profile.save()

	def test_user_cannot_create_another_standard_profile(self):
		profile = frappe.get_doc(
			{
				"doctype": "BMD Export Profile",
				"profile_name": "Unauthorized Standard Profile",
				"is_active": 1,
				"is_standard": 1,
				"delimiter": ";",
				"encoding": "utf-8-sig",
				"decimal_separator": ".",
				"date_format": "%d.%m.%Y",
				"line_ending": "CRLF",
				"money_precision": 2,
				"tax_rate_precision": 3,
				"exchange_rate_precision": 8,
				"quantity_precision": 6,
				"columns": [{"field_name": "text"}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			profile.insert()
