"""
RAG (Retrieval-Augmented Generation) Service for Policy Retrieval
Phase 1: Foundation - RAG Retrieval Layer
"""

from app.database import SessionLocal
from app.models.evaluation_criteria import EvaluationCriteria
from app.models.policy_template import PolicyTemplate
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("google-generativeai not installed. RAG embeddings will not work.")

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for retrieving relevant policy snippets.
    Uses vector embeddings to find the most relevant policy clauses for a call topic.
    """

    def __init__(self):
        self.embedding_model = None
        if GEMINI_AVAILABLE:
            # Use text-embedding-004 for vector embeddings
            self.embedding_model = "models/text-embedding-004"

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get vector embedding for text using Gemini text-embedding-004"""
        if not GEMINI_AVAILABLE or not self.embedding_model:
            logger.warning("Gemini embeddings not available")
            return None

        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'])
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def _extract_call_topics(self, transcript: str) -> List[str]:
        """
        Extract potential call topics from transcript for better policy retrieval.
        Returns topics like ["late delivery", "account issue", "refund request", etc.]
        """
        topics = []

        # Common call topics and their indicators
        topic_indicators = {
            "late delivery": ["late", "delayed", "delivery", "shipping", "tracking", "package"],
            "account issue": ["account", "login", "password", "access", "blocked", "locked"],
            "billing": ["bill", "charge", "payment", "refund", "credit", "invoice", "price"],
            "product issue": ["broken", "defective", "not working", "quality", "damage", "faulty"],
            "return": ["return", "exchange", "refund", "replacement", "send back"],
            "complaint": ["unacceptable", "frustrated", "angry", "terrible", "worst", "disappointed"],
            "technical support": ["error", "bug", "glitch", "website", "app", "system"],
            "cancellation": ["cancel", "terminate", "end service", "close account"],
            "upgrade": ["upgrade", "change plan", "modify", "add service"],
            "general inquiry": ["question", "information", "help", "how do i", "can you"]
        }

        transcript_lower = transcript.lower()

        # Check for topic indicators in transcript
        for topic, indicators in topic_indicators.items():
            if any(indicator in transcript_lower for indicator in indicators):
                topics.append(topic)

        # If no specific topics found, add general fallback
        if not topics:
            topics.append("general customer service")

        return topics

    def _prepare_policy_documents(self, criteria: List[EvaluationCriteria]) -> List[Dict[str, Any]]:
        """
        Prepare policy documents for vector search.
        Each document contains policy text, category, and embedding.
        """
        documents = []

        for criterion in criteria:
            # Create searchable document from evaluation prompt and rubric levels
            policy_text = f"Category: {criterion.category_name}\n"
            policy_text += f"Evaluation Prompt: {criterion.evaluation_prompt}\n"

            # Add rubric levels if available
            if criterion.rubric_levels:
                policy_text += "Rubric Levels:\n"
                for level in sorted(criterion.rubric_levels, key=lambda x: x.level_order):
                    examples = f" Examples: {level.examples}" if level.examples else ""
                    policy_text += f"- {level.level_name} ({level.min_score}-{level.max_score}): {level.description}{examples}\n"

            document = {
                "id": criterion.id,
                "category": criterion.category_name,
                "text": policy_text,
                "weight": float(criterion.weight),
                "passing_score": criterion.passing_score
            }

            # Get embedding for the policy text
            embedding = self._get_embedding(policy_text)
            if embedding is not None:
                document["embedding"] = embedding
                documents.append(document)
            else:
                logger.warning(f"Could not get embedding for criterion {criterion.category_name}")

        return documents

    def retrieve_relevant_policies(
        self,
        transcript: str,
        policy_template_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve the most relevant policy clauses for a given call transcript.
        Returns top-k most relevant policy snippets based on semantic similarity.
        """
        db = SessionLocal()
        try:
            # Get evaluation criteria for the policy template
            criteria = db.query(EvaluationCriteria).filter(
                EvaluationCriteria.policy_template_id == policy_template_id
            ).all()

            if not criteria:
                logger.warning(f"No criteria found for template {policy_template_id}")
                return {"retrieved_policies": [], "call_topics": []}

            # Extract call topics from transcript
            call_topics = self._extract_call_topics(transcript)
            logger.info(f"Extracted call topics: {call_topics}")

            # Prepare policy documents with embeddings
            policy_documents = self._prepare_policy_documents(criteria)

            if not policy_documents:
                logger.warning("No policy documents with embeddings available")
                return {"retrieved_policies": [], "call_topics": call_topics}

            # Create search query from transcript + topics
            search_query = f"Call transcript topics: {', '.join(call_topics)}\n\n{transcript[:1000]}"  # Limit transcript length
            query_embedding = self._get_embedding(search_query)

            if query_embedding is None:
                logger.warning("Could not get embedding for search query")
                # Fallback: return all policies if embeddings fail
                return {
                    "retrieved_policies": [doc for doc in policy_documents[:top_k]],
                    "call_topics": call_topics
                }

            # Calculate similarities
            similarities = []
            for doc in policy_documents:
                if "embedding" in doc:
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        doc["embedding"].reshape(1, -1)
                    )[0][0]
                    similarities.append((doc, similarity))

            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_documents = [doc for doc, sim in similarities[:top_k]]

            # Also include policies that are always relevant (high weight categories)
            high_priority_categories = ["Empathy", "Professionalism", "Resolution", "Communication"]
            for doc in policy_documents:
                if (doc["category"] in high_priority_categories and
                    doc not in top_documents and
                    len(top_documents) < top_k + 2):  # Allow a few extra
                    top_documents.append(doc)

            logger.info(f"Retrieved {len(top_documents)} relevant policy documents")

            return {
                "retrieved_policies": top_documents,
                "call_topics": call_topics,
                "search_query": search_query
            }

        finally:
            db.close()

    def format_policy_context(self, retrieved_policies: List[Dict[str, Any]]) -> str:
        """
        Format retrieved policies into a context string for the LLM prompt.
        """
        if not retrieved_policies:
            return "No specific policy context available."

        context_parts = ["RELEVANT POLICY CONTEXT (Retrieved based on call topic):\n"]

        for i, policy in enumerate(retrieved_policies, 1):
            context_parts.append(f"Policy {i}: {policy['category']} (Weight: {policy['weight']}%, Passing: {policy['passing_score']}/100)")
            context_parts.append(policy['text'])
            context_parts.append("")  # Empty line for readability

        return "\n".join(context_parts)
