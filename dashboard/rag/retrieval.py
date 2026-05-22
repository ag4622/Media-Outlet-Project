"""Python module for retrieval component of RAG pipeline, responsible for
fetching relevant clinical trials from DynamoDB based on query embeddings."""

import logging
import os
import boto3
from sklearn.metrics.pairwise import cosine_similarity


TABLE_NAME = "c23-ClinicalTrialTracker"
TOP_K = 10

dynamodb = boto3.resource(
    "dynamodb", region_name=os.getenv('AWS_REGION', 'eu-west-2')
)

table = dynamodb.Table(TABLE_NAME)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def decimal_to_float(vector):
    """Convert a list of Decimal objects to a list of floats."""
    return [float(x) for x in vector]


def get_candidate_trials(limit=1000):
    """Scan DynamoDB to retrieve candidate trials for RAG."""
    response = table.scan(
        Limit=limit
    )
    return response.get("Items", [])


def retrieve_relevant_trials(query_embedding, trials, top_k=TOP_K):
    """Retrieve the most relevant trials based on cosine similarity."""
    scored_trials = []
    for trial in trials:
        try:
            stored_embedding = decimal_to_float(trial["embedding"])

            similarity = cosine_similarity(
                [query_embedding],
                [stored_embedding]
            )[0][0]

            scored_trials.append({
                "score": similarity,
                "trial": trial
            })

        except Exception as e:
            logging.warning("Skipping trial due to error: %s", str(e))
    scored_trials.sort(key=lambda x: x["score"], reverse=True)
    return scored_trials[:top_k]
