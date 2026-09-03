"""
Generic handwriting segmentation for scanned/photographed answer scripts.

Pipeline (per page):
  preprocess (deskew-friendly binarization)
    -> horizontal projection profile
    -> line bands (top-to-bottom, in order)
    -> group lines into answer blocks (paragraph gaps)
    -> for each block, run the first line through TrOCR and test it against
       the question-marker regex to associate the block with a question
       number; if no confident match, the block is flagged `uncertain`
       rather than silently mis-assigned or dropped.

Nothing here is specific to any one exam layout, page count, or student —
thresholds are relative to each page's own row-density statistics, not
fixed pixel coordinates.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from config.settings import get_settings
from ai.ocr import trocr_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Matches question-number markers such as "1)", "1a)", "Q1.", "2.b", "10 a)"
QUESTION_MARKER_RE = re.compile(
    r"^\s*(?:Q\.?\s*)?(\d{1,2})\s*(?:([a-dA-D])(?![a-zA-Z])\s*)?[.)]\s*"
)

# Tunable segmentation constants (relative, not fixed-pixel — safe across
# scan resolutions since they're derived from each page's own dimensions).
MIN_LINE_HEIGHT_RATIO = 0.008     # a text line is at least this fraction of page height
LINE_GAP_MERGE_RATIO = 0.004      # gaps smaller than this fraction are the same line
BLOCK_GAP_RATIO = 0.018           # gaps larger than this fraction start a new answer block
ROW_DENSITY_THRESHOLD_RATIO = 0.02  # min fraction of dark pixels in a row to count as "text"


@dataclass
class LineSegment:
    line_number: int
    text: str
    confidence: float
    y_start: int
    y_end: int


@dataclass
class AnswerBlock:
    page_number: int
    question_number: str | None
    uncertain: bool
    lines: list[LineSegment] = field(default_factory=list)
    answer_text: str = ""
    confidence: float = 0.0


@dataclass
class HandwritingDocumentResult:
    blocks: list[AnswerBlock] = field(default_factory=list)
    page_count: int = 0


def _load_cv2():
    import cv2  # lazy: heavy optional dependency

    return cv2


def _pdf_to_page_images(file_path: str) -> list[np.ndarray]:
    """Rasterise each PDF page to a grayscale numpy image at OCR-friendly DPI."""
    import fitz  # PyMuPDF, lazy import

    cv2 = _load_cv2()
    images = []
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap(dpi=settings.SCAN_DPI)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        elif pix.n == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        else:
            arr = arr[:, :, 0]
        images.append(arr)
    return images


def _load_image_page(file_path: str) -> list[np.ndarray]:
    cv2 = _load_cv2()
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {file_path}")
    return [img]


def preprocess_page(gray: np.ndarray) -> np.ndarray:
    """Denoise + adaptive-threshold a page for reliable row-density segmentation."""
    cv2 = _load_cv2()
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15
    )
    return binary


def segment_lines(binary_page: np.ndarray) -> list[tuple[int, int]]:
    """
    Horizontal-projection-profile line segmentation: sums dark pixels per
    row, finds contiguous bands above a density threshold, and merges
    bands separated by only a small gap (natural spacing within a line of
    handwriting, e.g. ascenders/descenders). Returns (y_start, y_end)
    bands in top-to-bottom order.
    """
    height, width = binary_page.shape
    row_density = binary_page.sum(axis=1) / 255.0 / width  # fraction of dark pixels per row

    is_text_row = row_density > ROW_DENSITY_THRESHOLD_RATIO
    min_line_height = max(3, int(height * MIN_LINE_HEIGHT_RATIO))
    merge_gap = max(1, int(height * LINE_GAP_MERGE_RATIO))

    bands: list[tuple[int, int]] = []
    start = None
    for y in range(height):
        if is_text_row[y] and start is None:
            start = y
        elif not is_text_row[y] and start is not None:
            bands.append((start, y))
            start = None
    if start is not None:
        bands.append((start, height))

    # Merge bands with tiny gaps between them (same line, e.g. dotted 'i').
    merged: list[list[int]] = []
    for band_start, band_end in bands:
        if merged and band_start - merged[-1][1] <= merge_gap:
            merged[-1][1] = band_end
        else:
            merged.append([band_start, band_end])

    return [(s, e) for s, e in merged if (e - s) >= min_line_height]


def group_lines_into_blocks(line_bands: list[tuple[int, int]], page_height: int) -> list[list[tuple[int, int]]]:
    """Groups consecutive line bands into answer blocks, splitting on gaps
    large enough to indicate a new question/paragraph rather than a normal
    line break."""
    block_gap = max(4, int(page_height * BLOCK_GAP_RATIO))
    blocks: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []

    for i, (start, end) in enumerate(line_bands):
        if current and (start - current[-1][1]) > block_gap:
            blocks.append(current)
            current = []
        current.append((start, end))
    if current:
        blocks.append(current)

    return blocks


def _crop_line(gray_page: np.ndarray, y_start: int, y_end: int, padding: int = 4) -> np.ndarray:
    height, width = gray_page.shape
    y0 = max(0, y_start - padding)
    y1 = min(height, y_end + padding)
    return gray_page[y0:y1, 0:width]


def process_document(file_path: str) -> HandwritingDocumentResult:
    """
    Full pipeline entry point: PDF/image -> pages -> line segmentation ->
    per-block TrOCR -> question-number association with uncertainty flags.
    """
    suffix = Path(file_path).suffix.lower()
    pages = _pdf_to_page_images(file_path) if suffix == ".pdf" else _load_image_page(file_path)

    blocks: list[AnswerBlock] = []

    for page_index, gray_page in enumerate(pages, start=1):
        binary = preprocess_page(gray_page)
        line_bands = segment_lines(binary)
        grouped = group_lines_into_blocks(line_bands, gray_page.shape[0])

        for band_group in grouped:
            line_crops = [_crop_line(gray_page, s, e) for s, e in band_group]
            ocr_results = trocr_service.recognize_lines_batch(line_crops)

            line_segments = [
                LineSegment(
                    line_number=i + 1,
                    text=res.text,
                    confidence=res.confidence,
                    y_start=band_group[i][0],
                    y_end=band_group[i][1],
                )
                for i, res in enumerate(ocr_results)
            ]

            question_number, uncertain, remaining_first_line = _match_question_marker(
                line_segments[0].text if line_segments else ""
            )
            if remaining_first_line is not None and line_segments:
                line_segments[0] = LineSegment(
                    line_number=line_segments[0].line_number,
                    text=remaining_first_line,
                    confidence=line_segments[0].confidence,
                    y_start=line_segments[0].y_start,
                    y_end=line_segments[0].y_end,
                )

            answer_text = " ".join(l.text for l in line_segments if l.text).strip()
            avg_confidence = (
                round(sum(l.confidence for l in line_segments) / len(line_segments), 4)
                if line_segments else 0.0
            )

            blocks.append(
                AnswerBlock(
                    page_number=page_index,
                    question_number=question_number,
                    uncertain=uncertain,
                    lines=line_segments,
                    answer_text=answer_text,
                    confidence=avg_confidence,
                )
            )

    return HandwritingDocumentResult(blocks=blocks, page_count=len(pages))


def _match_question_marker(first_line_text: str) -> tuple[str | None, bool, str | None]:
    """
    Tries to detect a question-number marker at the start of a block's
    first line. Returns (question_number, uncertain, remaining_text).
    `uncertain=True` means no confident marker was found — the caller
    must NOT guess an assignment in that case.
    """
    if not first_line_text:
        return None, True, None

    match = QUESTION_MARKER_RE.match(first_line_text)
    if not match:
        return None, True, None

    number, sub = match.group(1), match.group(2)
    question_number = f"{number}{sub.lower()}" if sub else number
    remaining = first_line_text[match.end():].strip()
    return question_number, False, remaining
