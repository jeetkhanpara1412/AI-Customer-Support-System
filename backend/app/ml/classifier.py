from pathlib import Path

import joblib

from app.ml.preprocess import preprocess_text

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "support_classifier.joblib"


class SupportCategoryClassifier:
    def __init__(self, artifact_path: str | Path = ARTIFACT_PATH):
        self.artifact_path = Path(artifact_path)
        if not self.artifact_path.exists():
            raise FileNotFoundError(f"Trained classifier artifact not found: {self.artifact_path}")
        self.pipeline = joblib.load(self.artifact_path)

    def preprocess(self, message: str) -> str:
        return preprocess_text(message)

    def predict(self, message: str, preprocessed_text: str | None = None) -> tuple[str, float]:
        text = preprocessed_text if preprocessed_text is not None else self.preprocess(message)
        if not text:
            return "General Inquiry", 0.0
        probabilities = self.pipeline.predict_proba([text])[0]
        return str(self.pipeline.classes_[probabilities.argmax()]), float(probabilities.max())
