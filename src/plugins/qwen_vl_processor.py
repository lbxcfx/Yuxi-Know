from __future__ import annotations

import os
from typing import Any

from src.plugins.document_processor_base import BaseDocumentProcessor, OCRException


class QwenVLOCRProcessor(BaseDocumentProcessor):
    def process_file(self, file_path: str, params: dict[str, Any] | None = None) -> str:
        try:
            from src.plugins._ocr import OCRPlugin, OCRServiceException

            plugin = OCRPlugin()
            return plugin.process_file_qwen_vl(file_path, params=params)
        except OCRServiceException as e:
            raise OCRException(str(e), service_name="qwen_vl_ocr", status_code=getattr(e, "status_code", None))
        except Exception as e:  # noqa: BLE001
            raise OCRException(f"Qwen-VL OCR failed: {e}", service_name="qwen_vl_ocr", status_code="processing_failed")

    def check_health(self) -> dict[str, Any]:
        if os.getenv("DASHSCOPE_API_KEY"):
            return {"status": "healthy", "message": "DASHSCOPE_API_KEY is configured", "details": {"model": "qwen-vl-plus"}}
        return {"status": "unavailable", "message": "DASHSCOPE_API_KEY is not configured", "details": {}}

    def get_service_name(self) -> str:
        return "qwen_vl_ocr"

    def get_supported_extensions(self) -> list[str]:
        return [
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
            ".gif",
        ]
