"""
Vector embedding registry for interoperability between Vertex AI Vector Search and local features.
Stores per-page embedding metadata (and optional vectors) in SQLite.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import structlog

logger = structlog.get_logger()


class VectorRegistry:
    def __init__(self, db_path: str = "data/vector_registry.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                gcs_uri TEXT,
                embedding_json TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, page_number)
            )
            """
        )
        conn.commit()
        conn.close()

    def save_embeddings(
        self,
        document_id: str,
        embeddings: Sequence[Tuple[int, str, np.ndarray, Dict[str, Any]]],
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for page_number, gcs_uri, embedding, metadata in embeddings:
            cursor.execute(
                """
                INSERT OR REPLACE INTO embeddings
                (document_id, page_number, gcs_uri, embedding_json, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    page_number,
                    gcs_uri,
                    json.dumps(np.asarray(embedding).tolist()),
                    json.dumps(metadata or {}),
                ),
            )
        conn.commit()
        conn.close()

    def get_embeddings(
        self, document_id: str
    ) -> List[Tuple[int, np.ndarray, Dict[str, Any]]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT page_number, embedding_json, metadata
            FROM embeddings
            WHERE document_id = ?
            ORDER BY page_number
            """,
            (document_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        results: List[Tuple[int, np.ndarray, Dict[str, Any]]] = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            results.append(
                (
                    row["page_number"],
                    np.asarray(json.loads(row["embedding_json"])),
                    metadata,
                )
            )
        return results

    def delete_document(self, document_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
        conn.commit()
        conn.close()

    def get_stats(self) -> Dict[str, any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM embeddings")
        docs = cursor.fetchone()[0]
        conn.close()
        return {"total_embeddings": total, "unique_documents": docs}


_registry: Optional[VectorRegistry] = None


def get_vector_registry() -> VectorRegistry:
    global _registry
    if _registry is None:
        _registry = VectorRegistry()
    return _registry
