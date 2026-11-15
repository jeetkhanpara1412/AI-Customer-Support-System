from pathlib import Path
from typing import Any

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer

from app.ml.embeddings import MODEL_NAME, Encoder, encode_texts, get_encoder
from app.ml.preprocess import correct_common_typos, preprocess_text

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "support_classifier.joblib"


def hybrid_features(
    messages: list[str],
    char_vectorizer: TfidfVectorizer,
    encoder: Encoder | None = None,
) -> Any:
    corrected = [correct_common_typos(message) for message in messages]
    semantic = csr_matrix(encode_texts(corrected, encoder))
    character = char_vectorizer.transform(corrected)
    return hstack((semantic, character), format="csr")


class SupportCategoryClassifier:
    def __init__(
        self,
        artifact_path: str | Path = ARTIFACT_PATH,
        encoder: Encoder | None = None,
    ):
        self.artifact_path = Path(artifact_path)
        if not self.artifact_path.exists():
            raise FileNotFoundError(
                f"Trained classifier artifact not found: {self.artifact_path}"
            )
        artifact = joblib.load(self.artifact_path)
        self.pipeline = artifact["classifier"]
        self.char_vectorizer = artifact["char_vectorizer"]
        self.encoder = encoder or get_encoder(artifact.get("model_name", MODEL_NAME))

    def preprocess(self, message: str) -> str:
        return preprocess_text(message)

    def predict_top_k(self, message: str, top_k: int = 3) -> list[tuple[str, float]]:
        cleaned = correct_common_typos(message.strip())
        if not cleaned:
            return [("Out of Scope", 1.0)]
        probabilities = self.pipeline.predict_proba(
            hybrid_features([cleaned], self.char_vectorizer, self.encoder)
        )[0]
        count = min(max(top_k, 1), len(self.pipeline.classes_))
        order = np.argsort(probabilities)[::-1][:count]
        return [
            (str(self.pipeline.classes_[index]), float(probabilities[index]))
            for index in order
        ]

    def predict(
        self,
        message: str,
        preprocessed_text: str | None = None,
    ) -> tuple[str, float]:
        del preprocessed_text
        return self.predict_top_k(message, top_k=1)[0]
