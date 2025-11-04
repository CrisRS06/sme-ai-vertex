"""
Migration script to push existing embeddings from SQLite fallback into Vertex AI Vector Search.

Usage:
    python scripts/migrate_embeddings_to_vertex.py --batch-size 100

Requirements:
    - Environment variables set (see README/.env):
        * GCP_PROJECT_ID, GCP_LOCATION/REGION
        * VECTOR_SEARCH_INDEX_ID, VECTOR_SEARCH_ENDPOINT_ID, VECTOR_SEARCH_DEPLOYED_INDEX_ID
    - google-cloud-aiplatform >= 1.82.0 installed
"""
import argparse
import json
import os
import sqlite3
from typing import Dict, List, Tuple

import numpy as np
from dotenv import load_dotenv

from src.services.vector_search import VertexAIVectorSearchService
from src.services.vector_registry import get_vector_registry

SQLITE_PATH = "data/vector_search.db"


def load_sqlite_rows(limit: int | None = None) -> List[Tuple[str, int, str, np.ndarray, Dict]]:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT document_id, page_number, gcs_uri, embedding_json, metadata FROM embeddings ORDER BY document_id, page_number"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        embedding = np.asarray(json.loads(row["embedding_json"]), dtype=np.float32)
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        results.append(
            (
                row["document_id"],
                row["page_number"],
                row["gcs_uri"],
                embedding,
                metadata,
            )
        )
    return results


def migrate(batch_size: int, dry_run: bool) -> None:
    if dry_run:
        print("Running in DRY RUN mode. No changes will be written.")

    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f"SQLite fallback not found at {SQLITE_PATH}")

    registry = get_vector_registry()
    service = VertexAIVectorSearchService()

    rows = load_sqlite_rows()
    total = len(rows)
    print(f"Found {total} embeddings in SQLite fallback.")

    batch: List[Tuple[int, str, np.ndarray, Dict]] = []
    current_doc = None
    migrated = 0

    for doc_id, page_number, gcs_uri, embedding, metadata in rows:
        metadata = metadata or {}
        metadata.setdefault("gcs_uri", gcs_uri)
        metadata.setdefault("page_number", page_number)

        if current_doc is None:
            current_doc = doc_id

        if doc_id != current_doc or len(batch) >= batch_size:
            if not dry_run:
                service.store_embeddings(current_doc, batch)
                registry.save_embeddings(current_doc, batch)
            migrated += len(batch)
            print(f"Migrated {len(batch)} embeddings for document {current_doc}")
            batch = []
            current_doc = doc_id

        batch.append((page_number, gcs_uri, embedding, metadata))

    if batch:
        if not dry_run:
            service.store_embeddings(current_doc, batch)
            registry.save_embeddings(current_doc, batch)
        migrated += len(batch)
        print(f"Migrated {len(batch)} embeddings for document {current_doc}")

    print(f"Migration finished. Migrated embeddings: {migrated}/{total}")


def main():
    parser = argparse.ArgumentParser(description="Migrate embeddings from SQLite to Vertex AI Vector Search")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of embeddings to upsert per document")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to Vertex AI, only simulate")
    parser.add_argument("--env-file", type=str, default=".env", help="Path to environment file")
    args = parser.parse_args()

    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)

    migrate(args.batch_size, args.dry_run)


if __name__ == "__main__":
    main()
