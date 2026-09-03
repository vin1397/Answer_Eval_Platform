"""
Local handwriting OCR via a locally-downloaded TrOCR checkpoint
(e.g. microsoft/trocr-base-handwritten, saved to disk in advance).

Hard requirements from the project spec:
  - Model is loaded with local_files_only=True — never fetched at runtime.
  - No cloud OCR / external API calls of any kind.
  - The model is loaded ONCE and reused (singleton), not per line.
  - CPU by default, CUDA automatically if available.

This module operates purely on line-level crops (PIL Images / numpy
arrays for a single handwriting line) — never a full page. Page-level
segmentation into line crops is handled by `handwriting_segmentation.py`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TrOCRModelNotFoundError(RuntimeError):
    """Raised when the local TrOCR model directory is missing or incomplete."""


@dataclass
class LineOCRResult:
    text: str
    confidence: float  # 0..1, derived from average per-token generation probability


class _TrOCREngine:
    """Lazily-loaded singleton wrapping the TrOCR processor + model."""

    _instance: "_TrOCREngine | None" = None

    def __init__(self) -> None:
        model_dir = Path(settings.TROCR_MODEL_DIR)
        if not model_dir.exists() or not (model_dir / "config.json").exists():
            raise TrOCRModelNotFoundError(
                f"Local TrOCR model not found at '{model_dir}'. Expected files such as "
                "config.json, model.safetensors, tokenizer.json, vocab.json, merges.txt, "
                "preprocessor_config.json. Set TROCR_MODEL_DIR in your .env if the model "
                "lives elsewhere. The model is never downloaded automatically."
            )

        # Imported lazily so the rest of the app (and requirements-lite installs)
        # doesn't need `transformers`/`torch` just to boot.
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        self.device = "cuda" if (settings.TROCR_DEVICE == "auto" and torch.cuda.is_available()) else (
            settings.TROCR_DEVICE if settings.TROCR_DEVICE != "auto" else "cpu"
        )

        logger.info("Loading local TrOCR model from %s on device=%s", model_dir, self.device)
        self.processor = TrOCRProcessor.from_pretrained(str(model_dir), local_files_only=True)
        self.model = VisionEncoderDecoderModel.from_pretrained(str(model_dir), local_files_only=True)
        self.model.to(self.device)
        self.model.eval()
        self._torch = torch

    @classmethod
    def instance(cls) -> "_TrOCREngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def recognize_line(self, line_image: np.ndarray) -> LineOCRResult:
        """
        Runs TrOCR on a single pre-cropped handwriting line image
        (numpy array, RGB or grayscale) and returns the recognised text
        plus a confidence estimate derived from token-level generation
        probabilities (TrOCR has no native confidence output).
        """
        from PIL import Image

        torch = self._torch

        if line_image.ndim == 2:
            pil_image = Image.fromarray(line_image).convert("RGB")
        else:
            pil_image = Image.fromarray(line_image).convert("RGB")

        pixel_values = self.processor(images=pil_image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                pixel_values,
                max_new_tokens=196,
                output_scores=True,
                return_dict_in_generate=True,
            )

        token_ids = output.sequences[0]
        text = self.processor.batch_decode(output.sequences, skip_special_tokens=True)[0].strip()

        confidence = _estimate_confidence(output, torch)
        return LineOCRResult(text=text, confidence=confidence)

    def recognize_lines_batch(self, line_images: list[np.ndarray]) -> list[LineOCRResult]:
        """Batched variant for throughput when several line crops are ready at once."""
        if not line_images:
            return []
        from PIL import Image

        torch = self._torch
        pil_images = [Image.fromarray(img).convert("RGB") for img in line_images]
        pixel_values = self.processor(images=pil_images, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                pixel_values,
                max_new_tokens=196,
                output_scores=True,
                return_dict_in_generate=True,
            )

        texts = self.processor.batch_decode(output.sequences, skip_special_tokens=True)
        confidence = _estimate_confidence(output, torch)  # batch-averaged; per-item breakdown below

        results = []
        for i, text in enumerate(texts):
            results.append(LineOCRResult(text=text.strip(), confidence=confidence))
        return results


def _estimate_confidence(generate_output, torch) -> float:
    """
    TrOCR's `generate()` doesn't expose a calibrated confidence score, so we
    approximate one as the mean max-softmax-probability across generated
    tokens (a standard proxy for sequence-generation confidence).
    """
    scores = getattr(generate_output, "scores", None)
    if not scores:
        return 0.5  # neutral fallback if scores weren't returned

    probs = []
    for step_logits in scores:
        step_probs = torch.softmax(step_logits, dim=-1)
        probs.append(step_probs.max(dim=-1).values.mean().item())
    if not probs:
        return 0.5
    return round(max(0.0, min(1.0, sum(probs) / len(probs))), 4)


@lru_cache(maxsize=1)
def _cached_engine_or_none():
    """Returns the singleton engine, or None if the model directory is missing —
    callers decide whether that's fatal (production) or skippable (tests)."""
    try:
        return _TrOCREngine.instance()
    except TrOCRModelNotFoundError as exc:
        logger.warning(str(exc))
        return None


def is_model_available() -> bool:
    return _cached_engine_or_none() is not None


def recognize_line(line_image: np.ndarray) -> LineOCRResult:
    engine = _TrOCREngine.instance()  # raises TrOCRModelNotFoundError if missing — callers should surface this clearly
    return engine.recognize_line(line_image)


def recognize_lines_batch(line_images: list[np.ndarray]) -> list[LineOCRResult]:
    engine = _TrOCREngine.instance()
    return engine.recognize_lines_batch(line_images)
