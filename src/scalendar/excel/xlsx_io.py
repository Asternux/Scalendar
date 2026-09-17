"""Minimal OOXML reader/writer used by the XLSX exchange feature.

The application only needs plain values, a few sheets, basic styles, freeze
panes and filters. Keeping this boundary small avoids making the project
depend on a spreadsheet editor library at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re
from typing import Any, Iterable
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"x": MAIN_NS, "r": REL_NS, "pr": PACKAGE_REL_NS}


class XlsxError(ValueError):
    """A safe, user-facing category for malformed XLSX files."""

    def __init__(self, code: str, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


def _tag(name: str) -> str:
    return f"{{{MAIN_NS}}}{name}"


def _relationship_tag(name: str) -> str:
    return f"{{{PACKAGE_REL_NS}}}{name}"


def _column_name(number: int) -> str:
    value = number
    letters = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters or "A"


def _column_number(letters: str) -> int:
    result = 0
    for char in letters.upper():
        result = result * 26 + ord(char) - 64
    return result


def _cell_ref(row: int, column: int) -> str:
    return f"{_column_name(column)}{row}"


def _xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _string_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


@dataclass(frozen=True)
class XlsxSheet:
    name: str
    rows: list[list[Any]]
    widths: list[float]
    header_rows: tuple[int, ...] = (1,)
    autofilter: bool = False


class XlsxWriter:
    """Write a compact, ordinary XLSX workbook accepted by Excel and WPS."""

    def __init__(self) -> None:
        self._sheets: list[XlsxSheet] = []

    def add_sheet(
        self,
        name: str,
        rows: Iterable[Iterable[Any]],
        *,
        widths: Iterable[float] = (),
        header_rows: Iterable[int] = (1,),
        autofilter: bool = False,
    ) -> None:
        materialized = [list(row) for row in rows]
        self._sheets.append(
            XlsxSheet(
                name=name,
                rows=materialized,
                widths=list(widths),
                header_rows=tuple(header_rows),
                autofilter=autofilter,
            )
        )

    def save(self, path: str | Path) -> Path:
        if not self._sheets:
            raise XlsxError("empty_workbook", "工作簿没有可导出的工作表。")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        strings: list[str] = []
        string_ids: dict[str, int] = {}
        for sheet in self._sheets:
            for row in sheet.rows:
                for value in row:
                    if isinstance(value, (str, date, datetime)):
                        text = _string_value(value)
                        if text not in string_ids:
                            string_ids[text] = len(strings)
                            strings.append(text)

        content_types = ET.Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
        ET.SubElement(content_types, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
        ET.SubElement(content_types, "Default", {"Extension": "xml", "ContentType": "application/xml"})
        ET.SubElement(content_types, "Override", {"PartName": "/xl/workbook.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"})
        ET.SubElement(content_types, "Override", {"PartName": "/xl/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"})
        ET.SubElement(content_types, "Override", {"PartName": "/xl/sharedStrings.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"})
        for index in range(1, len(self._sheets) + 1):
            ET.SubElement(content_types, "Override", {"PartName": f"/xl/worksheets/sheet{index}.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"})

        package_rels = ET.Element("Relationships", {"xmlns": PACKAGE_REL_NS})
        ET.SubElement(package_rels, "Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "xl/workbook.xml"})

        workbook = ET.Element("workbook", {"xmlns": MAIN_NS, "xmlns:r": REL_NS})
        ET.SubElement(workbook, "workbookPr", {"defaultThemeVersion": "164011"})
        sheets_element = ET.SubElement(workbook, "sheets")
        workbook_rels = ET.Element("Relationships", {"xmlns": PACKAGE_REL_NS})
        for index, sheet in enumerate(self._sheets, start=1):
            ET.SubElement(sheets_element, "sheet", {"name": sheet.name, "sheetId": str(index), f"{{{REL_NS}}}id": f"rId{index}"})
            ET.SubElement(workbook_rels, "Relationship", {"Id": f"rId{index}", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": f"worksheets/sheet{index}.xml"})
        ET.SubElement(workbook_rels, "Relationship", {"Id": f"rId{len(self._sheets) + 1}", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "Target": "styles.xml"})
        ET.SubElement(workbook_rels, "Relationship", {"Id": f"rId{len(self._sheets) + 2}", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings", "Target": "sharedStrings.xml"})

        shared_strings = ET.Element("sst", {"xmlns": MAIN_NS, "count": str(len(strings)), "uniqueCount": str(len(strings))})
        for text in strings:
            item = ET.SubElement(shared_strings, "si")
            ET.SubElement(item, "t").text = text

        styles = self._styles_xml()
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", _xml_bytes(content_types))
            archive.writestr("_rels/.rels", _xml_bytes(package_rels))
            archive.writestr("xl/workbook.xml", _xml_bytes(workbook))
            archive.writestr("xl/_rels/workbook.xml.rels", _xml_bytes(workbook_rels))
            archive.writestr("xl/sharedStrings.xml", _xml_bytes(shared_strings))
            archive.writestr("xl/styles.xml", _xml_bytes(styles))
            for index, sheet in enumerate(self._sheets, start=1):
                archive.writestr(f"xl/worksheets/sheet{index}.xml", _xml_bytes(self._sheet_xml(sheet, string_ids)))
        return target

    @staticmethod
    def _styles_xml() -> ET.Element:
        styles = ET.Element("styleSheet", {"xmlns": MAIN_NS})
        ET.SubElement(styles, "numFmts", {"count": "0"})
        fonts = ET.SubElement(styles, "fonts", {"count": "2"})
        ET.SubElement(fonts, "font")
        bold_font = ET.SubElement(fonts, "font")
        ET.SubElement(bold_font, "b")
        fills = ET.SubElement(styles, "fills", {"count": "2"})
        ET.SubElement(fills, "fill").append(ET.Element("patternFill", {"patternType": "none"}))
        header_fill = ET.SubElement(fills, "fill")
        ET.SubElement(header_fill, "patternFill", {"patternType": "solid"}).append(ET.Element("fgColor", {"rgb": "FF4F81BD"}))
        borders = ET.SubElement(styles, "borders", {"count": "2"})
        ET.SubElement(borders, "border")
        border = ET.SubElement(borders, "border")
        for side in ("left", "right", "top", "bottom"):
            ET.SubElement(border, side, {"style": "thin"}).append(ET.Element("color", {"rgb": "FFD9E2F3"}))
        cell_style_xfs = ET.SubElement(styles, "cellStyleXfs", {"count": "1"})
        ET.SubElement(cell_style_xfs, "xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0"})
        cell_xfs = ET.SubElement(styles, "cellXfs", {"count": "4"})
        ET.SubElement(cell_xfs, "xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0", "xfId": "0"})
        ET.SubElement(cell_xfs, "xf", {"numFmtId": "0", "fontId": "1", "fillId": "1", "borderId": "1", "applyAlignment": "1", "xfId": "0"}).append(ET.Element("alignment", {"horizontal": "center", "vertical": "center", "wrapText": "1"}))
        ET.SubElement(cell_xfs, "xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "1", "applyAlignment": "1", "xfId": "0"}).append(ET.Element("alignment", {"vertical": "center"}))
        ET.SubElement(cell_xfs, "xf", {"numFmtId": "1", "fontId": "0", "fillId": "0", "borderId": "1", "applyAlignment": "1", "xfId": "0"}).append(ET.Element("alignment", {"horizontal": "right", "vertical": "center"}))
        ET.SubElement(styles, "cellStyles", {"count": "1"}).append(ET.Element("cellStyle", {"name": "Normal", "xfId": "0", "builtinId": "0"}))
        ET.SubElement(styles, "dxfs", {"count": "0"})
        ET.SubElement(styles, "tableStyles", {"count": "0", "defaultTableStyle": "TableStyleMedium2", "defaultPivotStyle": "PivotStyleMedium9"})
        return styles

    @staticmethod
    def _sheet_xml(sheet: XlsxSheet, string_ids: dict[str, int]) -> ET.Element:
        root = ET.Element("worksheet", {"xmlns": MAIN_NS, "xmlns:r": REL_NS})
        views = ET.SubElement(root, "sheetViews")
        view = ET.SubElement(views, "sheetView", {"workbookViewId": "0", "showGridLines": "0"})
        freeze = max(sheet.header_rows, default=1)
        ET.SubElement(view, "pane", {"ySplit": str(freeze), "topLeftCell": f"A{freeze + 1}", "activePane": "bottomLeft", "state": "frozen"})
        ET.SubElement(root, "sheetFormatPr", {"defaultRowHeight": "20"})
        if sheet.widths:
            cols = ET.SubElement(root, "cols")
            for index, width in enumerate(sheet.widths, start=1):
                ET.SubElement(cols, "col", {"min": str(index), "max": str(index), "width": str(width), "customWidth": "1"})
        sheet_data = ET.SubElement(root, "sheetData")
        header_rows = set(sheet.header_rows)
        for row_index, values in enumerate(sheet.rows, start=1):
            row = ET.SubElement(sheet_data, "row", {"r": str(row_index), "ht": "22" if row_index in header_rows else "20", "customHeight": "1"})
            for column_index, value in enumerate(values, start=1):
                if value is None or value == "":
                    continue
                cell = ET.SubElement(row, "c", {"r": _cell_ref(row_index, column_index)})
                if row_index in header_rows:
                    cell.set("s", "1")
                if isinstance(value, bool):
                    cell.set("t", "b")
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    cell.set("s", "3")
                else:
                    cell.set("t", "s")
                value_element = ET.SubElement(cell, "v")
                if isinstance(value, bool):
                    value_element.text = "1" if value else "0"
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    value_element.text = str(value)
                else:
                    value_element.text = str(string_ids[_string_value(value)])
        if sheet.autofilter and sheet.rows:
            final_column = _column_name(max(len(row) for row in sheet.rows))
            ET.SubElement(root, "autoFilter", {"ref": f"A1:{final_column}{len(sheet.rows)}"})
        ET.SubElement(root, "pageMargins", {"left": "0.3", "right": "0.3", "top": "0.5", "bottom": "0.5", "header": "0.2", "footer": "0.2"})
        return root


class XlsxReader:
    """Read ordinary XLSX value cells without evaluating formulas."""

    def __init__(self, path: str | Path) -> None:
        source = Path(path)
        try:
            with ZipFile(source) as archive:
                self._parts = {name: archive.read(name) for name in archive.namelist()}
        except FileNotFoundError as exc:
            raise XlsxError("file_not_found", "找不到 Excel 文件。") from exc
        except (BadZipFile, OSError, KeyError) as exc:
            raise XlsxError("file_corrupt", "Excel 文件损坏或不是有效的 XLSX 文件。", str(exc)) from exc
        try:
            self._shared_strings = self._read_shared_strings()
            self._sheet_targets = self._read_sheets()
        except (ET.ParseError, KeyError, ValueError) as exc:
            raise XlsxError("file_corrupt", "Excel 文件结构无法读取。", str(exc)) from exc

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheet_targets)

    def rows(self, sheet_name: str) -> list[list[Any]]:
        target = self._sheet_targets.get(sheet_name)
        if not target:
            raise XlsxError("missing_sheet", f"缺少必要 Sheet：{sheet_name}。")
        root = ET.fromstring(self._parts[target])
        result: list[list[Any]] = []
        for row_element in root.findall("x:sheetData/x:row", NS):
            values: list[Any] = []
            for cell in row_element.findall("x:c", NS):
                ref = cell.get("r", "A1")
                match = re.match(r"([A-Za-z]+)\d+", ref)
                if not match:
                    continue
                column = _column_number(match.group(1))
                while len(values) < column:
                    values.append(None)
                values[column - 1] = self._cell_value(cell)
            result.append(values)
        return result

    def _read_shared_strings(self) -> list[str]:
        raw = self._parts.get("xl/sharedStrings.xml")
        if raw is None:
            return []
        root = ET.fromstring(raw)
        return ["".join(text for text in item.itertext()) for item in root.findall("x:si", NS)]

    def _read_sheets(self) -> dict[str, str]:
        workbook = ET.fromstring(self._parts["xl/workbook.xml"])
        relationships = ET.fromstring(self._parts["xl/_rels/workbook.xml.rels"])
        rel_targets = {item.get("Id"): item.get("Target", "") for item in relationships.findall(_relationship_tag("Relationship"))}
        result: dict[str, str] = {}
        for sheet in workbook.findall("x:sheets/x:sheet", NS):
            name = sheet.get("name", "")
            relation_id = sheet.get(f"{{{REL_NS}}}id", "")
            target = rel_targets.get(relation_id, "")
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            if name and target in self._parts:
                result[name] = target
        return result

    def _cell_value(self, cell: ET.Element) -> Any:
        cell_type = cell.get("t", "")
        if cell_type == "inlineStr":
            return "".join(cell.itertext())
        value_element = cell.find("x:v", NS)
        if value_element is None or value_element.text is None:
            return None
        value = value_element.text
        if cell_type == "s":
            try:
                return self._shared_strings[int(value)]
            except (ValueError, IndexError) as exc:
                raise XlsxError("file_corrupt", "Excel 共享字符串索引无效。", value) from exc
        if cell_type == "b":
            return value == "1"
        if cell_type in {"str", "e"}:
            return value
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except ValueError:
            return value
