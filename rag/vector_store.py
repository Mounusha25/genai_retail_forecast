from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings

logger = logging.getLogger(__name__)


def _make_embeddings():
    """Return an embedding model based on EMBEDDING_PROVIDER setting."""
    cfg = get_settings()
    if cfg.embedding_provider == "local":
        from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore[import]

        return HuggingFaceEmbeddings(model_name=cfg.huggingface_embed_model)
    else:
        from langchain_openai import OpenAIEmbeddings  # type: ignore[import]

        return OpenAIEmbeddings(
            model=cfg.openai_embed_model,
            openai_api_key=cfg.openai_api_key,
            request_timeout=cfg.openai_request_timeout,
            max_retries=3,
        )


def build_vector_store(docs_dir: str | None = None) -> FAISS:
    """
    Load all PDF / TXT / MD files from *docs_dir*, chunk them, embed
    with OpenAI, and persist a FAISS index to disk.

    Returns:
        The in-memory FAISS store (also saved to disk).
    """
    cfg = get_settings()
    src_dir = docs_dir or cfg.docs_dir
    idx_dir = Path(cfg.faiss_index_path)

    # ── 1. Load documents ──────────────────────────────────────
    loaders = [
        DirectoryLoader(src_dir, glob="**/*.pdf", loader_cls=PyPDFLoader, silent_errors=True),  # type: ignore[arg-type]
        DirectoryLoader(src_dir, glob="**/*.txt", loader_cls=TextLoader, silent_errors=True),
        DirectoryLoader(src_dir, glob="**/*.md", loader_cls=TextLoader, silent_errors=True),
    ]
    raw_docs = []
    for ldr in loaders:
        raw_docs.extend(ldr.load())

    if not raw_docs:
        raise FileNotFoundError(f"No documents found in {src_dir!r}")

    logger.info("Loaded %d raw documents from %s", len(raw_docs), src_dir)

    # ── 2. Chunk ───────────────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)
    logger.info("Split into %d chunks (size=%d overlap=%d)", len(chunks), cfg.chunk_size, cfg.chunk_overlap)

    # ── 3. Embed & build FAISS index ───────────────────────────
    embeddings = _make_embeddings()
    store = FAISS.from_documents(chunks, embeddings)

    # ── 4. Persist ─────────────────────────────────────────────
    idx_dir.mkdir(parents=True, exist_ok=True)
    store.save_local(str(idx_dir))
    logger.info("FAISS index saved to %s (%d vectors)", idx_dir, store.index.ntotal)

    return store


def load_vector_store() -> FAISS:
    """Load an existing FAISS index from disk."""
    cfg = get_settings()
    idx_dir = Path(cfg.faiss_index_path)

    if not idx_dir.exists():
        raise FileNotFoundError(f"FAISS index not found at {idx_dir}. Run `python -m scripts.build_index` first.")

    embeddings = _make_embeddings()
    store = FAISS.load_local(
        str(idx_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    logger.info("FAISS index loaded from %s (%d vectors)", idx_dir, store.index.ntotal)
    return store
