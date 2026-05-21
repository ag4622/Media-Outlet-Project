import boto3
import logging
from sklearn.metrics.pairwise import cosine_similarity


TABLE_NAME = "c23-ClinicalTrialTracker"
TOP_K = 5

dynamodb = boto3.resource(
    "dynamodb")

table = dynamodb.Table(TABLE_NAME)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
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
            logging.warning(
                f"Skipping trial due to error: {e}"
            )
    scored_trials.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    return scored_trials[:top_k]
