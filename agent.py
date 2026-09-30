from llm import chat
from rag_pipeline import search_vector_store

NOT_FOUND_MESSAGE = "I couldn't find that information in the uploaded report."
_MIN_MATCH_SCORE = 0.03  # below this, the retriever found no real overlap with the question


def ask_medical_agent(query: str, vector_store):
    """Answers strictly from the uploaded report. If retrieval finds no real overlap,
    returns the fixed not-found message instead of guessing or using general knowledge --
    this app must never hallucinate an answer that isn't grounded in the document."""
    scored = search_vector_store(vector_store, query, top_k=3, return_scores=True)
    if not scored or scored[0][0] < _MIN_MATCH_SCORE:
        return NOT_FOUND_MESSAGE, None

    chunks = [c for _, c in scored]
    context = "\n---\n".join(chunks)
    prompt = f"""
You are an AI assistant answering ONLY from the report context below. Do not add information
that is not present in the context. If the context does not answer the question, say so plainly.
Always remind the user this is not a medical diagnosis.

Report Context:
{context}

User Question: {query}
"""
    answer = chat(prompt, temperature=0.2)
    first_line = chunks[0].strip().splitlines()[0].strip() if chunks[0].strip() else ""
    source_hint = first_line if first_line and len(first_line) < 60 else None
    return answer, source_hint
