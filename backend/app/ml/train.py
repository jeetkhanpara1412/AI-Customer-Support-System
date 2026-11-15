import argparse
import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.preprocess import preprocess_text

DATA_PATH = Path(__file__).parents[2] / "data" / "knowledge_base.csv"
ARTIFACT_DIR = Path(__file__).parent / "artifacts"


def _read_rows(csv_path: str | Path) -> tuple[list[str], list[str]]:
    messages: list[str] = []
    categories: list[str] = []
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            message = (row.get("Customer Message") or row.get("message") or "").strip()
            category = (row.get("Category") or row.get("category") or "").strip()
            if message and category:
                messages.append(preprocess_text(message))
                categories.append(category)
    if len(set(categories)) < 2:
        raise ValueError("Training data must contain at least two categories")
    return messages, categories


def train_pipeline(
    csv_path: str | Path = DATA_PATH,
    artifact_dir: str | Path = ARTIFACT_DIR,
    return_metrics: bool = False,
) -> Path | tuple[Path, float, int]:
    messages, categories = _read_rows(csv_path)
    test_count = min(
        max(len(set(categories)), round(len(categories) * 0.2)),
        len(categories) - 2,
    )
    can_stratify = min(categories.count(category) for category in set(categories)) >= 2
    x_train, x_test, y_train, y_test = train_test_split(
        messages,
        categories,
        test_size=test_count,
        random_state=42,
        stratify=categories if can_stratify else None,
    )
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
            ("classifier", LogisticRegression(max_iter=1500, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    accuracy = float(accuracy_score(y_test, predictions))
    print(f"Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, predictions, zero_division=0))
    pipeline.fit(messages, categories)
    output = Path(artifact_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "support_classifier.joblib"
    joblib.dump(pipeline, artifact)
    return (artifact, accuracy, len(messages)) if return_metrics else artifact


def ensure_model() -> Path:
    artifact = ARTIFACT_DIR / "support_classifier.joblib"
    return artifact if artifact.exists() else train_pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the customer support category model")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=ARTIFACT_DIR)
    arguments = parser.parse_args()
    train_pipeline(arguments.data, arguments.output)
