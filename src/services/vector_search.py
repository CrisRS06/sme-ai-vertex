"""
Vector search service abstraction.
Supports Vertex AI Vector Search (Tree-AH/ScaNN) with a SQLite fallback for local dev.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import structlog
from google.api_core.exceptions import FailedPrecondition, NotFound
from google.cloud.aiplatform.matching_engine import (
    MatchEngineIndexDatapoint,
    MatchEngineProxyDatapointRestriction,
)

from src.config.gcp_clients import (
    get_vector_search_endpoint,
    get_vector_search_index,
    init_vertex_ai,
)
from src.config.settings import settings
from src.services.vector_registry import get_vector_registry

logger = structlog.get_logger()


@dataclass
class VectorSearchResult:
    """Normalized representation of un resultado de búsqueda vectorial."""

    document_id: str
    page_number: Optional[int]
    gcs_uri: Optional[str]
    similarity: float
    metadata: Dict[str, Any]


class BaseVectorSearchService:
    """Interfaz básica para operaciones de vector search."""

    def store_embeddings(
        self,
        document_id: str,
        embeddings: Sequence[Tuple[int, str, np.ndarray, Dict[str, Any]]],
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def search_similar(
        self,
        query_embedding: np.ndarray,
        *,
        top_k: int = 10,
        min_similarity: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:  # pragma: no cover - interface
        raise NotImplementedError

    def delete_document_embeddings(self, document_id: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def get_document_embeddings(
        self, document_id: str
    ) -> List[Tuple[int, np.ndarray, Dict[str, Any]]]:  # pragma: no cover
        raise NotImplementedError


class VertexAIVectorSearchService(BaseVectorSearchService):
    """
    Implementación gestionada usando Vertex AI Vector Search.
    Requiere index + endpoint + deployed index configurados en settings.
    """

    def __init__(self):
        init_vertex_ai()
        self.index = get_vector_search_index()
        self.endpoint = get_vector_search_endpoint()
        self.deployed_index_id = getattr(settings, "vector_search_deployed_index_id", "")

        if not all([self.index, self.endpoint, self.deployed_index_id]):
            missing = []
            if not self.index:
                missing.append("vector_search_index_id")
            if not self.endpoint:
                missing.append("vector_search_endpoint_id")
            if not self.deployed_index_id:
                missing.append("vector_search_deployed_index_id")
            raise RuntimeError(
                "Vertex AI Vector Search no está completamente configurado. "
                f"Faltan: {', '.join(missing)}"
            )

        logger.info(
            "vertex_ai_vector_search_initialized",
            index=self.index.resource_name,
            endpoint=self.endpoint.resource_name,
            deployed_index_id=self.deployed_index_id,
        )

    def store_embeddings(
        self,
        document_id: str,
        embeddings: Sequence[Tuple[int, str, np.ndarray, Dict[str, Any]]],
    ) -> None:
        registry = get_vector_registry()
        datapoints = []
        for page_number, gcs_uri, embedding, metadata in embeddings:
            datapoint_id = f"{document_id}__{page_number}"
            restricts = []
            for key, value in (metadata or {}).items():
                if value is None:
                    continue
                restricts.append(
                    MatchEngineProxyDatapointRestriction(
                        namespace=key,
                        allow_tokens=[str(value)],
                    )
                )

            datapoints.append(
                MatchEngineIndexDatapoint(
                    datapoint_id=datapoint_id,
                    feature_vector=np.asarray(embedding, dtype=np.float32),
                    restricts=restricts,
                )
            )

        if not datapoints:
            logger.warning("vertex_ai_no_embeddings_to_store", document_id=document_id)
            return

        logger.info(
            "vertex_ai_upsert_embeddings",
            document_id=document_id,
            count=len(datapoints),
        )

        try:
            self.index.upsert_datapoints(datapoints=datapoints)
        except (FailedPrecondition, NotFound) as exc:
            logger.error("vertex_ai_upsert_failed", error=str(exc))
            raise

        registry.save_embeddings(document_id, embeddings)

    def search_similar(
        self,
        query_embedding: np.ndarray,
        *,
        top_k: int = 10,
        min_similarity: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        filter_configs = []
        if filter_metadata:
            for key, value in filter_metadata.items():
                filter_configs.append(
                    MatchEngineProxyDatapointRestriction(
                        namespace=key,
                        allow_tokens=[str(value)],
                    )
                )

        response = self.endpoint.find_neighbors(
            deployed_index_id=self.deployed_index_id,
            queries=[
                {
                    "feature_vector": np.asarray(query_embedding, dtype=np.float32),
                    "neighbor_count": top_k,
                    "restricts": filter_configs,
                }
            ],
        )

        if not response.nearest_neighbors:
            return []

        results: List[VectorSearchResult] = []
        for neighbor in response.nearest_neighbors[0].neighbors:
            similarity = neighbor.distance
            if similarity < min_similarity:
                continue

            metadata = {}
            for restrict in neighbor.restricts:
                metadata[restrict.namespace] = restrict.allow_tokens[0]

            datapoint_id = neighbor.datapoint.datapoint_id
            doc_id, _, page = datapoint_id.partition("__")
            page_number = int(page) if page else None

            results.append(
                VectorSearchResult(
                    document_id=doc_id,
                    page_number=page_number,
                    gcs_uri=metadata.get("gcs_uri"),
                    similarity=similarity,
                    metadata=metadata,
                )
            )

        logger.info(
            "vertex_ai_similarity_search_completed",
            results_count=len(results),
            top_similarity=results[0].similarity if results else None,
        )
        return results

    def delete_document_embeddings(self, document_id: str) -> bool:
        datapoint_ids = self._list_document_datapoint_ids(document_id)
        if not datapoint_ids:
            return False

        self.index.remove_datapoints(datapoint_ids=datapoint_ids)
        get_vector_registry().delete_document(document_id)
        logger.info(
            "vertex_ai_embeddings_deleted",
            document_id=document_id,
            count=len(datapoint_ids),
        )
        return True

    def _list_document_datapoint_ids(self, document_id: str) -> List[str]:
        logger.warning(
            "vertex_ai_list_datapoints_not_implemented",
            document_id=document_id,
        )
        return []

    def get_stats(self) -> Dict[str, Any]:
        return {
            "mode": "vertex_ai",
            "index": self.index.resource_name,
            "endpoint": self.endpoint.resource_name,
        }

    def get_document_embeddings(
        self, document_id: str
    ) -> List[Tuple[int, np.ndarray, Dict[str, Any]]]:
        registry = get_vector_registry()
        embeddings = registry.get_embeddings(document_id)
        if not embeddings:
            raise NotImplementedError(
                "No hay embeddings en el registro local. Ejecute la migración o regenere."
            )
        return embeddings


class SQLiteVectorSearchService(BaseVectorSearchService):
    """
    Implementación local basada en SQLite para entornos de desarrollo.
    """

    def __init__(self, db_path: str = "data/vector_search.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info("sqlite_vector_search_initialized", db_path=db_path)

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                page_number INTEGER,
                gcs_uri TEXT,
                embedding_json TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_embeddings_document
            ON embeddings(document_id)
            """
        )
        conn.commit()
        conn.close()

    def store_embeddings(
        self,
        document_id: str,
        embeddings: Sequence[Tuple[int, str, np.ndarray, Dict[str, Any]]],
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for page_number, gcs_uri, embedding, metadata in embeddings:
            cursor.execute(
                """
                INSERT INTO embeddings (document_id, page_number, gcs_uri, embedding_json, metadata)
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
        logger.info(
            "sqlite_embeddings_stored",
            document_id=document_id,
            count=len(embeddings),
        )

    def search_similar(
        self,
        query_embedding: np.ndarray,
        *,
        top_k: int = 10,
        min_similarity: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM embeddings")
        rows = cursor.fetchall()
        conn.close()

        results: List[VectorSearchResult] = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            if filter_metadata and not all(
                metadata.get(k) == v for k, v in filter_metadata.items()
            ):
                continue

            stored_embedding = np.asarray(json.loads(row["embedding_json"]))
            similarity = self._cosine_similarity(query_embedding, stored_embedding)
            if similarity < min_similarity:
                continue

            results.append(
                VectorSearchResult(
                    document_id=row["document_id"],
                    page_number=row["page_number"],
                    gcs_uri=row["gcs_uri"],
                    similarity=float(similarity),
                    metadata=metadata,
                )
            )

        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:top_k]

    def delete_document_embeddings(self, document_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        if deleted:
            logger.info("sqlite_embeddings_deleted", document_id=document_id)
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM embeddings")
        docs = cursor.fetchone()[0]
        conn.close()
        return {
            "mode": "sqlite_fallback",
            "total_embeddings": total,
            "unique_documents": docs,
        }

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def get_document_embeddings(
        self, document_id: str
    ) -> List[Tuple[int, np.ndarray, Dict[str, Any]]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT page_number, embedding_json, metadata FROM embeddings WHERE document_id = ? ORDER BY page_number",
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


_vector_search: Optional[BaseVectorSearchService] = None


def get_vector_search() -> BaseVectorSearchService:
    """
    Obtiene la instancia singleton de vector search.
    """
    global _vector_search
    if _vector_search is not None:
        return _vector_search

    if settings.vector_search_endpoint_id and settings.vector_search_index_id:
        try:
            _vector_search = VertexAIVectorSearchService()
        except RuntimeError as exc:
            logger.warning(
                "vertex_ai_vector_search_unavailable_fallback_sqlite",
                error=str(exc),
            )
            _vector_search = SQLiteVectorSearchService()
    else:
        _vector_search = SQLiteVectorSearchService()

    return _vector_search
