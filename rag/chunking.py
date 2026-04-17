"""Text chunking policy.

Strategy: paragraph-aware windowing with a character budget and a small
overlap. Keeps section headers with the following body so retrieval stays
coherent. Metadata is attached per chunk.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class Chunk:
    text: str
    order: int
    metadata: dict


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in text.replace("\r", "").split("\n\n")]
    return [p for p in parts if p]


def chunk_text(
    text: str,
    *,
    max_chars: int = 1200,
    overlap_chars: int = 150,
    base_metadata: dict | None = None,
) -> list[Chunk]:
    base = dict(base_metadata or {})
    paras = _split_paragraphs(text)
    chunks: list[Chunk] = []
    buf = ""
    order = 0
    for p in paras:
        if not buf:
            buf = p
            continue
        if len(buf) + 2 + len(p) <= max_chars:
            buf = f"{buf}\n\n{p}"
        else:
            chunks.append(Chunk(text=buf, order=order, metadata=base))
            order += 1
            # carry overlap from tail of previous buffer
            tail = buf[-overlap_chars:] if overlap_chars > 0 else ""
            buf = f"{tail}\n\n{p}" if tail else p
    if buf:
        chunks.append(Chunk(text=buf, order=order, metadata=base))
    return chunks


def batched(items: Iterable, n: int) -> Iterable[list]:
    batch: list = []
    for x in items:
        batch.append(x)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch
