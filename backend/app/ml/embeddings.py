from functools import lru_cache
from pathlib import Path
from typing import Protocol

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_CACHE = Path(__file__).parent / "artifacts" / "transformers"


class Encoder(Protocol):
    def encode(self, sentences: list[str], **kwargs: object) -> np.ndarray: ...


@lru_cache(maxsize=1)
def get_encoder(model_name: str = MODEL_NAME) -> Encoder:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        model_name,
        cache_folder=str(MODEL_CACHE),
        trust_remote_code=False,
        device="cpu",
    )


def encode_texts(texts: list[str], encoder: Encoder | None = None) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = encoder or get_encoder()
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)
