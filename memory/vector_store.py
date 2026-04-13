import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

class LongTermMemory:
    def __init__(self):
        # Free local embeddings — no API key required (downloads ~80MB model once)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        self.vector_db = Chroma(
            collection_name="financial_docs",
            embedding_function=self.embeddings,
            persist_directory="./memory/chroma_db"  # Stores data locally on your PC
        )

    def store_document(self, text: str, metadata: dict):
        """Chunks text and saves it to the database."""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        self.vector_db.add_texts(texts=chunks, metadatas=[metadata]*len(chunks))
        print(f"  💾 Stored {len(chunks)} chunk(s) in long-term memory.")

    def search(self, query: str, k: int = 3):
        """Finds the most relevant pieces of information."""
        return self.vector_db.similarity_search(query, k=k)
