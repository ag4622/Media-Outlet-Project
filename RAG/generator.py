import json
import boto3
import logging


EMBED_MODEL = "amazon.titan-embed-text-v2:0"
LLM_MODEL = "meta.llama3-8b-instruct-v1:0"

bedrock_runtime = boto3.client(
    "bedrock-runtime"
)


def get_prompt(user_identity: str = 'investor') -> str:
    """Fetch system prompt based on user identity."""
    with open(f"prompts/{user_identity}.txt", "r") as f:
        return f.read()


def build_context(retrieved_trials):

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

    response = bedrock_runtime.invoke_model(
        modelId=LLM_MODEL,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response["body"].read())
    print(response_body)
    return response_body["generation"]





















if __name__ == "__main__":
    # Example usage
    retrieved_trials = [
        {
            "score": 0.95,
            "trial": {
                "trial_id": "NCT12345678",
                "title": "A Study of Drug X in Patients with Condition Y",
                "condition": "Condition Y",
                "sponsor": "Pharma Company A",
                "phase": "Phase 2",
                "status": "Recruiting",
                "summary": "This is a summary of the clinical trial."
            }
        },
        {
            "score": 0.90,
            "trial": {
                "trial_id": "NCT87654321",
                "title": "A Study of Drug Z in Patients with Condition Y",
                "condition": "Condition Y",
                "sponsor": ["Pharma Company B", "Pharma Company C"],
                "phase": "Phase 3",
                "status": "Completed",
                "summary": "This is another summary of a clinical trial."
            }
        }
    ]

    context = build_context(retrieved_trials)
    print(context)
    print(get_prompt())