from __future__ import annotations

import io
import unittest
import zipfile
from hashlib import sha256
from types import SimpleNamespace

from kmu_erp_austria.bmd_export.services.csv_renderer import render_csv
from kmu_erp_austria.bmd_export.services.models import AttachmentPayload
from kmu_erp_austria.bmd_export.services.package import build_zip


class TestBMDCSVAndPackage(unittest.TestCase):
	def profile(self):
		return SimpleNamespace(
			columns=[
				SimpleNamespace(field_name=name)
				for name in ("satzart", "konto", "betrag", "dokument", "text")
			],
			delimiter=";",
			line_ending="CRLF",
			date_format="%d.%m.%Y",
			decimal_separator=",",
			encoding="utf-8-sig",
		)

	def test_csv_has_bom_crlf_decimal_and_sanitized_text(self):
		content = render_csv(
			[{"satzart": 0, "konto": "200000", "betrag": "1200", "text": "A;B\nC"}],
			self.profile(),
		)
		self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
		self.assertIn(b"\r\n", content)
		self.assertIn("1200,00".encode(), content)
		self.assertIn("A,B C".encode(), content)

	def test_zip_is_flat_and_reproducible(self):
		attachment = AttachmentPayload(
			export_name="AR-1.pdf",
			content=b"%PDF-test",
			sha256=sha256(b"%PDF-test").hexdigest(),
			source_file="FILE-1",
			mime_type="application/pdf",
		)
		first = build_zip("buchungen.csv", b"satzart\r\n0\r\n", [attachment])
		second = build_zip("buchungen.csv", b"satzart\r\n0\r\n", [attachment])
		self.assertEqual(first, second)
		with zipfile.ZipFile(io.BytesIO(first)) as archive:
			self.assertEqual(archive.namelist(), ["buchungen.csv", "AR-1.pdf"])
			self.assertTrue(all("/" not in name for name in archive.namelist()))


if __name__ == "__main__":
	unittest.main()
