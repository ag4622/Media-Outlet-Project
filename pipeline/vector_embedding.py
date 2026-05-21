"""Adds vector embedding to the pipeline."""
import logging
import json
import os
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3

bedrock_runtime = boto3.client(
    'bedrock-runtime',
    region_name=os.getenv('AWS_REGION', 'eu-west-2')
)


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
    if not text:
        raise ValueError("Input text for embedding is empty.")

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
        db_compliant_vector = [Decimal(str(x)) for x in raw_float_vector]
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


def embedding_pipeline(data: list[dict]) -> list[dict]:
    """Complete pipeline to generate and append embeddings to list of data items in parallel."""
    try:
        data_with_embeddings = []

        # Use ThreadPoolExecutor for parallel processing (up to 5 concurrent requests)
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Map each item to a future
            futures = {
                executor.submit(
                    lambda item=item: append_embedding(
                        item,
                        get_embedding(get_rag_text_chunk(item))
                    )
                ): idx for idx, item in enumerate(data)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    data_with_embeddings.append(result)
                    logging.info("Completed embedding for item")
                except Exception as e:
                    logging.error(
                        "Error processing item in parallel: %s", str(e))
                    raise

        return data_with_embeddings
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
