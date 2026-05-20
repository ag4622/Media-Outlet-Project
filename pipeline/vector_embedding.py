"""Adds vector embedding to the pipeline."""
import logging
import json
from decimal import Decimal
import boto3

bedrock_runtime = boto3.client('bedrock-runtime')


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def get_rag_text_chunk(data: dict):
    """Extract text chunk for RAG from the data dictionary."""
    return (
        f"trial_id: {data.get('trial_id', 'N/A')}. "
        f"title: {data.get('title', 'N/A')}. "
        f"conditions: {', '.join(data.get('conditions', []))
                       if data.get('conditions') else 'N/A'}. "
        f"therapeutic_area: {data.get('therapeutic_area', 'N/A')}. "
        f"interventions: {', '.join(data.get('interventions', []))
                          if data.get('interventions') else 'N/A'}. "
        f"sponsors: {', '.join(data.get('sponsors', []))
                     if data.get('sponsors') else 'N/A'}. "
        f"status: {data.get('status', 'N/A')}. "
        f"publication_date: {data.get('publication_date', 'N/A')}. "
        f"source_link: {data.get('source_link', 'N/A')}. "
        f"last_ingested: {data.get('last_ingested', 'N/A')}. "
        f"raw_description: {data.get('raw_description', 'N/A')}"
    )


def get_embedding(text: str) -> list:
    """Generate embedding for text chunk using Bedrock."""
    try:
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": 512,
                    "normalize": True
                }
            )
        )
        response_body = json.loads(response.get('body').read())
        raw_float_vector = response_body.get('embedding')
        db_compliant_vector = [Decimal(x) for x in raw_float_vector]
        return db_compliant_vector

    except Exception as e:
        logging.error("Error generating embedding: %s", str(e))
        raise


def append_embedding(data: dict, embedding: list) -> dict:
    """Append embedding to the data dictionary."""
    try:
        data['embedding'] = embedding
        return data
    except Exception as e:
        logging.error("Error appending embedding: %s", str(e))
        raise


def embedding_pipeline(data: dict) -> dict:
    """Complete pipeline to generate and append embedding to data."""
    try:
        text_chunk = get_rag_text_chunk(data)
        embedding = get_embedding(text_chunk)
        data_with_embedding = append_embedding(data, embedding)
        return data_with_embedding
    except Exception as e:
        logging.error("Error in embedding pipeline: %s", str(e))
        raise


if __name__ == "__main__":
    trial_data = {
        "trial_id": "NCT12345678",
        "title": "A Study on the Effects of XYZ Drug",
        "conditions": ["Condition A", "Condition B"],
        "therapeutic_area": "Oncology",
        "interventions": ["Drug XYZ"],
        "sponsors": ["Pharma Company"],
        "status": "Recruiting",
        "publication_date": "2024-01-01",
        "source_link": "http://example.com/trial/NCT12345678",
        "last_ingested": "2024-06-01",
        "raw_description": "This is a detailed description of the clinical trial..."
    }
    setup_logging()
    enriched_data = embedding_pipeline(trial_data)
    logging.info("Data with embedding: %s", enriched_data)
    bedrock_runtime.close()
