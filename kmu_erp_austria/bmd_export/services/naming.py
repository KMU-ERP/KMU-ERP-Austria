from __future__ import annotations

import re
import unicodedata
from pathlib import PurePath
from typing import Any

from frappe import _
from jinja2 import StrictUndefined, TemplateError
from jinja2.sandbox import SandboxedEnvironment


MAX_DOCUMENT_NAME_LENGTH = 255
_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]+')
_WHITESPACE = re.compile(r"\s+")


class FilenameTemplateEnvironment(SandboxedEnvironment):
	def is_safe_attribute(self, obj: Any, attr: str, value: Any) -> bool:
		return False

	def is_safe_callable(self, obj: Any) -> bool:
		return False


def _environment() -> FilenameTemplateEnvironment:
	environment = FilenameTemplateEnvironment(undefined=StrictUndefined, autoescape=False)
	environment.globals.clear()
	return environment


def validate_filename_template(template: str) -> None:
	if not template or len(template) > 1000:
		raise ValueError(_("Document filename template must contain between 1 and 1,000 characters."))
	try:
		_environment().parse(template)
	except TemplateError as exc:
		raise ValueError(_("Invalid document filename template: {0}").format(exc)) from exc


def render_filename_stem(template: str, context: dict[str, Any]) -> str:
	validate_filename_template(template)
	primitive_context = {
		key: value if isinstance(value, str | int | float | bool | type(None)) else str(value)
		for key, value in context.items()
	}
	try:
		rendered = _environment().from_string(template).render(primitive_context)
	except TemplateError as exc:
		raise ValueError(_("Unable to render document filename template: {0}").format(exc)) from exc
	return sanitize_stem(rendered)


def sanitize_stem(value: str) -> str:
	value = unicodedata.normalize("NFC", value or "")
	value = _UNSAFE_FILENAME_CHARS.sub("-", value)
	value = _WHITESPACE.sub(" ", value).strip(" .-")
	value = value.replace("..", ".")
	if not value or value in {".", ".."}:
		raise ValueError(_("Document filename template rendered an empty or unsafe filename."))
	return value


def safe_extension(filename: str) -> str:
	name = PurePath(filename or "").name
	suffix = PurePath(name).suffix
	if not suffix or not re.fullmatch(r"\.[A-Za-z0-9]{1,10}", suffix):
		raise ValueError(_("Attachment has no safe file extension."))
	return suffix


def unique_export_filename(
	stem: str,
	extension: str,
	used_names: set[str],
	encoding: str,
) -> str:
	for index in range(1, 10000):
		suffix = "" if index == 1 else f"_{index:02d}"
		available = MAX_DOCUMENT_NAME_LENGTH - len(extension) - len(suffix)
		candidate = f"{stem[:available].rstrip(' .-')}{suffix}{extension}"
		try:
			candidate.encode(encoding)
		except UnicodeEncodeError as exc:
			raise ValueError(
				_("Export filename {0} cannot be represented using {1}.").format(
					repr(candidate), encoding
				)
			) from exc
		key = candidate.casefold()
		if key not in used_names:
			used_names.add(key)
			return candidate
	raise ValueError(_("Unable to create a collision-free export filename."))
