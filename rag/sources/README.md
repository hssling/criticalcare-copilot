# RAG sources

Drop local protocols, unit guidelines, medication monographs, and checklists here (`.md`, `.txt`, `.pdf`).

**Do not commit proprietary or restricted material unless licensing permits.** This directory is intended for your institution's own content and public-domain references.

Index with:

```bash
python -m rag.ingest_documents --sources rag/sources --out data/processed/faiss_index
```
