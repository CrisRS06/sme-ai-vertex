"""
RAG Evaluation Service
Implements Vertex AI evaluation metrics for RAG quality assessment.

Based on Vertex AI best practices (GA 2025):
- Groundedness: Response based on retrieved documents
- Relevance: Response answers the query
- Coherence: Response is logically consistent
- Fluency: Response is well-written
- Safety: No harmful content
"""
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from src.config.settings import settings
from src.config.gcp_clients import init_vertex_ai

logger = structlog.get_logger()


class RAGEvaluationService:
    """
    Service for evaluating RAG system quality using Vertex AI metrics.

    Implements comprehensive evaluation as recommended in:
    https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluate-models
    """

    def __init__(self):
        """Initialize evaluation service."""
        init_vertex_ai()
        logger.info("rag_evaluation_service_initialized")

    async def evaluate_response(
        self,
        query: str,
        response: str,
        retrieved_docs: List[str],
        reference_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a RAG response using Vertex AI metrics.

        Args:
            query: User's original query
            response: Generated response
            retrieved_docs: List of retrieved document chunks
            reference_answer: Optional ground truth answer

        Returns:
            Dictionary with evaluation scores and metrics
        """
        try:
            # Import Vertex AI evaluation (GA 2025)
            from vertexai.evaluation import EvalTask

            # Prepare evaluation dataset
            eval_data = {
                "query": query,
                "response": response,
                "context": "\n\n".join(retrieved_docs),
            }

            if reference_answer:
                eval_data["reference"] = reference_answer

            # Define metrics to evaluate
            metrics = [
                "groundedness",  # Response based on retrieved docs
                "relevance",     # Response answers the query
                "coherence",     # Response is logically consistent
                "fluency",       # Response is well-written
                "safety"         # No harmful content
            ]

            # Create evaluation task
            eval_task = EvalTask(
                dataset=[eval_data],
                metrics=metrics
            )

            # Run evaluation
            results = eval_task.evaluate()

            # Extract scores
            scores = {
                "groundedness": self._extract_score(results, "groundedness"),
                "relevance": self._extract_score(results, "relevance"),
                "coherence": self._extract_score(results, "coherence"),
                "fluency": self._extract_score(results, "fluency"),
                "safety": self._extract_score(results, "safety"),
                "overall_quality": self._calculate_overall_quality(results),
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info(
                "rag_response_evaluated",
                groundedness=scores["groundedness"],
                relevance=scores["relevance"],
                overall_quality=scores["overall_quality"]
            )

            return scores

        except ImportError as e:
            logger.warning(
                "vertex_ai_evaluation_not_available",
                error=str(e),
                fallback="using_heuristic_evaluation"
            )
            # Fallback to heuristic evaluation
            return self._heuristic_evaluation(query, response, retrieved_docs)

        except Exception as e:
            logger.error("rag_evaluation_failed", error=str(e))
            raise

    def _extract_score(self, results: Any, metric_name: str) -> float:
        """Extract score for a specific metric from evaluation results."""
        try:
            if hasattr(results, metric_name):
                return float(getattr(results, metric_name))
            return 0.0
        except Exception:
            return 0.0

    def _calculate_overall_quality(self, results: Any) -> float:
        """Calculate weighted overall quality score."""
        try:
            # Weighted average: groundedness and relevance are most important
            weights = {
                "groundedness": 0.35,
                "relevance": 0.35,
                "coherence": 0.15,
                "fluency": 0.10,
                "safety": 0.05
            }

            total_score = 0.0
            for metric, weight in weights.items():
                score = self._extract_score(results, metric)
                total_score += score * weight

            return round(total_score, 2)

        except Exception:
            return 0.0

    def _heuristic_evaluation(
        self,
        query: str,
        response: str,
        retrieved_docs: List[str]
    ) -> Dict[str, Any]:
        """
        Fallback heuristic evaluation when Vertex AI evaluation is not available.

        Uses simple heuristics to estimate quality scores.
        """
        try:
            # Groundedness: Check if response references retrieved docs
            groundedness = self._calculate_groundedness(response, retrieved_docs)

            # Relevance: Check if response relates to query
            relevance = self._calculate_relevance(query, response)

            # Coherence: Check basic structure
            coherence = self._calculate_coherence(response)

            # Fluency: Check readability
            fluency = self._calculate_fluency(response)

            # Safety: Basic checks
            safety = self._calculate_safety(response)

            # Overall quality
            overall = (
                groundedness * 0.35 +
                relevance * 0.35 +
                coherence * 0.15 +
                fluency * 0.10 +
                safety * 0.05
            )

            return {
                "groundedness": round(groundedness, 2),
                "relevance": round(relevance, 2),
                "coherence": round(coherence, 2),
                "fluency": round(fluency, 2),
                "safety": round(safety, 2),
                "overall_quality": round(overall, 2),
                "evaluated_at": datetime.now().isoformat(),
                "evaluation_method": "heuristic_fallback"
            }

        except Exception as e:
            logger.error("heuristic_evaluation_failed", error=str(e))
            return {
                "groundedness": 0.0,
                "relevance": 0.0,
                "coherence": 0.0,
                "fluency": 0.0,
                "safety": 0.0,
                "overall_quality": 0.0,
                "evaluated_at": datetime.now().isoformat(),
                "evaluation_method": "fallback_failed"
            }

    def _calculate_groundedness(self, response: str, retrieved_docs: List[str]) -> float:
        """Estimate groundedness using keyword overlap."""
        if not retrieved_docs or not response:
            return 0.0

        # Extract key terms from retrieved docs
        doc_text = " ".join(retrieved_docs).lower()
        response_lower = response.lower()

        # Split into words
        doc_words = set(doc_text.split())
        response_words = set(response_lower.split())

        # Calculate overlap (excluding common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        doc_words = doc_words - common_words
        response_words = response_words - common_words

        if not response_words:
            return 0.0

        overlap = len(doc_words.intersection(response_words))
        score = min(overlap / len(response_words), 1.0)

        return score

    def _calculate_relevance(self, query: str, response: str) -> float:
        """Estimate relevance using keyword overlap."""
        if not query or not response:
            return 0.0

        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        # Exclude common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        query_words = query_words - common_words
        response_words = response_words - common_words

        if not query_words:
            return 0.5  # Default score if query has no meaningful words

        overlap = len(query_words.intersection(response_words))
        score = min(overlap / len(query_words), 1.0)

        return score

    def _calculate_coherence(self, response: str) -> float:
        """Estimate coherence based on structure."""
        if not response:
            return 0.0

        # Basic checks for coherence
        checks = []

        # Has reasonable length (not too short, not too long)
        length_ok = 50 <= len(response) <= 5000
        checks.append(length_ok)

        # Has proper sentence structure (ends with punctuation)
        ends_with_punct = response.strip()[-1] in {'.', '!', '?'}
        checks.append(ends_with_punct)

        # Has multiple sentences
        sentence_count = response.count('.') + response.count('!') + response.count('?')
        has_multiple_sentences = sentence_count > 1
        checks.append(has_multiple_sentences)

        score = sum(checks) / len(checks)
        return score

    def _calculate_fluency(self, response: str) -> float:
        """Estimate fluency based on readability."""
        if not response:
            return 0.0

        # Basic fluency checks
        checks = []

        # Has reasonable word length
        words = response.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            word_length_ok = 3 <= avg_word_length <= 8
            checks.append(word_length_ok)

        # Has proper capitalization
        has_capital = any(c.isupper() for c in response)
        checks.append(has_capital)

        # Not too many very long words
        long_words = [w for w in words if len(w) > 15]
        too_many_long = len(long_words) / max(len(words), 1) < 0.15
        checks.append(too_many_long)

        score = sum(checks) / max(len(checks), 1)
        return score

    def _calculate_safety(self, response: str) -> float:
        """Basic safety check."""
        if not response:
            return 0.0

        # Very basic safety checks (production should use Vertex AI safety)
        unsafe_patterns = [
            'sudo rm',
            'DROP TABLE',
            'DELETE FROM',
            '<script>',
            'eval(',
            'exec(',
        ]

        response_lower = response.lower()
        for pattern in unsafe_patterns:
            if pattern.lower() in response_lower:
                return 0.0

        return 1.0  # Assume safe if no obvious issues

    async def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple RAG responses in batch.

        Args:
            evaluations: List of dicts with query, response, retrieved_docs

        Returns:
            Aggregated evaluation metrics
        """
        try:
            results = []

            for eval_item in evaluations:
                result = await self.evaluate_response(
                    query=eval_item["query"],
                    response=eval_item["response"],
                    retrieved_docs=eval_item.get("retrieved_docs", []),
                    reference_answer=eval_item.get("reference_answer")
                )
                results.append(result)

            # Aggregate scores
            aggregated = {
                "total_evaluations": len(results),
                "avg_groundedness": sum(r["groundedness"] for r in results) / len(results),
                "avg_relevance": sum(r["relevance"] for r in results) / len(results),
                "avg_coherence": sum(r["coherence"] for r in results) / len(results),
                "avg_fluency": sum(r["fluency"] for r in results) / len(results),
                "avg_safety": sum(r["safety"] for r in results) / len(results),
                "avg_overall_quality": sum(r["overall_quality"] for r in results) / len(results),
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info(
                "batch_evaluation_completed",
                total=len(results),
                avg_quality=aggregated["avg_overall_quality"]
            )

            return aggregated

        except Exception as e:
            logger.error("batch_evaluation_failed", error=str(e))
            raise


# Singleton instance
_evaluation_service: Optional[RAGEvaluationService] = None


def get_rag_evaluation() -> RAGEvaluationService:
    """Get singleton RAG evaluation service instance."""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = RAGEvaluationService()
    return _evaluation_service
