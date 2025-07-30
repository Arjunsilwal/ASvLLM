import os
import json
import re
from typing import Optional
from openai import OpenAI # The OpenAI client library can be used for Anthropic's API if configured correctly
import pypdf # For PDF text extraction
import numpy as np # For numerical operations with embeddings
from sentence_transformers import SentenceTransformer # For generating embeddings
import faiss # For efficient similarity search

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"

YOUR_SITE_URL = "local_pygame_simulator"
YOUR_APP_NAME = "VesselSim_COLREGs_Test"

# Claude pricing (per token)
INPUT_TOKEN_PRICE = 0.015 / 1_000
OUTPUT_TOKEN_PRICE = 0.075 / 1_000

# ─── RAG CONFIG (Copied from your naive RAG file) ──────────────────────────────
PDF_PATH = "COLREG-Consolidated-2018.pdf"  # Path to COLREG PDF
CHUNK_SIZE = 500  # Size of text chunks for embeddings
CHUNK_OVERLAP = 50  # Overlap between chunks to preserve context
TOP_K = 5  # Number of top relevant chunks to retrieve
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Model for generating text embeddings

# --- Global Variables for RAG components ---
_chunks = []
_faiss_index = None
_embedding_model = None # Will be initialized once in the RAG setup

# --- Paths for saving/loading the index and chunks ---
FAISS_INDEX_PATH = "colreg_faiss_index.bin"
CHUNKS_PATH = "colreg_chunks.json"

# ─── UTILS ─────────────────────────────────────────────────────────────────────
def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return prompt_tokens * INPUT_TOKEN_PRICE + completion_tokens * OUTPUT_TOKEN_PRICE

def _clean_response(content: str) -> str:
    # strip markdown fences
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # drop stray "json" markers
    return re.sub(r'^(?:json)?\s*|\s*$', "", text,
                  flags=re.IGNORECASE | re.MULTILINE).strip()

# ─── RAG COMPONENT FUNCTIONS (Copied from your naive RAG file) ─────────────────

def extract_text_from_pdf(path: str) -> str:
    """Extracts all text from a given PDF file."""
    text = ""
    try:
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"ERROR: Could not extract text from {path}: {e}")
        return ""
    return text

