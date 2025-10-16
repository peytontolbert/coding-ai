### Semantic search over CodeGraph

MVP:
- Use a small embedding model to index file chunks + symbol docs.
- Store vectors in a local FAISS/SQLite-vec index.
- Retrieve top-k per objective and feed into planner context.

Upgrades:
- Hybrid retrieval: BM25 (ripgrep/ctags) + embeddings rerank.


