from __future__ import annotations

import hashlib
import io
import re
import zipfile

from frappe import _

from kmu_erp_austria.bmd_export.services.models import AttachmentPayload


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256(content: bytes) -> str:
	return hashlib.sha256(content).hexdigest()


def _zip_info(filename: str) -> zipfile.ZipInfo:
	if (
		not filename
		or filename in {".", ".."}
		or filename.startswith(("/", "\\"))
		or "/" in filename
		or "\\" in filename
		or re.search(r'[:\x00-\x1f\x7f]', filename)
	):
		raise ValueError(_("ZIP entry {0} must be a plain filename.").format(repr(filename)))
	info = zipfile.ZipInfo(filename=filename, date_time=ZIP_TIMESTAMP)
	info.compress_type = zipfile.ZIP_DEFLATED
	info.create_system = 3
	info.external_attr = 0o100644 << 16
	return info


def build_zip(
	csv_filename: str,
	csv_content: bytes,
	attachments: list[AttachmentPayload],
) -> bytes:
	names = [csv_filename, *(attachment.export_name for attachment in attachments)]
	if len({name.casefold() for name in names}) != len(names):
		raise ValueError(_("ZIP contains duplicate filenames."))
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
		archive.writestr(_zip_info(csv_filename), csv_content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
		for attachment in sorted(attachments, key=lambda item: item.export_name.casefold()):
			archive.writestr(
				_zip_info(attachment.export_name),
				attachment.content,
				compress_type=zipfile.ZIP_DEFLATED,
				compresslevel=9,
			)
	return buffer.getvalue()
