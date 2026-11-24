"""ChromaDB Vector Store management with role-based metadata filtering."""
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.models.Collection import Collection

from rag.config import settings
from rag.embeddings import get_embedding_function
from rag.document_loader import DocumentChunk

ROLE_ACCESS_HIERARCHY = {
    "employee": ["all"],
    "manager": ["all", "managers"],
    "admin": ["all", "managers", "admin"]
}

def get_role_filter(user_role: str) -> Optional[Dict[str, Any]]:
    """Builds a strict ChromaDB metadata filter based on user role."""
    normalized_role = user_role.lower().strip()
    allowed_access_levels = ROLE_ACCESS_HIERARCHY.get(normalized_role, ["all"])

    if len(allowed_access_levels) == 1:
        return {"role_access": allowed_access_levels[0]}
    else:
        return {"role_access": {"$in": allowed_access_levels}}

class AcmeVectorStore:
    COLLECTION_NAME = "acme_documents"

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.embedding_fn = get_embedding_function()
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Adds or updates chunks in the vector store."""
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [c.to_chroma_metadata() for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def delete_document(self, doc_id: str) -> int:
        """Deletes all chunks associated with a specific doc_id."""
        existing = self.collection.get(where={"doc_id": doc_id})
        found_ids = existing.get("ids", [])
        if found_ids:
            self.collection.delete(ids=found_ids)
            return len(found_ids)
        return 0

    def replace_document(self, doc_id: str, new_chunks: List[DocumentChunk]) -> tuple[int, int]:
        """Atomically cleans up all old chunks for doc_id, then inserts new_chunks."""
        deleted_count = self.delete_document(doc_id)
        added_count = self.add_chunks(new_chunks)
        return deleted_count, added_count

    def search(
        self,
        query: str,
        user_role: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Queries the vector store strictly filtered by role access permissions.
        
        CRITICAL SECURITY INVARIANT:
        Role filtering occurs in ChromaDB prior to returning any results.
        Restricted chunks are never retrieved into application memory or prompt context.
        """
        where_filter = get_role_filter(user_role)

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        chunks_found: List[Dict[str, Any]] = []
        if not results or not results["documents"] or not results["documents"][0]:
            return chunks_found

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for idx, doc_text in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            dist = distances[idx] if idx < len(distances) else 1.0

            # Cosine distance in chromadb is between 0 (identical) and 2 (opposite)
            # Similarity = 1 - distance
            chunks_found.append({
                "content": doc_text,
                "metadata": meta,
                "distance": dist,
                "score": 1.0 - dist
            })

        return chunks_found

    def count(self) -> int:
        return self.collection.count()

    def get_all_indexed_docs(self) -> List[Dict[str, Any]]:
        """Summarizes distinct documents currently stored."""
        records = self.collection.get(include=["metadatas"])
        docs_map: Dict[str, Dict[str, Any]] = {}
        for meta in records.get("metadatas", []):
            if not meta:
                continue
            doc_id = meta.get("doc_id", "unknown")
            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "doc_id": doc_id,
                    "title": meta.get("doc_title", doc_id),
                    "role_access": meta.get("role_access", "all"),
                    "department": meta.get("department", "General"),
                    "chunks": 0
                }
            docs_map[doc_id]["chunks"] += 1
        return list(docs_map.values())
