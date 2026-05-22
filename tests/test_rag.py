"""Tests for the rag modules."""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest

from rag import embeddings, generator, retrieval


class Testembeddings:
    """Tests for the embedding generation component of RAG pipeline."""
    def test_get_embedding(self):
        """Test get_embedding with a sample text."""
        text = "This is a test text for embedding."
        embedding = embeddings.generate_embedding(text)
        assert isinstance(embedding, list)
        assert all(isinstance(x, Decimal) for x in embedding)
        assert len(embedding) == 512

    def test_get_embedding_empty_text(self):
        """Test get_embedding with empty text input."""
        text = ""
        with pytest.raises(ValueError, match="Input text is empty."):
            embeddings.generate_embedding(text)


class Testretrieval:
    """Tests for the retrieval component of RAG pipeline."""
    @patch('rag.retrieval.table')
    def test_get_candidate_trials_returns_items(self, mock_table):
        """Should return a list of trials from DynamoDB scan."""
        mock_table.scan.return_value = {"Items": [{"trial_id": "NCT123"}]}
        retrieval.table = mock_table

        trials = retrieval.get_candidate_trials(limit=10)
        assert isinstance(trials, list)
        assert trials == [{"trial_id": "NCT123"}]

    def test_retrieve_relevant_trials_sorts_by_similarity_and_skips_invalid(self):
        """Trials with higher cosine similarity should come first, and bad embeddings are skipped."""
        query_embedding = [1.0, 0.0]
        trials = [
            {"trial_id": "A", "embedding": [Decimal("1"), Decimal("0")]},
            {"trial_id": "B", "embedding": [Decimal("0"), Decimal("1")]},
            {"trial_id": "C", "embedding": "not-a-vector"},
        ]

        results = retrieval.retrieve_relevant_trials(query_embedding, trials, top_k=5)

        assert [item["trial"]["trial_id"] for item in results] == ["A", "B"]
        assert results[0]["score"] >= results[1]["score"]


class Testgenerator:
    """Tests for the prompt generation component of RAG pipeline."""

    def test_build_context_includes_trial_fields(self):
        """The prompt context should include the key trial fields for each result."""
        context = generator.build_context([
            {
             "trial": {
                "trial_id": "NCT123",
                "title": "Alpha Study",
                "conditions": ["Cancer", "Diabetes"],
                "sponsors": ["ACME"],
                "interventions": ["Drug A"],
                "status": "Recruiting",
                "source_link": "https://example.com/trial/NCT123"}
            }
        ])

        assert "Trial ID:\nNCT123" in context
        assert "Title:\nAlpha Study" in context
        assert "Condition:\n['Cancer', 'Diabetes']" in context
        assert "Sponsor:\n['ACME']" in context
        assert "Interventions:\n['Drug A']" in context
        assert "Status:\nRecruiting" in context
        assert "Source Link:\nhttps://example.com/trial/NCT123" in context

    def test_empty_question_returns_empty_answer(self):
        """If the question is empty, the generated answer should also be empty."""
        answer = generator.generate_answer("", "Some context")
        assert answer == ""
