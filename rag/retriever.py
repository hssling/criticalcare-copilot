"""Retriever interface.

Kept thin and pluggable: any object with a ``search(query, k)`` method
returning objects with ``text``, ``score``, ``metadata`` attributes works.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .embed_store import EmbedStore, Hit, hit_to_evidence


@runtime_checkable
class _SearchLike(Protocol):
    def search(self, query: str, k: int = 5) -> list[Hit]: ...


class Retriever:
    def __init__(self, backend: _SearchLike | None = None, k: int = 5):
        self._backend = backend
        self._k = k

    @classmethod
    def from_default(cls, path: str = "data/processed/faiss_index", k: int = 5) -> "Retriever":
        store = EmbedStore(path=path)
        store.load()
        return cls(backend=store, k=k)

    def retrieve_evidence(self, query: str) -> list[dict]:
        if self._backend is None:
            return []
        hits = self._backend.search(query, k=self._k)
        return [hit_to_evidence(h) for h in hits]
