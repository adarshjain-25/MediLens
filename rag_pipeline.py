import math
import re
from collections import Counter

from pypdf import PdfReader

# Groq has no embeddings endpoint, so retrieval uses TF-IDF (pure Python, no extra downloads).

SECTION_HEADERS = re.compile(
    r"(?im)^\s*(complete blood count|cbc|lipid panel|thyroid panel|liver function|"
    r"kidney function|metabolic panel|medications?|clinical notes?|test results?|"
    r"vitals?|urinalysis)\s*:?\s*$"
)


def split_by_section(text: str) -> list[str]:
    """Splits on recognized section headers so a lab value stays with its own
    section (and reference range) instead of being cut apart from it."""
    marks = [m.start() for m in SECTION_HEADERS.finditer(text)]
    if not marks:
        return [text]
    marks.append(len(text))
    return [text[marks[i]:marks[i + 1]] for i in range(len(marks) - 1)]


def chunk_text(text: str, chunk_size=1000, overlap=150) -> list[str]:
    """Chunks by section first, then sub-splits any section too long to embed whole."""
    chunks = []
    for section in split_by_section(text):
        if len(section) <= chunk_size:
            if section.strip():
                chunks.append(section)
            continue
        start = 0
        while start < len(section):
            chunks.append(section[start:start + chunk_size])
            start += chunk_size - overlap
    return chunks


def _tokens(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())


def _vectorize(tokens, idf):
    tf = Counter(tokens)
    return {t: (c / len(tokens)) * idf.get(t, 0.0) for t, c in tf.items()} if tokens else {}


def _cosine(a: dict, b: dict):
    dot = sum(v * b.get(t, 0.0) for t, v in a.items())
    ma = math.sqrt(sum(v * v for v in a.values()))
    mb = math.sqrt(sum(v * v for v in b.values()))
    return 0.0 if ma == 0 or mb == 0 else dot / (ma * mb)


def process_text(full_text: str):
    """Indexes raw report text (used for both real uploads and the sample report)
    and returns (vector_store, summary_text)."""
    if not full_text.strip():
        raise ValueError("No readable text found. Scanned PDFs need OCR first.")

    chunks = chunk_text(full_text)
    tokenized = [_tokens(c) for c in chunks]
    df = Counter(t for toks in tokenized for t in set(toks))
    idf = {t: math.log((1 + len(chunks)) / (1 + n)) + 1 for t, n in df.items()}
    vectors = [_vectorize(toks, idf) for toks in tokenized]

    return {"chunks": chunks, "idf": idf, "vectors": vectors}, full_text


def process_document(file_path: str):
    """Reads a PDF and delegates to process_text."""
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(p for p in pages if p.strip())
    return process_text(full_text)


def search_vector_store(vector_store, query: str, top_k=3, return_scores=False):
    q = _vectorize(_tokens(query), vector_store["idf"])
    scored = [(_cosine(q, v), c) for v, c in zip(vector_store["vectors"], vector_store["chunks"])]
    scored.sort(key=lambda x: x[0], reverse=True)
    if return_scores:
        return scored[:top_k]
    if scored and scored[0][0] == 0:  # no word overlap: fall back to the start of the report
        return vector_store["chunks"][:top_k]
    return [c for _, c in scored[:top_k]]
