"""
Tests for local TrOCR loading (spec items E, F). These are guarded: if the
local model directory (TROCR_MODEL_DIR) isn't present in the environment
running the tests, they skip with a clear reason rather than failing —
the model is a large local asset that isn't expected to exist in every
CI/dev environment, but the loading code itself is still exercised
wherever the model IS present (e.g. on the machine that has it installed).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402

settings = get_settings()
_model_dir = Path(settings.TROCR_MODEL_DIR)
_model_present = _model_dir.exists() and (_model_dir / "config.json").exists()

settings = get_settings()
_model_dir = Path(settings.TROCR_MODEL_DIR)
_model_present = _model_dir.exists() and (_model_dir / "config.json").exists()

requires_model = pytest.mark.skipif(
    not _model_present,
    reason=f"Local TrOCR model not found at {settings.TROCR_MODEL_DIR} — set TROCR_MODEL_DIR "
    "or place the model there to run this test.",
)


@requires_model
def test_trocr_engine_loads_with_local_files_only():
    from ai.ocr import trocr_service

    assert trocr_service.is_model_available() is True


@requires_model
def test_trocr_recognizes_a_synthetic_line_without_crashing():
    """Not asserting exact transcription (that depends on real handwriting
    imagery) — just that a plausible line-shaped image is accepted and
    returns a text+confidence result, proving the model/processor wiring
    (local_files_only, tensor shapes, device placement) is correct."""
    from ai.ocr import trocr_service

    line_image = np.full((48, 320), 255, dtype=np.uint8)
    line_image[10:30, 20:280] = 0  # a dark band standing in for handwriting strokes

    result = trocr_service.recognize_line(line_image)
    assert isinstance(result.text, str)
    assert 0.0 <= result.confidence <= 1.0


def test_trocr_model_not_found_error_is_actionable():
    """Confirms the missing-model error path (spec item 14) gives a clear,
    non-cryptic message rather than a bare stack trace — tested by pointing
    at a directory that doesn't exist. Deliberately NOT gated behind
    `requires_model`: the whole point is verifying the failure path works
    correctly in environments where the model is absent, and it never
    needs torch/transformers since the existence check happens first."""
    from ai.ocr.trocr_service import TrOCRModelNotFoundError, _TrOCREngine

    original = settings.TROCR_MODEL_DIR
    try:
        settings.TROCR_MODEL_DIR = "/definitely/not/a/real/path"
        with pytest.raises(TrOCRModelNotFoundError, match="local_files_only|not found|TROCR_MODEL_DIR"):
            _TrOCREngine()
    finally:
        settings.TROCR_MODEL_DIR = original
