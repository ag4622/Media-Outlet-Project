import json
import boto3
import logging
from decimal import Decimal


EMBED_MODEL = "amazon.titan-embed-text-v2:0"


bedrock_runtime = boto3.client(
    "bedrock-runtime"
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_embedding(query: str) -> list[float]:
    """Generate embedding for query using Bedrock."""
    if not query.strip():
        raise ValueError("Input text is empty.")

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


if __name__ == "__main__":
    sample_text = "This is a question"
    embedding = generate_embedding(sample_text)
    print(embedding)
