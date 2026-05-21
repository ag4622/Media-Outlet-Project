"""Python module for embedding generation component of RAG pipeline, responsible for generating
    vector embeddings for user queries using Bedrock."""
import logging
import json
from decimal import Decimal
import boto3


EMBED_MODEL = "amazon.titan-embed-text-v2:0"


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


bedrock_runtime = boto3.client(
    "bedrock-runtime"
)


def generate_embedding(query: str) -> list[float]:
    """Generate embedding for query using Bedrock."""
    if not query.strip():
        raise ValueError("Input text is empty.")
    try:
        response = bedrock_runtime.invoke_model(
            modelId=EMBED_MODEL,
            body=json.dumps({
                "inputText": query,
                "dimensions": 512,
                "normalize": True
            })
        )

        response_body = json.loads(
            response["body"].read()
        )
        raw_float_vector = response_body["embedding"]
        db_compliant_vector = [Decimal(str(x)) for x in raw_float_vector]
        return db_compliant_vector
    except boto3.exceptions.Boto3Error as e:
        logging.error("Error generating embedding: %s", str(e))
        raise


if __name__ == "__main__":
    setup_logging()
    embedding = generate_embedding("This is a question")
    print(embedding)
