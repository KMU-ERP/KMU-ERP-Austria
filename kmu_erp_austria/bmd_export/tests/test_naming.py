from __future__ import annotations

import unittest

from kmu_erp_austria.bmd_export.services.naming import (
	render_filename_stem,
	safe_extension,
	unique_export_filename,
)


class TestBMDDocumentNaming(unittest.TestCase):
	def test_custom_jinja_renames_test_pdf(self):
		stem = render_filename_stem(
			"{{ invoice_number }}-{{ party_name }}",
			{"invoice_number": "AR-2026-0042", "party_name": "Musterkunde"},
		)
		name = unique_export_filename(stem, safe_extension("test.pdf"), set(), "utf-8-sig")
		self.assertEqual(name, "AR-2026-0042-Musterkunde.pdf")

	def test_collisions_are_deterministic(self):
		used = set()
		self.assertEqual(unique_export_filename("AR-1", ".pdf", used, "utf-8-sig"), "AR-1.pdf")
		self.assertEqual(unique_export_filename("AR-1", ".pdf", used, "utf-8-sig"), "AR-1_02.pdf")

	def test_path_components_are_removed(self):
		self.assertEqual(render_filename_stem("../../{{ name }}", {"name": "A/B"}), "A-B")

	def test_unknown_jinja_variable_blocks_preview(self):
		with self.assertRaises(ValueError):
			render_filename_stem("{{ unknown_value }}", {})


if __name__ == "__main__":
	unittest.main()
