import os
import json
from typing import Optional

# LangChain components for a modular pipeline
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# --- CONFIGURATION ---
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"

# RAG Configuration
PDF_PATH = "COLREG-Consolidated-2018.pdf"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 150
VECTOR_STORE_PATH = "faiss_colreg_index"


class ModularRAGManager:
    """
    Manages a modular RAG pipeline using LangChain Expression Language (LCEL).
    This provides greater control and transparency over the RAG process.
    """

    def __init__(self):
        """
        Initializes the manager, loading or building the vector store and setting up the RAG chain.
        """
        print("Initializing ModularRAGManager...")
        self.api_key = os.getenv(DEEPSEEK_API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"FATAL: Environment variable '{DEEPSEEK_API_KEY_ENV}' not set.")

        # Using HuggingFace embeddings is more direct for local sentence-transformer models
        from langchain_community.embeddings import HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        self.vector_store = self._load_or_build_vector_store()

        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=DEEPSEEK_BASE_URL,
            model_name=DEEPSEEK_MODEL,
            temperature=0.1,
            max_tokens=1000,
        )

        # The main RAG chain is now built from modular components
        self.rag_chain = self._setup_rag_chain()
        print("Modular RAGManager is ready.")

    def _load_or_build_vector_store(self) -> FAISS:
        """Loads the FAISS vector store from disk or builds it from the PDF."""
        if os.path.exists(VECTOR_STORE_PATH):
            print(f"Loading existing vector store from {VECTOR_STORE_PATH}...")
            try:
                return FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Warning: Failed to load vector store: {e}. Rebuilding...")

        print(f"No existing vector store found. Building from {PDF_PATH}...")
        loader = PyPDFLoader(PDF_PATH)
        docs = loader.load()
        if not docs:
            raise FileNotFoundError(f"Could not load any documents from {PDF_PATH}.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        split_docs = text_splitter.split_documents(docs)

        print(f"Creating embeddings for {len(split_docs)} document chunks...")
        vector_store = FAISS.from_documents(split_docs, self.embeddings)

        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            print(f"Vector store saved to {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"Warning: Failed to save vector store: {e}")

        return vector_store

    def _setup_rag_chain(self):
        """
        Builds the modular RAG chain using LangChain Expression Language (LCEL).
        """
        # Module 1: The Retriever
        # This component retrieves documents from the vector store.
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

        # Module 2: The Prompt Template
        # This defines the structure of the prompt sent to the LLM.
        # It takes 'context' (from the retriever) and 'question' (from the user) as input.
        template = """
        You are an expert assistant on maritime regulations, specifically the COLREGs.
        Answer the following question based *only* on the provided context.
        Your response MUST be a valid JSON array of objects, where each object represents a specific action or decision.
        If the context does not contain the answer, state that clearly in the JSON response.

        Context:
        {context}

        Question:
        {question}

        JSON Answer:
        """
        prompt = ChatPromptTemplate.from_template(template)

        # Module 3: The Output Parser
        # This ensures the LLM's string output is parsed into a structured format (JSON).
        # We'll use a simple string parser for now and parse JSON in the final step.
        output_parser = StrOutputParser()

        # Helper function to format the retrieved documents
        def format_docs(docs):
            return "\n\n---\n\n".join(doc.page_content for doc in docs)

        # Assemble the chain using LCEL pipe (|) syntax
        # This defines the flow of data through our modules.
        rag_chain = (
            # This part runs in parallel:
            # 1. The user's question is passed to the retriever to get documents.
            # 2. The user's question is also passed through unchanged.
                RunnableParallel(
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                )
                # The dictionary from the parallel step is passed to the prompt.
                | prompt
                # The formatted prompt is passed to the LLM.
                | self.llm
                # The LLM's message object is passed to the string output parser.
                | output_parser
        )

        return rag_chain

    def get_llm_decision(self, user_query: str) -> Optional[str]:
        """
        Uses the modular RAG chain to get a decision from the LLM.
        """
        if not self.rag_chain:
            print("ERROR: RAG chain is not initialized.")
            return None

        print(f"\nInvoking modular chain with query: '{user_query}'")
        try:
            # The input to the chain is the user's question.
            response_str = self.rag_chain.invoke(user_query)

            # Now, attempt to parse the final string output as JSON
            try:
                parsed_json = json.loads(response_str)
                return json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError:
                print("Warning: LLM output was not valid JSON. Returning raw text.")
                print(f"Received: {response_str}")
                return response_str

        except Exception as e:
            print(f"Error during modular chain execution: {e}")
            return None


# --- Example of how to use the class (for standalone testing) ---
if __name__ == "__main__":
    try:
        rag_manager = ModularRAGManager()

        print("\n--- Modular RAG Test (using LangChain Expression Language) ---")
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

