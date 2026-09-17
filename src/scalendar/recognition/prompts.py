"""The standalone prompt and JSON schema for timetable recognition."""

from __future__ import annotations

from .base import RecognitionContext


RECOGNITION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "courses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "weekday": {"type": ["integer", "null"]},
                    "start_section": {"type": ["integer", "null"]},
                    "end_section": {"type": ["integer", "null"]},
                    "start_week": {"type": ["integer", "null"]},
                    "end_week": {"type": ["integer", "null"]},
                    "week_pattern": {"type": "string", "enum": ["all", "odd", "even", "custom"]},
                    "custom_weeks": {"type": "array", "items": {"type": "integer"}},
                    "teacher": {"type": "string"},
                    "building": {"type": "string"},
                    "room": {"type": "string"},
                    "location_text": {"type": "string"},
                    "needs_review_fields": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": [
                    "name", "weekday", "start_section", "end_section",
                    "start_week", "end_week", "week_pattern", "custom_weeks",
                    "teacher", "building", "room", "location_text",
                    "needs_review_fields", "notes",
                ],
            },
        }
    },
    "required": ["courses"],
}


def build_recognition_prompt(context: RecognitionContext) -> str:
    context_text = (
        f"学校上下文：{context.school or '未知'}"
        f"；校区上下文：{context.campus or '未知'}"
        f"；学期总周数：{context.total_weeks}"
        f"；可用节次编号：{', '.join(str(item) for item in context.section_indices) or '未知'}"
    )
    lines = [
        "你正在识别一张大学课程表图片。请理解二维表格结构，不要只做逐字 OCR。",
        "横轴通常代表星期，纵轴通常代表节次；一个色块可能跨越多个节次，一个单元格可能同时包含课程名、周次、教师和地点。",
        "",
        "只输出要求的结构化 JSON。标准 week_pattern 只能是 all、odd、even、custom。",
        "如果图片无法可靠判断某个字符串，输出空字符串；如果无法可靠判断某个数字，输出 null，并把字段名放进 needs_review_fields。",
        "绝对不要猜学校、校区、教师、教室、周次或节次，也不要根据常识补全。上下文只用于帮助理解图片，不是图片事实。",
        "如果 custom，只有在图片明确给出具体周次时才填写 custom_weeks；否则使用 needs_review_fields。",
        "不要输出置信度、思考过程或任何 schema 之外的字段。",
        "",
        "当前项目上下文：",
        context_text,
    ]
    return chr(10).join(lines)