def chunk_text(text: str, sz: int, overlap: int) -> list[str]:
    """Splits a long text into smaller, overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + sz, len(text))
        chunks.append(text[start:end])
        start += sz - overlap
    return chunks

def retrieve_relevant_chunks(query: str, top_k: int = TOP_K) -> list[str]:
    """
    Retrieves the most relevant text chunks from the FAISS index based on a query.
    Requires _embedding_model and _faiss_index to be globally initialized.
    """
    global _embedding_model, _faiss_index, _chunks
    if _faiss_index is None or not _chunks:
        print("ERROR: RAG index or chunks not initialized. Cannot retrieve.")
        return []

    if _embedding_model is None: # Initialize embedding model if not already
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    q_emb = _embedding_model.encode([query]).astype('float32')
    D, I = _faiss_index.search(q_emb, top_k)

    return [_chunks[i] for i in I[0] if i < len(_chunks)]

# ─── CLIENT SETUP ───────────────────────────────────────────────────────────────
api_key = os.getenv(DEEPSEEK_API_KEY_ENV)
if not api_key:
    print(f"FATAL ERROR: Environment variable '{DEEPSEEK_API_KEY_ENV}' not set.")
    client = None
else:
    # Note: The `OpenAI` client from `openai` library can be used for Anthropic's API
    # if the base_url is set correctly. Anthropic's API is largely compatible with
    # OpenAI's client for chat completions.
    client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=api_key)
    print(f"[useLLm] Claude API key loaded from {DEEPSEEK_API_KEY_ENV}.")


# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────
def get_llm_decision(user_query: str) -> Optional[str]:
    """
    1) Grabs top-K chunks for the given `user_query` using RAG.
    2) Wraps them into a context-grounded prompt for the LLM.
    3) Sends the prompt to your Claude LLM API.
    4) Returns the full text response, expected to be in JSON array form.
    """
    if client is None:
        print("ERROR: Claude client not initialized.")
        return None
    if not isinstance(user_query, str) or not user_query.strip():
        print("ERROR: User query must be a non-empty string.")
        return None

    # 1) Fetch context using the retrieval function
    context_chunks = retrieve_relevant_chunks(user_query)

    if not context_chunks:
        context = "No specific information found in the document relevant to your question."
        print("\nNOTE: No relevant context found in document. LLM will answer based on general knowledge or state lack of info.")
    else:
        context = "\n\n--- Context Snippet(s) from COLREG-Consolidated-2018.pdf ---\n\n" + "\n\n".join(context_chunks)

    # 2) Build the RAG prompt for the LLM (for Claude)
    # Claude uses a slightly different message structure than pure OpenAI often.
    # While OpenAI client might adapt, it's safer to stick to their 'messages' format.
    rag_prompt_content = (
        f"Context:\n{context}\n\n"
        f"Question:\n{user_query}\n\n"
    )

    # Print the augmented text before sending to LLM
    print("\n===== Augmented Prompt (sent to Deepseek) =====")
    print(rag_prompt_content)
    print("=============================================\n")

    try:
        # deepseek API uses a `messages` array, typically with "user" and "assistant" roles.
        # The prompt goes into the user message.
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": rag_prompt_content}],
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_APP_NAME,
            },
            max_tokens=1000, # Increased max_tokens for potentially longer JSON output
            temperature=0.1,
            stream=False,
        )
    except Exception as e:
        print(f"Error: Claude request failed: {e}")
        return None

    # extract content
    try:
        content = resp.choices[0].message.content
    except Exception as e:
        print(f"Error: Unexpected Claude response structure: {e}")
        return None

    if not content:
        print("Error: Empty content in LLM response.")
        return None

    # if usage info is present, print estimated cost
    # The `usage` object might be nested or have slightly different attributes
    # depending on the specific API response from Anthropic when using OpenAI client.
    if hasattr(resp, "usage") and resp.usage:
        p_toks = getattr(resp.usage, "prompt_tokens", 0)
        c_toks = getattr(resp.usage, "completion_tokens", 0)
        cost = calculate_cost(p_toks, c_toks)
        print(f"[Claude] Prompt tokens: {p_toks}, Completion tokens: {c_toks}, Estimated cost: ${cost:.6f}")
    else:
        print("[Claude] Usage information not available in response.")


    # clean & debug-print
    cleaned = _clean_response(content)
    # try parsing
    try:
        data = json.loads(cleaned)
        return json.dumps(data, indent=2)
    except json.JSONDecodeError:
        print("Error: Failed to parse cleaned content as JSON.")
        print("Received:\n", cleaned)
        return None

# ─── RAG System Initialization Logic (Runs once when script is loaded) ─────────
print("Initializing RAG system...")
if _embedding_model is None:
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    _embedding_model = SentenceTransformer(EMBEDDING_MODEL)

if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
    print("Loading existing COLREG RAG index and chunks...")
    try:
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
            _chunks = json.load(f)
        print(f"Loaded {_faiss_index.ntotal} chunks from disk.")
    except Exception as e:
        print(f"ERROR: Could not load existing index/chunks. Re-ingesting PDF. Error: {e}")
        _faiss_index = None
        _chunks = [] # Reset to trigger re-ingestion
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
        if len(_chunks) > 0: # Ensure there are chunks before encoding
            _embeddings = _embedding_model.encode(_chunks).astype('float32')
            if len(_embeddings) > 0:
                _faiss_index = faiss.IndexFlatL2(_embeddings.shape[1])
                _faiss_index.add(_embeddings)
                print(f"Indexed {_faiss_index.ntotal} chunks. Saving for future use...")
                try:
                    faiss.write_index(_faiss_index, FAISS_INDEX_PATH)
                    with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
                        json.dump(_chunks, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"WARNING: Failed to save FAISS index or chunks: {e}")
            else:
                print("WARNING: No embeddings generated from chunks. FAISS index will be empty.")
        else:
            print("WARNING: No chunks generated from PDF. FAISS index will be empty.")

# You can add a check here to ensure the RAG system is ready before use
if _faiss_index is None or not _chunks:
    print("RAG system not fully initialized. LLM calls might not be context-aware.")
else:
    print("RAG system is ready.")

# --- Example of how to use it ---
if __name__ == "__main__":
    if _faiss_index is not None and _chunks:
        print("\n--- RAG-powered Claude Test ---")
        while True:
            user_query = input("Ask a question about COLREGs (or type 'quit' to exit): ")
            if user_query.lower() == 'quit':
                break
            decision_json = get_llm_decision(user_query)
            if decision_json:
                print("\n--- LLM Decision (JSON) ---\n")
                print(decision_json)
                print("\n-------------------------------\n")
            else:
                print("\nFailed to get LLM decision.\n")
    else:
        print("\nRAG system not ready. Cannot process queries. Please check PDF path and content.")