"""Embedding + vector store abstraction.

Default implementation uses sentence-transformers + FAISS (CPU). Designed
to be swapped: any class exposing ``add(texts, metadatas)`` and
``search(query, k)`` satisfies the ``Retriever`` contract.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Hit:
    text: str
    score: float
    metadata: dict[str, Any]


class EmbedStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 path: str | Path = "data/processed/faiss_index"):
        self.path = Path(path)
        self.model_name = model_name
        self._model = None
        self._index = None
        self._meta: list[dict[str, Any]] = []
        self._texts: list[str] = []

    # --- lazy deps -------------------------------------------------------
    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def _ensure_index(self, dim: int):
        if self._index is None:
            import faiss
            self._index = faiss.IndexFlatIP(dim)

    # --- api -------------------------------------------------------------
    def add(self, texts: list[str], metadatas: list[dict[str, Any]]) -> None:
        if len(texts) != len(metadatas):
            raise ValueError("texts/metadatas length mismatch")
        self._ensure_model()
        import numpy as np
        vecs = self._model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        self._ensure_index(vecs.shape[1])
        self._index.add(vecs.astype(np.float32))
        self._texts.extend(texts)
        self._meta.extend(metadatas)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        if self._index is None or not self._texts:
            return []
        self._ensure_model()
        import numpy as np
        q = self._model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
        scores, idxs = self._index.search(q, k)
        out: list[Hit] = []
        for score, i in zip(scores[0].tolist(), idxs[0].tolist()):
            if i < 0:
                continue
            out.append(Hit(text=self._texts[i], score=float(score), metadata=self._meta[i]))
        return out

    # --- persistence -----------------------------------------------------
    def save(self) -> None:
        import faiss
        self.path.mkdir(parents=True, exist_ok=True)
        if self._index is not None:
            faiss.write_index(self._index, str(self.path / "index.faiss"))
        with (self.path / "meta.jsonl").open("w", encoding="utf-8") as f:
            for text, meta in zip(self._texts, self._meta):
                f.write(json.dumps({"text": text, "meta": meta}) + "\n")

    def load(self) -> None:
        import faiss
        idx_path = self.path / "index.faiss"
        meta_path = self.path / "meta.jsonl"
        if not idx_path.exists() or not meta_path.exists():
            return
        self._index = faiss.read_index(str(idx_path))
        self._texts, self._meta = [], []
        with meta_path.open("r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                self._texts.append(row["text"])
                self._meta.append(row["meta"])


def hit_to_evidence(h: Hit) -> dict[str, Any]:
    return {
        "title": h.metadata.get("title", "source"),
        "snippet": h.text[:400],
        "source_id": h.metadata.get("source_id", h.metadata.get("path", "unknown")),
    }
