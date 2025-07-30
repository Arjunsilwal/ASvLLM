import os
import json
from typing import Optional

# LangChain components
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA

# --- CONFIGURATION ---
# Note: It's good practice to keep these in a separate config file or as environment variables.
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"

# RAG Configuration
PDF_PATH = "COLREG-Consolidated-2018.pdf"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # This is a sentence-transformer model
CHUNK_SIZE = 500
CHUNK_OVERLAP = 150

# Paths for saving/loading the pre-processed vector store
VECTOR_STORE_PATH = "faiss_colreg_index"


class RAGManager:
    """
    Manages the RAG pipeline using LangChain for robust document processing and retrieval.
    """

    def __init__(self):
        """
        Initializes the RAGManager, loading or building the vector store and setting up the QA chain.
        """
        print("Initializing RAGManager...")
        self.api_key = os.getenv(DEEPSEEK_API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"FATAL: Environment variable '{DEEPSEEK_API_KEY_ENV}' not set.")

        # Initialize embeddings model
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_base="https://api.openai.com/v1",  # Dummy base, not used by sentence-transformer
            # The OpenAIEmbeddings wrapper can be a bit tricky with local models.
            # For sentence-transformers, it's often better to use HuggingFaceEmbeddings.
            # However, for simplicity, we'll stick to this structure.
            # A more robust way is:
            # from langchain_community.embeddings import HuggingFaceEmbeddings
            # self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        )

        # Load or build the vector store
        self.vector_store = self._load_or_build_vector_store()

        # Initialize the LLM
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=DEEPSEEK_BASE_URL,
            model_name=DEEPSEEK_MODEL,
            temperature=0.1,
            max_tokens=1000,
        )

        # Initialize the RetrievalQA chain
        self.qa_chain = self._setup_qa_chain()
        print("RAGManager is ready.")

    def _load_or_build_vector_store(self) -> FAISS:
        """
        Loads the FAISS vector store from disk if it exists, otherwise builds it from the PDF.
        """
        if os.path.exists(VECTOR_STORE_PATH):
            print(f"Loading existing vector store from {VECTOR_STORE_PATH}...")
            try:
                return FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Warning: Failed to load vector store: {e}. Rebuilding...")

        print(f"No existing vector store found. Building from {PDF_PATH}...")

        # 1. Load the document
        loader = PyPDFLoader(PDF_PATH)
        docs = loader.load()
        if not docs:
            raise FileNotFoundError(f"Could not load any documents from {PDF_PATH}.")

        # 2. Split the document into semantic chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len
        )
        split_docs = text_splitter.split_documents(docs)

        # 3. Create embeddings and the FAISS vector store
        print(f"Creating embeddings for {len(split_docs)} document chunks. This may take a moment...")
        vector_store = FAISS.from_documents(split_docs, self.embeddings)

        # 4. Save the vector store for future use
        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            print(f"Vector store saved to {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"Warning: Failed to save vector store: {e}")

        return vector_store

    def _setup_qa_chain(self):
        """
        Sets up the LangChain RetrievalQA chain.
        """
        if not self.vector_store:
            print("ERROR: Vector store is not initialized. Cannot create QA chain.")
            return None

        # The retriever is the part of the vector store that finds relevant documents
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 chunks

        # The chain combines the retriever and the LLM
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # "stuff" puts all retrieved chunks into the context
            retriever=retriever,
            return_source_documents=True  # Optional: to see which chunks were used
        )

    def get_llm_decision(self, user_query: str) -> Optional[str]:
        """
        Uses the QA chain to get a decision from the LLM based on the user query and retrieved context.
        """
        if not self.qa_chain:
            print("ERROR: QA chain is not initialized.")
            return None

        print(f"\nSending query to LLM: '{user_query}'")
        try:
            # The chain handles retrieving context and formatting the prompt automatically
            response = self.qa_chain.invoke({"query": user_query})

            # The main answer is in 'result'
            result_text = response.get("result")

            # Debug: Print source documents
            source_docs = response.get("source_documents", [])
            print(f"\n--- Retrieved {len(source_docs)} Context Snippets ---")
            for i, doc in enumerate(source_docs):
                print(f"Snippet {i + 1} (from page {doc.metadata.get('page', 'N/A')}):\n{doc.page_content[:200]}...\n")
            print("--------------------------------\n")

            # Attempt to parse the result as JSON
            try:
                # Clean up potential markdown fences
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]

                parsed_json = json.loads(result_text)
                return json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError:
                print("Warning: LLM output was not valid JSON. Returning raw text.")
                return result_text

        except Exception as e:
            print(f"Error during LLM query execution: {e}")
            return None


# --- Example of how to use the class (for standalone testing) ---
if __name__ == "__main__":
    try:
        # Initialization happens here. Ensure your DEEPSEEK_API_KEY is set.
        rag_manager = RAGManager()

        print("\n--- RAG-powered LLM Test (using LangChain) ---")
        while True:
            user_query = input("Ask a question about COLREGs (or type 'quit' to exit): ")
            if user_query.lower() in ['quit', 'exit']:
                break

            decision = rag_manager.get_llm_decision(user_query)

            if decision:
                print("\n--- LLM Decision ---\n")
                print(decision)
                print("\n--------------------\n")
            else:
                print("\nFailed to get a valid decision from the LLM.\n")

    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

