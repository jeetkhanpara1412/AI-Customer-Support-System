import csv
import hashlib
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from app.ml.embeddings import MODEL_NAME, Encoder, encode_texts
from app.ml.preprocess import correct_common_typos

EMBEDDING_CACHE_PATH = Path(__file__).parent / "artifacts" / "knowledge_embeddings.joblib"


@dataclass(frozen=True)
class KnowledgeMatch:
    id: int
    message: str
    category: str
    response: str
    score: float


@dataclass(frozen=True)
class KnowledgeRow:
    id: int
    message: str
    category: str
    response: str


class TicketRetriever:
    def __init__(
        self,
        knowledge_base: str | Path | Iterable[object],
        encoder: Encoder | None = None,
        cache_path: str | Path = EMBEDDING_CACHE_PATH,
    ):
        self.knowledge_base_path = Path(knowledge_base) if isinstance(knowledge_base, (str, Path)) else None
        self.encoder = encoder
        self.cache_path = Path(cache_path)
        self.rows: list[KnowledgeRow] = []
        self.embeddings = np.empty((0, 384), dtype=np.float32)
        self.reload(knowledge_base)

    @staticmethod
    def _read_rows(source: str | Path | Iterable[object]) -> list[KnowledgeRow]:
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Knowledge base not found: {path}")
            with path.open(encoding="utf-8-sig", newline="") as handle:
                return [
                    KnowledgeRow(
                        id=index,
                        message=(row.get("Customer Message") or row.get("message") or "").strip(),
                        category=(row.get("Category") or row.get("category") or "General Inquiry").strip(),
                        response=(row.get("Company Response") or row.get("response") or "").strip(),
                    )
                    for index, row in enumerate(csv.DictReader(handle), start=1)
                    if (row.get("Customer Message") or row.get("message") or "").strip()
                ]
        rows: list[KnowledgeRow] = []
        for item in source:
            rows.append(
                KnowledgeRow(
                    id=int(item.id),
                    message=str(item.message).strip(),
                    category=str(item.category).strip(),
                    response=str(item.response).strip(),
                )
            )
        return [row for row in rows if row.message and row.category and row.response]

    @staticmethod
    def _fingerprint(row: KnowledgeRow) -> str:
        value = "\0".join((row.message, row.category))
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def reload(self, knowledge_base: str | Path | Iterable[object] | None = None) -> None:
        source = knowledge_base if knowledge_base is not None else self.knowledge_base_path
        if source is None:
            raise ValueError("Knowledge entries are required to rebuild the index")
        rows = self._read_rows(source)
        if not rows:
            raise ValueError("Knowledge base contains no valid entries")
        previous: dict[int, dict[str, object]] = {}
        if self.cache_path.exists():
            cached = joblib.load(self.cache_path)
            if cached.get("model_name") == MODEL_NAME:
                previous = cached.get("entries", {})

        embeddings: list[np.ndarray | None] = [None] * len(rows)
        missing_indices: list[int] = []
        for index, row in enumerate(rows):
            cached_entry = previous.get(row.id)
            if cached_entry and cached_entry.get("fingerprint") == self._fingerprint(row):
                embeddings[index] = np.asarray(cached_entry["embedding"], dtype=np.float32)
            else:
                missing_indices.append(index)
        if missing_indices:
            new_vectors = encode_texts(
                [correct_common_typos(rows[index].message) for index in missing_indices],
                self.encoder,
            )
            for index, vector in zip(missing_indices, new_vectors, strict=True):
                embeddings[index] = vector

        self.rows = rows
        self.embeddings = np.vstack(embeddings).astype(np.float32)
        entries = {
            row.id: {
                "fingerprint": self._fingerprint(row),
                "embedding": self.embeddings[index],
            }
            for index, row in enumerate(rows)
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=self.cache_path.parent,
            prefix=f".{self.cache_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        try:
            joblib.dump({"model_name": MODEL_NAME, "entries": entries}, temporary_path)
            os.replace(temporary_path, self.cache_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def retrieve(
        self,
        message: str,
        top_k: int = 3,
        category: str | None = None,
    ) -> list[KnowledgeMatch]:
        if not message.strip():
            return []
        indexes = [
            index for index, row in enumerate(self.rows)
            if category is None or row.category == category
        ]
        if not indexes:
            return []
        query = encode_texts([correct_common_typos(message)], self.encoder)[0]
        scores = self.embeddings[indexes] @ query
        order = np.argsort(scores)[::-1][:max(top_k, 0)]
        return [
            KnowledgeMatch(
                id=self.rows[indexes[position]].id,
                message=self.rows[indexes[position]].message,
                category=self.rows[indexes[position]].category,
                response=self.rows[indexes[position]].response,
                score=float(scores[position]),
            )
            for position in order
        ]
