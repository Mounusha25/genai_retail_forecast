"""
Utility script: embed all business documents and persist the FAISS index.

Usage:
    python -m scripts.build_index [--docs-dir data/business_docs]
"""

from __future__ import annotations

import argparse
import sys

from rag.vector_store import build_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS embedding index from business docs")
    parser.add_argument("--docs-dir", default=None, help="Override docs directory")
    args = parser.parse_args()

    try:
        store = build_vector_store(docs_dir=args.docs_dir)
        print(f"Index built successfully — {store.index.ntotal} vectors")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
