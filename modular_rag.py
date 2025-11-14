import os
import re
from typing import Optional, List

# LangChain Imports
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# --- CONFIGURATION (remains the same) ---
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"

PDF_DIRECTORY = "pdf_files/"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 150
VECTOR_STORE_PATH = "faiss_multi_pdf_index"


class ModularRAGManager:
    """
    This RAG Manager enriches a dynamic prompt with COLREGs context,
    cleans the LLM's output, and returns a pure JSON string.
    """

    def __init__(self):
        """
        Initializes the manager, loading the vector store and setting up the RAG chain.
        """
        print("Initializing ModularRAGManager...")
        self.api_key = os.getenv(DEEPSEEK_API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"FATAL: Environment variable '{DEEPSEEK_API_KEY_ENV}' not set.")

        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = self._load_or_build_vector_store()
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=DEEPSEEK_BASE_URL,
            model_name=DEEPSEEK_MODEL,
            temperature=0.1,
            max_tokens=1000,
        )
        self.rag_chain = self._setup_rag_chain()
        print("Modular RAGManager is ready.")

    def _load_or_build_vector_store(self) -> FAISS:
        """This method remains unchanged."""
        # ... (your existing implementation)
        if os.path.exists(VECTOR_STORE_PATH):
            print(f"Loading existing vector store from {VECTOR_STORE_PATH}...")
            try:
                return FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Warning: Failed to load vector store: {e}. Rebuilding...")

        print(f"No existing vector store found. Building from all PDFs in {PDF_DIRECTORY}...")
        all_docs: List[Document] = []
        if not os.path.isdir(PDF_DIRECTORY):
            raise FileNotFoundError(f"The specified PDF directory does not exist: {PDF_DIRECTORY}")
        pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.lower().endswith(".pdf")]
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in the directory: {PDF_DIRECTORY}")
        print(f"Found {len(pdf_files)} PDF files to process.")
        for pdf_file in pdf_files:
            pdf_path = os.path.join(PDF_DIRECTORY, pdf_file)
            print(f" > Loading documents from {pdf_path}...")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            all_docs.extend(docs)
        if not all_docs:
            raise ValueError(f"Could not load any documents from the PDFs in {PDF_DIRECTORY}.")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        split_docs = text_splitter.split_documents(all_docs)
        print(f"Creating embeddings for {len(split_docs)} document chunks...")
        vector_store = FAISS.from_documents(split_docs, self.embeddings)
        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            print(f"Vector store saved to {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"Warning: Failed to save vector store: {e}")
        return vector_store

    def _setup_rag_chain(self):
        """This method remains unchanged."""
        template = """
        You are a ship navigation expert system. Your task is to determine the correct action for each vessel based on the International Regulations for Preventing Collisions at Sea (COLREGs).
        First, use the following relevant COLREGs rules to inform your decision:
        --- RELEVANT COLREGS RULES ---
        {context}
        ------------------------------
        Now, analyze the following real-time vessel data and determine the situation, role, and required action for each vessel. The prompt already contains instructions for the output format.
        --- VESSEL DATA AND INSTRUCTIONS ---
        {dynamic_prompt}
        ------------------------------------
        """
        prompt = ChatPromptTemplate.from_template(template)
        print(prompt)
        output_parser = StrOutputParser()

        def format_docs(docs: List[Document]) -> str:
            # --- lines to print the context ---
            # print("\n\n==================== RETRIEVED CONTEXT LOG ====================")
            # if not docs:
            #     print("--- No documents were retrieved. ---")
            # else:
            #     for i, doc in enumerate(docs):
            #         # We print the page content of each retrieved document chunk
            #         print(f"--- Document {i + 1} ---\n{doc.page_content}\n")
            # print("===============================================================\n\n")
            # ---------------------------------------------
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
                RunnableParallel(
                    {
                        "context": RunnablePassthrough() | self.retriever | format_docs,
                        "dynamic_prompt": RunnablePassthrough(),
                    }
                )
                | prompt
                | self.llm
                | output_parser
        )
        return chain

    def _clean_json_response(self, content: str) -> Optional[str]:
        """
        A robust helper method to find and extract a JSON array from the LLM's messy output.
        """
        if not isinstance(content, str):
            return None

        # Use regex to find content between ```json and ```
        match = re.search(r'```(json)?\s*(\[.*\])\s*```', content, re.DOTALL)
        if match:
            return match.group(2)

        # If no markdown fences, find the first occurrence of a JSON array
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]

        return None  # Return None if no valid JSON array is found

    def get_llm_decision(self, dynamic_prompt: str) -> Optional[str]:
        """
        UPDATED: This method now invokes the chain AND cleans the response
        before returning a pure JSON string.
        """
        if not self.rag_chain:
            print("ERROR: RAG chain is not initialized.")
            return None

        print("\n--- RAG Manager: Enriching dynamic prompt with COLREGs context... ---")
        try:
            # 1. Get the raw, potentially messy response from the LLM
            raw_response = self.rag_chain.invoke(dynamic_prompt)

            # 2. Clean the raw response to isolate the JSON string
            clean_json_string = self._clean_json_response(raw_response)

            if not clean_json_string:
                print("--- RAG Warning: Could not extract valid JSON from LLM response. ---")
                print("Raw response was:", raw_response)
                return "[]"  # Return an empty array string to prevent crashes downstream

            # 3. Return the clean JSON string to the EntityManager
            return clean_json_string

        except Exception as e:
            print(f"Error during RAG chain execution: {e}")
            return "[]"  # Return an empty array string on error