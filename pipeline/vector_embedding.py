"""Adds vector embedding to the pipeline."""
import logging
import boto3
import json
from decimal import Decimal

# configure runtime client to be 512 dimensions
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


def get_embedding(text: str) -> list:
    """Generate embedding for text using Bedrock."""
    try:
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": 1536,
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
    data['embedding'] = embedding
    return data


if __name__ == "__main__":
    try:
        setup_logging()
        sample_text = "This is a sample text to generate embedding."
        embedding = get_embedding(sample_text)
        logging.info("Generated embedding: %s", embedding)
    finally:
        bedrock_runtime.close()
