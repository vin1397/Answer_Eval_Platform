from pathlib import Path
import io
import re

import pandas as pd
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = ROOT / "models" / "handwriting" / "trocr-base-handwritten"
DATASET_FILE = ROOT / "dataset" / "test.parquet"

SAMPLES = 10


def normalize(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def levenshtein(a, b):
    previous = list(range(len(b) + 1))

    for i, ca in enumerate(a, start=1):
        current = [i]

        for j, cb in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (ca != cb)

            current.append(
                min(insert, delete, replace)
            )

        previous = current

    return previous[-1]


def extract_image(value):
    if isinstance(value, Image.Image):
        return value.convert("RGB")

    if isinstance(value, dict):

        if value.get("bytes") is not None:
            return Image.open(
                io.BytesIO(value["bytes"])
            ).convert("RGB")

        if value.get("path"):
            return Image.open(
                value["path"]
            ).convert("RGB")

    if isinstance(value, bytes):
        return Image.open(
            io.BytesIO(value)
        ).convert("RGB")

    raise TypeError(
        f"Unsupported image type: {type(value)}"
    )


def word_error_rate(reference, prediction):

    ref_words = normalize(reference).split()
    pred_words = normalize(prediction).split()

    distance = levenshtein(
        ref_words,
        pred_words,
    )

    if len(ref_words) == 0:
        return 0.0 if len(pred_words) == 0 else 1.0

    return distance / len(ref_words)


def character_error_rate(reference, prediction):

    reference = normalize(reference)
    prediction = normalize(prediction)

    distance = levenshtein(
        reference,
        prediction,
    )

    if len(reference) == 0:
        return 0.0 if len(prediction) == 0 else 1.0

    return distance / len(reference)


def main():

    print("=" * 70)
    print("LOCAL TrOCR DATASET BENCHMARK")
    print("=" * 70)

    print(f"\nModel:   {MODEL_DIR}")
    print(f"Dataset: {DATASET_FILE}")
    print(f"Samples: {SAMPLES}")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Model not found:\n{MODEL_DIR}"
        )

    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATASET_FILE}"
        )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"\nDevice: {device}")

    print("\nLoading dataset...")

    df = pd.read_parquet(
        DATASET_FILE
    )

    print(
        f"Dataset contains {len(df)} samples."
    )

    count = min(
        SAMPLES,
        len(df),
    )

    df = df.head(count)

    print(
        f"Testing {count} samples."
    )

    print("\nLoading local TrOCR processor...")

    processor = TrOCRProcessor.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    print("Loading local TrOCR model...")

    model = VisionEncoderDecoderModel.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    model.to(device)
    model.eval()

    print("\nTrOCR ready.")
    print("-" * 70)

    total_cer = 0.0
    total_wer = 0.0

    correct_like = 0

    results = []

    for index, row in df.iterrows():

        sample_number = index + 1

        reference = str(
            row["text"]
        )

        try:

            image = extract_image(
                row["image"]
            )

            print(
                f"\n[{sample_number}/{count}] "
                f"Image size: {image.size}"
            )

            pixel_values = processor(
                images=image,
                return_tensors="pt",
            ).pixel_values

            pixel_values = pixel_values.to(
                device
            )

            with torch.no_grad():

                generated_ids = model.generate(
                    pixel_values,
                    max_new_tokens=128,
                )

            prediction = processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
            )[0]

            cer = character_error_rate(
                reference,
                prediction,
            )

            wer = word_error_rate(
                reference,
                prediction,
            )

            total_cer += cer
            total_wer += wer

            if normalize(reference) == normalize(
                prediction
            ):
                correct_like += 1

            results.append(
                {
                    "sample": sample_number,
                    "reference": reference,
                    "prediction": prediction,
                    "cer": cer,
                    "wer": wer,
                }
            )

            print(
                f"Reference : {reference}"
            )

            print(
                f"TrOCR     : {prediction}"
            )

            print(
                f"CER       : {cer * 100:.2f}%"
            )

            print(
                f"WER       : {wer * 100:.2f}%"
            )

        except Exception as exc:

            print(
                f"ERROR on sample {sample_number}: "
                f"{exc}"
            )

            results.append(
                {
                    "sample": sample_number,
                    "reference": reference,
                    "prediction": "",
                    "cer": None,
                    "wer": None,
                }
            )

    successful = [
        r for r in results
        if r["cer"] is not None
    ]

    if successful:

        average_cer = (
            sum(r["cer"] for r in successful)
            / len(successful)
        )

        average_wer = (
            sum(r["wer"] for r in successful)
            / len(successful)
        )

    else:

        average_cer = 1.0
        average_wer = 1.0

    output_dir = (
        ROOT
        / "datasets"
        / "handwriting"
        / "benchmark_results"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / "trocr_test_results.csv"
    )

    pd.DataFrame(
        results
    ).to_csv(
        output_file,
        index=False,
    )

    print("\n")
    print("=" * 70)
    print("FINAL TrOCR BENCHMARK")
    print("=" * 70)

    print(
        f"Samples tested : {count}"
    )

    print(
        f"Successful     : {len(successful)}"
    )

    print(
        f"Exact matches  : {correct_like}/{count}"
    )

    print(
        f"Average CER    : {average_cer * 100:.2f}%"
    )

    print(
        f"Average WER    : {average_wer * 100:.2f}%"
    )

    print(
        f"\nResults saved to:\n{output_file}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()