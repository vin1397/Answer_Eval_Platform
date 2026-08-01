"""
OCR service built on PaddleOCR.

Responsible for:
  - Loading pages of a scanned answer script (PDF or image)
  - Running text detection + recognition (handwriting-capable PP-OCR models)
  - Grouping recognised text lines into paragraphs
  - Locating question-number markers ("1a)", "Q2.", "3." ...) so downstream
    NLP can split the OCR stream into per-question answer segments.

The heavy PaddleOCR engine is loaded lazily and cached as a singleton so it
is only initialised once per worker process (import/model load is expensive).
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Matches question-number markers such as "1)", "1a)", "Q1.", "2.b", "10 a)"
QUESTION_MARKER_RE = re.compile(
    r"^\s*(?:Q\.?\s*)?(\d{1,2})\s*[.)]?\s*([a-dA-D])?\s*[.)]\s*"
)


@dataclass
class OCRLine:
    text: str
    confidence: float
    bbox: list  # 4 (x, y) points


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


@lru_cache(maxsize=1)
def _get_engine():
    """
    Lazily instantiate the PaddleOCR engine. Cached so the (large)
    detection + recognition models are loaded only once per process.
    """
    from paddleocr import PaddleOCR  # imported lazily: heavy + optional at dev time

    return PaddleOCR(
        use_angle_cls=True,
        lang=settings.OCR_LANGUAGE,
        show_log=False,
    )


def _preprocess_image(image_path: str) -> np.ndarray:
    """
    Basic OpenCV preprocessing pipeline to improve OCR accuracy on
    photographed / scanned handwritten answer sheets: grayscale,
    denoise, adaptive threshold, then convert back to BGR (PaddleOCR
    expects a 3-channel image).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 15
    )
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


def _pdf_to_images(pdf_path: str) -> list[np.ndarray]:
    """Rasterise each page of a PDF answer script into an OpenCV image."""
    import fitz  # PyMuPDF - optional dependency, imported lazily

    images = []
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        images.append(img_array)
    return images


def run_ocr_on_page(image: np.ndarray) -> OCRPageResult:
    engine = _get_engine()
    result = engine.ocr(image, cls=True)

    lines: list[OCRLine] = []
    if result and result[0]:
        for detection in result[0]:
            bbox, (text, confidence) = detection
            lines.append(OCRLine(text=text, confidence=float(confidence), bbox=bbox))

    # Sort top-to-bottom, then left-to-right, using the top-left bbox corner
    lines.sort(key=lambda l: (round(l.bbox[0][1] / 20), l.bbox[0][0]))
    raw_text = "\n".join(l.text for l in lines)
    return OCRPageResult(page_number=0, lines=lines, raw_text=raw_text)


def extract_document(file_path: str) -> OCRDocumentResult:
    """
    Run the full OCR pipeline over an answer script (PDF or image),
    returning per-page results plus the concatenated full text and a
    best-effort split into per-question-number answer segments.
    """
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        images = _pdf_to_images(file_path)
    else:
        images = [_preprocess_image(file_path)]

    pages: list[OCRPageResult] = []
    for idx, img in enumerate(images, start=1):
        page_result = run_ocr_on_page(img)
        page_result.page_number = idx
        pages.append(page_result)

    full_text = "\n\n".join(p.raw_text for p in pages)
    question_segments = segment_by_question_number(full_text)

    return OCRDocumentResult(pages=pages, full_text=full_text, question_segments=question_segments)


def segment_by_question_number(full_text: str) -> dict[str, str]:
    """
    Split raw OCR text into {question_number: answer_text} using detected
    question-marker lines (e.g. "1a)", "Q2.") as segment boundaries.
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
