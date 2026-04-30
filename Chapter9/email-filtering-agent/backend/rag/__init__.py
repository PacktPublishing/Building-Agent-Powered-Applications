from typing import Tuple

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from backend.config import Settings
from backend.rag.report_indexer import ReportIndexer
from backend.rag.report_retriever import ReportRetriever


def create_rag(settings: Settings) -> Tuple[ReportIndexer, ReportRetriever]:
    """Create a shared ChromaDB collection and return configured indexer and retriever."""
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    ef = OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.embedding_model,
    )
    collection = client.get_or_create_collection(
        name="email_reports",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return ReportIndexer(collection), ReportRetriever(collection, settings.rag_top_k)
