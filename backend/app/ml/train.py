import argparse
import csv
from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

from app.ml.classifier import hybrid_features
from app.ml.embeddings import Encoder, MODEL_NAME, get_encoder
from app.ml.preprocess import correct_common_typos

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
                messages.append(correct_common_typos(message))
                categories.append(category)
    counts = {category: categories.count(category) for category in set(categories)}
    if len(counts) < 2 or min(counts.values()) < 4:
        raise ValueError("Training data must contain at least two categories and four examples per category")
    return messages, categories


def train_pipeline(
    csv_path: str | Path = DATA_PATH,
    artifact_dir: str | Path = ARTIFACT_DIR,
    return_metrics: bool = False,
    encoder: Encoder | None = None,
) -> Path | tuple[Path, float, int]:
    messages, categories = _read_rows(csv_path)
    model = encoder or get_encoder()
    char_vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True,
    )
    char_vectorizer.fit(messages)
    features = hybrid_features(messages, char_vectorizer, model)
    test_count = min(
        max(len(set(categories)), round(len(categories) * 0.2)),
        len(categories) - 2,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        categories,
        test_size=test_count,
        random_state=42,
        stratify=categories,
    )
    base_classifier = LogisticRegression(max_iter=2000, class_weight="balanced")
    validation_classifier = CalibratedClassifierCV(
        estimator=base_classifier,
        method="sigmoid",
        cv=3,
    )
    validation_classifier.fit(x_train, y_train)
    predictions = validation_classifier.predict(x_test)
    accuracy = float(accuracy_score(y_test, predictions))
    print(f"Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, predictions, zero_division=0))
    final_classifier = CalibratedClassifierCV(
        estimator=LogisticRegression(max_iter=2000, class_weight="balanced"),
        method="sigmoid",
        cv=3,
    )
    final_classifier.fit(features, categories)
    output = Path(artifact_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "support_classifier.joblib"
    joblib.dump(
        {
            "classifier": final_classifier,
            "char_vectorizer": char_vectorizer,
            "model_name": MODEL_NAME,
        },
        artifact,
    )
    return (artifact, accuracy, len(messages)) if return_metrics else artifact


def ensure_model() -> Path:
    artifact = ARTIFACT_DIR / "support_classifier.joblib"
    if artifact.exists():
        try:
            saved = joblib.load(artifact)
            if (
                isinstance(saved, dict)
                and "classifier" in saved
                and "char_vectorizer" in saved
                and saved.get("model_name") == MODEL_NAME
            ):
                return artifact
        except (OSError, ValueError, EOFError):
            pass
    return train_pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the customer support category model")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=ARTIFACT_DIR)
    arguments = parser.parse_args()
    train_pipeline(arguments.data, arguments.output)
