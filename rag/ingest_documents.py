"""Ingest local protocol/guideline/monograph documents into a vector store.

Supports: .md, .txt, .pdf (via pypdf if available).

Usage:
    python -m rag.ingest_documents --sources rag/sources --out data/processed/faiss_index
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .chunking import chunk_text
from .embed_store import EmbedStore


def _read(path: Path) -> str:
    if path.suffix.lower() in (".md", ".txt"):
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as e:
            raise SystemExit(f"pypdf not installed; cannot read {path}: {e}")
        reader = PdfReader(str(path))
        return "\n\n".join((p.extract_text() or "") for p in reader.pages)
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="rag/sources")
    ap.add_argument("--out", default="data/processed/faiss_index")
    ap.add_argument("--embed-model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    store = EmbedStore(model_name=args.embed_model, path=args.out)
    src = Path(args.sources)
    files = [p for p in src.rglob("*") if p.suffix.lower() in (".md", ".txt", ".pdf") and p.is_file()]
    if not files:
        print(f"[ingest] no files under {src}")
        return

    texts: list[str] = []
    metas: list[dict] = []
    for f in files:
        raw = _read(f)
        if not raw.strip():
            continue
        for c in chunk_text(raw, base_metadata={
            "title": f.stem, "path": str(f), "source_id": f.stem,
        }):
            texts.append(c.text)
            metas.append({**c.metadata, "order": c.order})

    if not texts:
        print("[ingest] nothing to index")
        return

    store.add(texts, metas)
    store.save()
    print(f"[ingest] indexed {len(texts)} chunks from {len(files)} files -> {args.out}")


if __name__ == "__main__":
    main()
