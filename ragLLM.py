import os
import json
import requests
import pypdf
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# ─── CONFIG ────────────────────────────────────────────────────────────────────
PDF_PATH = "COLREG-Consolidated-2018.pdf"  # Path to COLREG PDF
CHUNK_SIZE = 500  # Size of text chunks for embeddings
CHUNK_OVERLAP = 50  # Overlap between chunks to preserve context
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"  # URL for local Ollama instance
OLLAMA_MODEL = "llama3.2"  # The LLM model name served by Ollama
TOP_K = 3  # Number of top relevant chunks to retrieve
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Model for generating text embeddings

# --- Global Variables for RAG components ---
# These will be initialized once, either by loading or by ingesting
_chunks = []
_faiss_index = None

# Instantiate the embedding model ONCE at the global scope.
# This avoids re-loading the model every time the script runs if data is cached.
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)


# 1) TEXT INGESTION & INDEXING FUNCTIONS
def extract_text_from_pdf(path: str) -> str:
    """Extracts all text from a given PDF file."""
    text = ""
    try:
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            text += page.extract_text() or ""  # Use .extract_text() and handle None
    except Exception as e:
        print(f"ERROR: Could not extract text from {path}: {e}")
        return ""  # Return empty string on error
    return text


def chunk_text(text: str, sz: int, overlap: int) -> list[str]:
    """Splits a long text into smaller, overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + sz, len(text))  # Ensure 'end' doesn't exceed text length
        chunks.append(text[start:end])
        start += sz - overlap
    return chunks


# 2) RETRIEVAL FUNCTION
def retrieve_relevant_chunks(query: str, top_k: int = TOP_K) -> list[str]:
    """
    Retrieves the most relevant text chunks from the FAISS index based on a query.
    Requires _embedding_model and _faiss_index to be globally initialized.
    """
    if _faiss_index is None or not _chunks:
        print("ERROR: RAG index or chunks not initialized. Cannot retrieve.")
        return []

    q_emb = _embedding_model.encode([query]).astype('float32')
    # D: Distances, I: Indices of the retrieved chunks
    D, I = _faiss_index.search(q_emb, top_k)

    # Filter out invalid indices (e.g., if top_k is larger than available chunks)
    # and return the actual text chunks
    return [_chunks[i] for i in I[0] if i < len(_chunks)]


# 3) RAG PROMPT & LLM CALL FUNCTION
def get_llm_decision(prompt: str) -> str | None:
    """
    1) Grabs top-K chunks for the given `prompt` using RAG.
    2) Wraps them into a context-grounded prompt for the LLM.
    3) Sends the prompt to your local Ollama LLM (streaming).
    4) Returns the full text response, expected to be in JSON array form.
    """
    if not prompt or not prompt.strip():
        print("ERROR: Empty prompt passed to get_llm_decision()")
        return None

    # 1) Fetch context using the retrieval function
    context_chunks = retrieve_relevant_chunks(prompt)

    # If no context is found, inform the LLM to answer generally or state lack of info
    if not context_chunks:
        context = "No specific information found in the document relevant to your question."
        print(
            "\nNOTE: No relevant context found in document. LLM will answer based on general knowledge or state lack of info.")
    else:
        context = "\n\n--- Context Snippet(s) from COLREG-Consolidated-2018.pdf ---\n\n" + "\n\n".join(context_chunks)

    # 2) Build the RAG prompt for the LLM
    rag_prompt = (
        "You are a maritime-COLREGs assistant. Your primary goal is to provide concise, accurate, and actionable advice "
        "based *only* on the provided context, specifically concerning COLREGs rules and situations. "
        "If the answer cannot be found in the context, you must state: \"I do not have enough information to answer that question from the provided COLREGs document.\"\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{prompt}\n\n"
        "Please provide your answer in a JSON array format, strictly adhering to the structure: "
        "`{\"id\": \"<unique_identifier>\", \"situation\": \"<brief_situation_description>\", \"role\": \"<role_of_vessel>\", \"action\": \"<prescribed_action_based_on_COLREGs>\"}`. "
        "If no specific action or role is directly implied by the context, use 'N/A' for those fields. "
        "Ensure the `id` is a simple string (e.g., 'rule_1', 'situation_A')."
    )

    #  PRINT THE AUGMENTED TEXT
    print("\n--- Augmented Prompt (sent to LLM) ---\n")
    print(rag_prompt)
    print("\n---------------------------------------\n")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": rag_prompt}],
        "stream": True  # Keep streaming for better user experience
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, stream=True)
        resp.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ollama request failed: {e}")
        return None

    # 3) Collect full streamed content
    full_response_content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
            # Assuming standard chat-streaming format from Ollama
            content_part = data.get("message", {}).get("content", "")
            full_response_content += content_part
        except json.JSONDecodeError:
            # This can happen if a line is not complete JSON (e.g., partial stream end)
            # For robustness, we might just append it or log it.
            # print(f"WARNING: Failed to parse JSON line: {line}") # Uncomment for debugging
            full_response_content += line  # Append raw line if it's not JSON

    # 4) Strip markdown fences if present (common for JSON output from LLMs)
    text_result = full_response_content.strip()
    if text_result.startswith("```") and text_result.endswith("```"):
        text_result = "\n".join(text_result.splitlines()[1:-1]).strip()

    return text_result or None

### **Main RAG Initialization and Execution**
# --- Paths for saving/loading the index and chunks ---
FAISS_INDEX_PATH = "colreg_faiss_index.bin"
CHUNKS_PATH = "colreg_chunks.json"

# --- RAG System Initialization Logic ---
if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
    print("Loading existing COLREG RAG index and chunks...")
    try:
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:  # Specify encoding for safety
            _chunks = json.load(f)
        print(f"Loaded {_faiss_index.ntotal} chunks from disk.")
    except Exception as e:
        print(f"ERROR: Could not load existing index/chunks. Re-ingesting PDF. Error: {e}")
        # Fallback to ingestion if loading fails
        _faiss_index = None
        _chunks = []
else:
    print("No existing index found or incomplete. Ingesting COLREG PDF for RAG...")

# If index or chunks are not loaded from disk (either because they don't exist
# or loading failed), proceed with fresh ingestion.
if _faiss_index is None or not _chunks:
    _full_text = extract_text_from_pdf(PDF_PATH)
    if not _full_text:
        print(f"FATAL ERROR: Could not extract text from {PDF_PATH}. RAG system cannot be initialized.")
    else:
        _chunks = chunk_text(_full_text, CHUNK_SIZE, CHUNK_OVERLAP)
        _embeddings = _embedding_model.encode(_chunks).astype('float32')

        # Ensure there are chunks to add to the index
        if len(_embeddings) > 0:
            _faiss_index = faiss.IndexFlatL2(_embeddings.shape[1])
            _faiss_index.add(_embeddings)
            print(f"Indexed {_faiss_index.ntotal} chunks. Saving for future use...")
            try:
                faiss.write_index(_faiss_index, FAISS_INDEX_PATH)
                with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:  # Specify encoding for safety
                    json.dump(_chunks, f, ensure_ascii=False, indent=4)  # Pretty print JSON
            except Exception as e:
                print(f"WARNING: Failed to save FAISS index or chunks: {e}")
        else:
            print("WARNING: No chunks generated from PDF. FAISS index will be empty.")

# You can add a check here to ensure the RAG system is ready before use
if _faiss_index is None or not _chunks:
    print("RAG system not fully initialized. LLM calls might not be context-aware.")
else:
    print("RAG system is ready.")