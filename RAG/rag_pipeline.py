import logging

from embeddings import generate_embedding
from retrieval import get_candidate_trials, retrieve_relevant_trials
from generator import build_context, generate_answer


def ask_rag(question, user_identity='investor'):

    logging.info("Generating query embedding...")

    query_embedding = generate_embedding(question)

    logging.info("Fetching candidate trials...")

    candidate_trials = get_candidate_trials()

    logging.info(f"Retrieved {len(candidate_trials)} candidate trials")

    logging.info("Running similarity search...")

    retrieved_trials = retrieve_relevant_trials(query_embedding, candidate_trials)

    logging.info(f"Top matches found: {len(retrieved_trials)}")

    logging.info("Building context...")

    context = build_context(retrieved_trials)

    logging.info("Generating final answer...")

    answer = generate_answer(question, context, user_identity)

    return {
        "question": question,
        "answer": answer,
        "retrieved_trials": retrieved_trials
    }


if __name__ == "__main__":

    question = "What are the latest diabetes clinical trials?"

    result = ask_rag(question, 'investor')

    print("\nQUESTION:\n")
    print(result["question"])

    print("\nANSWER:\n")
    print(result["answer"])