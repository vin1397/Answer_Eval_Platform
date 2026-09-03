"""
OCR service — public entry point used by the evaluation pipeline.

Two engines are available, selected by `settings.OCR_ENGINE`:
  - "trocr"     (default): local handwriting-line segmentation + local
                 TrOCR recognition (see handwriting_segmentation.py /
                 trocr_service.py). This is what handwritten student
                 answer scripts should use.
  - "paddleocr": legacy full-page OCR, kept as a fallback/alternative for
                 printed or lightly-structured documents. Not removed —
                 some deployments may still want it for non-handwriting
                 scripts.

`extract_document()` is the single public interface the rest of the app
depends on (`services/evaluation_pipeline.py`) — its signature and return
type (`OCRDocumentResult`) are unchanged from before, so nothing downstream
needed to change. New optional fields (`structured_answers`,
`has_uncertain_segments`) were added with safe defaults rather than
replacing the existing `question_segments: dict[str, str]` shape.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Matches question-number markers such as "1)", "1a)", "Q1.", "2.b", "10 a)"
QUESTION_MARKER_RE = re.compile(
    r"^\s*(?:Q\.?\s*)?(\d{1,2})\s*(?:([a-dA-D])(?![a-zA-Z])\s*)?[.)]\s*"
)


@dataclass
class OCRLine:
    text: str
    confidence: float
    bbox: list  # 4 (x, y) points, or [[x0,y0]] line-band marker for the TrOCR path


@dataclass
class OCRPageResult:
    page_number: int
    lines: list[OCRLine] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class OCRDocumentResult:
    pages: list[OCRPageResult] = field(default_factory=list)
    full_text: str = ""
    question_segments: dict[str, str] = field(default_factory=dict)
    # New, additive — richer per-question data from the TrOCR pipeline.
    # Empty dict / False when using the legacy PaddleOCR path.
    structured_answers: dict[str, dict] = field(default_factory=dict)
    has_uncertain_segments: bool = False


def extract_document(file_path: str) -> OCRDocumentResult:
    """
    Runs the configured OCR engine over an answer script (PDF or image)
    and returns per-page results, the concatenated full text, and a
    best-effort split into per-question-number answer segments.
    """
    if settings.OCR_ENGINE == "paddleocr":
        return _extract_document_paddleocr(file_path)
    return _extract_document_trocr(file_path)


# --------------------------------------------------------------------------
# Default engine: local TrOCR line segmentation
# --------------------------------------------------------------------------
def _extract_document_trocr(file_path: str) -> OCRDocumentResult:
    from ai.ocr import handwriting_segmentation as hw

    doc = hw.process_document(file_path)

    pages: dict[int, OCRPageResult] = {}
    structured_answers: dict[str, dict] = {}
    any_uncertain = False
    full_text_parts: list[str] = []

    for block in doc.blocks:
        page = pages.setdefault(block.page_number, OCRPageResult(page_number=block.page_number))
        for line in block.lines:
            page.lines.append(
                OCRLine(text=line.text, confidence=line.confidence, bbox=[[0, line.y_start], [0, line.y_end]])
            )
        page.raw_text = (page.raw_text + "\n" + block.answer_text).strip()
        full_text_parts.append(block.answer_text)

        if block.uncertain:
            any_uncertain = True
            # Uncertain blocks are kept (never silently dropped) under a
            # placeholder key so a human can see and reassign them.
            key = f"uncertain_p{block.page_number}_{len([k for k in structured_answers if k.startswith('uncertain')]) + 1}"
        else:
            key = block.question_number

        structured_answers[key] = {
            "answer_text": block.answer_text,
            "confidence": block.confidence,
            "uncertain": block.uncertain,
            "page_number": block.page_number,
            "line_count": len(block.lines),
        }

    question_segments = {
        k: v["answer_text"] for k, v in structured_answers.items() if not v["uncertain"]
    }

    return OCRDocumentResult(
        pages=[pages[p] for p in sorted(pages.keys())],
        full_text="\n\n".join(full_text_parts),
        question_segments=question_segments,
        structured_answers=structured_answers,
        has_uncertain_segments=any_uncertain,
    )


# --------------------------------------------------------------------------
# Legacy/alternate engine: full-page PaddleOCR (kept, not the default)
# --------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_paddle_engine():
    from paddleocr import PaddleOCR  # imported lazily: heavy + optional at dev time

    return PaddleOCR(
        use_angle_cls=True,
        lang=settings.OCR_LANGUAGE,
        show_log=False,
    )


def _preprocess_image_paddle(image_path: str) -> np.ndarray:
    import cv2  # lazy: only needed by this engine

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 15
    )
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


def _pdf_to_images_paddle(pdf_path: str) -> list[np.ndarray]:
    import cv2  # lazy
    import fitz  # PyMuPDF - optional dependency, imported lazily

    images = []
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap(dpi=settings.SCAN_DPI)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        images.append(img_array)
    return images


def _run_paddle_ocr_on_page(image: np.ndarray) -> OCRPageResult:
    engine = _get_paddle_engine()
    result = engine.ocr(image, cls=True)

    lines: list[OCRLine] = []
    if result and result[0]:
        for detection in result[0]:
            bbox, (text, confidence) = detection
            lines.append(OCRLine(text=text, confidence=float(confidence), bbox=bbox))

    lines.sort(key=lambda l: (round(l.bbox[0][1] / 20), l.bbox[0][0]))
    raw_text = "\n".join(l.text for l in lines)
    return OCRPageResult(page_number=0, lines=lines, raw_text=raw_text)


def _extract_document_paddleocr(file_path: str) -> OCRDocumentResult:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        images = _pdf_to_images_paddle(file_path)
    else:
        images = [_preprocess_image_paddle(file_path)]

    pages: list[OCRPageResult] = []
    for idx, img in enumerate(images, start=1):
        page_result = _run_paddle_ocr_on_page(img)
        page_result.page_number = idx
        pages.append(page_result)

    full_text = "\n\n".join(p.raw_text for p in pages)
    question_segments = segment_by_question_number(full_text)

    return OCRDocumentResult(pages=pages, full_text=full_text, question_segments=question_segments)


def segment_by_question_number(full_text: str) -> dict[str, str]:
    """
    Split raw OCR text into {question_number: answer_text} using detected
    question-marker lines (e.g. "1a)", "Q2.") as segment boundaries.
    Used by the legacy PaddleOCR path; the TrOCR path segments per-block
    during line grouping instead (see handwriting_segmentation.py).
    """
    segments: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []

    for line in full_text.splitlines():
        match = QUESTION_MARKER_RE.match(line)
        if match:
            if current_key is not None:
                segments[current_key] = "\n".join(buffer).strip()
            number, sub = match.group(1), match.group(2)
            current_key = f"{number}{sub.lower()}" if sub else number
            buffer = [line[match.end():]]
        else:
            if current_key is not None:
                buffer.append(line)

    if current_key is not None:
        segments[current_key] = "\n".join(buffer).strip()

    return segments
