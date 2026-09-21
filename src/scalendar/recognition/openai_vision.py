"""OpenAI Responses API implementation for timetable image recognition."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from .base import RecognitionContext, RecognitionError, RecognitionProvider
from .models import RecognitionResult
from .normalizer import normalize_recognition_payload
from .prompts import RECOGNITION_SCHEMA, build_recognition_prompt


SUPPORTED_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class OpenAIVisionProvider(RecognitionProvider):
    requires_api_key = True

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-5.5")
        self.client = client
        self.timeout = timeout

    def recognize(self, image: Path, context: RecognitionContext) -> RecognitionResult:
        path = Path(image)
        if path.suffix.lower() not in SUPPORTED_IMAGE_TYPES:
            raise RecognitionError("invalid_image", "图片格式无法读取。")
        if not path.is_file():
            raise RecognitionError("invalid_image", "找不到所选图片。")
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RecognitionError("missing_api_key", "未设置 OpenAI API Key。")
        try:
            data = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError as exc:
            raise RecognitionError("invalid_image", "图片无法读取。", str(exc)) from exc
        mime = SUPPORTED_IMAGE_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        image_url = f"data:{mime};base64,{data}"
        client = self.client or self._build_client(api_key)
        request = {
            "model": self.model,
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": build_recognition_prompt(context)},
                    {"type": "input_image", "image_url": image_url, "detail": "high"},
                ],
            }],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "scalendar_timetable",
                    "description": "Structured timetable recognition candidates",
                    "schema": RECOGNITION_SCHEMA,
                    "strict": True,
                }
            },
        }
        try:
            response = client.responses.create(**request)
        except Exception as exc:
            raise self._map_api_error(exc) from exc
        output_text = str(getattr(response, "output_text", "") or "").strip()
        if not output_text:
            raise RecognitionError("output_parse", "模型输出无法解析。")
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RecognitionError("output_parse", "模型输出无法解析。", "invalid JSON") from exc
        result = normalize_recognition_payload(payload, context)
        result.provider = "openai"
        if any(issue.severity == "error" for issue in result.issues) and not result.courses:
            raise RecognitionError("output_parse", "识别结果没有有效课程。")
        return result

    def _build_client(self, api_key: str) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RecognitionError("model_unavailable", "OpenAI Python SDK 未安装。") from exc
        return OpenAI(api_key=api_key, timeout=self.timeout)

    @staticmethod
    def _map_api_error(error: Exception) -> RecognitionError:
        name = type(error).__name__.lower()
        status = getattr(error, "status_code", None)
        if "authentication" in name or "permission" in name or status in (401, 403):
            return RecognitionError("invalid_api_key", "OpenAI API Key 无效或未授权。")
        if "ratelimit" in name or status == 429:
            return RecognitionError("quota", "OpenAI API 限额或额度不足。")
        if "timeout" in name:
            return RecognitionError("timeout", "识别请求超时。")
        if "connection" in name or isinstance(error, ConnectionError):
            return RecognitionError("network", "网络连接失败。")
        if status == 404 or "notfound" in name:
            return RecognitionError("model_unavailable", "识别模型不可用。")
        return RecognitionError("api_error", "识别服务暂时不可用。")
