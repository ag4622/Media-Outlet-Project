"""Tests for vector_embedding.py."""

from decimal import Decimal
import pytest
from vector_embedding import (
    get_rag_text_chunk, get_embedding, append_embedding
)


def test_get_rag_text_chunk():
    """Test get_rag_text_chunk with complete data."""
    data = {
        "trial_id": "NCT12345678",
        "title": "A Study on the Effects of XYZ Drug",
        "conditions": ["Condition A", "Condition B"],
        "therapeutic_area": "Oncology",
        "interventions": ["Intervention 1", "Intervention 2"],
        "sponsors": ["Sponsor A", "Sponsor B"],
        "status": "Completed",
        "publication_date": "2023-01-01",
        "source_link": "http://example.com/trial/NCT12345678",
        "last_ingested": "2023-02-01",
        "raw_description": "This is a detailed description of the clinical trial."
    }
    expected_output = (
        f"trial_id: {data['trial_id']}. "
        f"title: {data['title']}. "
        f"conditions: {', '.join(data['conditions'])}. "
        f"therapeutic_area: {data['therapeutic_area']}. "
        f"interventions: {', '.join(data['interventions'])}. "
        f"sponsors: {', '.join(data['sponsors'])}. "
        f"status: {data['status']}. "
        f"publication_date: {data['publication_date']}. "
        f"source_link: {data['source_link']}. "
        f"last_ingested: {data['last_ingested']}. "
        f"raw_description: {data['raw_description']}"
    )
    assert get_rag_text_chunk(data) == expected_output


def test_get_rag_text_chunk_missing_fields():
    """Test get_rag_text_chunk with missing optional fields."""
    data = {
        "trial_id": "NCT12345678",
        "title": "A Study on the Effects of XYZ Drug",
        # Missing conditions, therapeutic_area, interventions, sponsors
        "status": "Completed",
        "publication_date": "2023-01-01",
        "source_link": "http://example.com/trial/NCT12345678",
        "last_ingested": "2023-02-01",
        "raw_description": "This is a detailed description of the clinical trial."
    }
    expected_output = (
        f"trial_id: {data['trial_id']}. "
        f"title: {data['title']}. "
        f"conditions: N/A. "
        f"therapeutic_area: N/A. "
        f"interventions: N/A. "
        f"sponsors: N/A. "
        f"status: {data['status']}. "
        f"publication_date: {data['publication_date']}. "
        f"source_link: {data['source_link']}. "
        f"last_ingested: {data['last_ingested']}. "
        f"raw_description: {data['raw_description']}"
    )
    assert get_rag_text_chunk(data) == expected_output


def test_get_embedding():
    """Test get_embedding with a sample text."""
    text = "This is a test text for embedding."
    embedding = get_embedding(text)
    assert isinstance(embedding, list)
    assert all(isinstance(x, Decimal) for x in embedding)
    assert len(embedding) == 512


def test_get_embedding_empty_text():
    """Test get_embedding with empty text input."""
    text = ""
    with pytest.raises(ValueError, match="Input text for embedding is empty."):
        get_embedding(text)


def test_append_embedding():
    """Test append_embedding with sample data and embedding."""
    data = {"trial_id": "NCT12345678"}
    embedding = [Decimal(0.1), Decimal(0.2), Decimal(0.3)]
    expected_output = {
        "trial_id": "NCT12345678",
        "embedding": embedding
    }
    assert append_embedding(data, embedding) == expected_output
