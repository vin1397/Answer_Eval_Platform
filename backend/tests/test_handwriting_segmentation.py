"""
Tests for ai/ocr/handwriting_segmentation.py — line/block segmentation and
question-marker detection (spec items D, F, uncertainty flagging).

These tests use synthetic numpy "binary page" arrays rather than real scans,
so they run without OpenCV needing real handwriting images and without the
TrOCR model being installed. TrOCR itself is tested separately (guarded,
skips if the local model isn't present — see test_trocr_model_loading.py).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

cv2 = pytest.importorskip("cv2", reason="opencv-python-headless not installed in this environment")

from ai.ocr.handwriting_segmentation import (  # noqa: E402
    segment_lines, group_lines_into_blocks, _match_question_marker,
)


def _make_binary_page(line_bands: list[tuple[int, int]], width: int = 400, height: int = 300) -> np.ndarray:
    """Builds a synthetic binarized page (0/255) with solid horizontal bands
    of 'ink' at the given (y_start, y_end) ranges — mimicking text lines."""
    page = np.zeros((height, width), dtype=np.uint8)
    for y_start, y_end in line_bands:
        page[y_start:y_end, 40:360] = 255
    return page


def test_segment_lines_detects_correct_number_of_bands():
    page = _make_binary_page([(20, 35), (50, 65), (80, 95)])
    bands = segment_lines(page)
    assert len(bands) == 3


def test_segment_lines_preserves_top_to_bottom_order():
    page = _make_binary_page([(120, 135), (20, 35), (70, 85)])
    bands = segment_lines(page)
    starts = [b[0] for b in bands]
    assert starts == sorted(starts)


def test_segment_lines_ignores_page_with_no_text():
    page = _make_binary_page([])
    bands = segment_lines(page)
    assert bands == []


def test_group_lines_into_blocks_splits_on_large_gaps():
    # Two lines close together (one block), then a big gap, then one more line (second block).
    page_height = 400
    line_bands = [(20, 35), (38, 53), (200, 215)]
    blocks = group_lines_into_blocks(line_bands, page_height)
    assert len(blocks) == 2
    assert len(blocks[0]) == 2
    assert len(blocks[1]) == 1


def test_group_lines_into_blocks_keeps_close_lines_together():
    page_height = 400
    line_bands = [(20, 35), (40, 55), (60, 75)]
    blocks = group_lines_into_blocks(line_bands, page_height)
    assert len(blocks) == 1
    assert len(blocks[0]) == 3


@pytest.mark.parametrize(
    "text,expected_number,expected_uncertain",
    [
        ("1) Supervised learning is...", "1", False),
        ("Q21. The answer is...", "21", False),
        ("12b) Layered architecture...", "12b", False),
        ("2.b Something here", "2", False),
        ("this has no marker at all", None, True),
        ("", None, True),
    ],
)
def test_match_question_marker(text, expected_number, expected_uncertain):
    number, uncertain, _remaining = _match_question_marker(text)
    assert number == expected_number
    assert uncertain == expected_uncertain


def test_match_question_marker_strips_marker_from_remaining_text():
    _number, _uncertain, remaining = _match_question_marker("21. Supervised learning is a type of ML.")
    assert remaining == "Supervised learning is a type of ML."


def test_unmatched_block_is_flagged_uncertain_not_guessed():
    """Core safety property from spec item 6: when detection isn't
    confident, the block must be marked uncertain, never silently
    assigned to some question number."""
    number, uncertain, _ = _match_question_marker("mumbled illegible text")
    assert uncertain is True
    assert number is None
