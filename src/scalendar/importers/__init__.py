"""Input adapters for supported spreadsheet and image workflows."""

from .xlsx import ExcelImportError, ExcelImportResult, import_xlsx

__all__ = ["ExcelImportError", "ExcelImportResult", "import_xlsx"]
