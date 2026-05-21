"""Python module for answer generation component of RAG pipeline, responsible for generating answers
    based on retrieved clinical trial context and user questions using Bedrock LLM."""


import logging
import json
import boto3


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


EMBED_MODEL = "amazon.titan-embed-text-v2:0"
LLM_MODEL = "meta.llama3-8b-instruct-v1:0"

bedrock_runtime = boto3.client(
    "bedrock-runtime"
)


def get_prompt(user_identity: str = 'investor') -> str:
    """Fetch system prompt based on user identity."""
    with open(f"./RAG/prompts/{user_identity}.txt", "r", encoding="utf-8") as f:
        return f.read()


def build_context(retrieved_trials):
    """Build context string from retrieved trials for LLM input."""
    context = ""
    for item in retrieved_trials:
        trial = item["trial"]
        context += f"""

Trial ID:
{trial.get('trial_id', 'N/A')}

Title:
{trial.get('title', 'N/A')}

Condition:
{trial.get('conditions', 'N/A')}

Sponsor:
{trial.get('sponsors', 'N/A')}

Interventions:
{trial.get('interventions', 'N/A')}

Status:
{trial.get('status', 'N/A')}

Source Link:
{trial.get('source_link', 'N/A')}

"""
    return context


def generate_answer(question, context, user_identity='investor'):
    """Generate answer using Bedrock LLM based on question and retrieved context."""
    system_prompt = get_prompt(user_identity)

    full_prompt = f"""
System:
{system_prompt}

Context:
{context}

User Question:
{question}

Answer:
"""

    body = {
        "prompt": full_prompt,
        "temperature": 0.2,
        "top_p": 0.9
    }
    try:
        response = bedrock_runtime.invoke_model(
            modelId=LLM_MODEL,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        return response_body["generation"]
    except boto3.exceptions.Boto3Error as e:
        logging.error("Error generating answer: %s", str(e))
        raise
