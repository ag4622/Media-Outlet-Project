"""Python module for RAG pipeline, orchestrating the end-to-end process of generating embeddings,
    retrieving relevant clinical trials, and generating answers based on user questions."""


import logging

from RAG.embeddings import generate_embedding
from RAG.retrieval import get_candidate_trials, retrieve_relevant_trials
from RAG.generator import build_context, generate_answer


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def ask_rag(question, user_identity='investor'):
    """Main RAG pipeline function to process user question and generate answer."""

    logging.info("Generating query embedding...")
    query_embedding = generate_embedding(question)

    logging.info("Fetching candidate trials...")
    candidate_trials = get_candidate_trials()
    logging.info("Retrieved %d candidate trials", len(candidate_trials))

    logging.info("Running similarity search...")
    retrieved_trials = retrieve_relevant_trials(query_embedding, candidate_trials)
    logging.info("Top matches found: %d", len(retrieved_trials))

    logging.info("Building context...")
    context = build_context(retrieved_trials)

    logging.info("Generating final answer...")
    answer = generate_answer(question, context, user_identity)

    return {
        "question": question,
        "answer": answer
    }


if __name__ == "__main__":
    setup_logging()
    result = ask_rag("What are the most popular drugs being tested?", 'investor')

    print("\nQUESTION:\n")
    print(result["question"])

    print("\nANSWER:\n")
    print(result["answer"])
