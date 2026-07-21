import numpy as np
from sentence_transformers import SentenceTransformer
from database import (
    advisories_collection,
    capec_collection,
    cisa_kev_collection,
    cve_collection,
    mitre_attack_collection,
    mitre_preattack_collection,
    vulnerabilities_collection
)

# Load a lightweight embedding model matching your 384-dimension vector arrays shown in MongoDB
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

async def search_vector_collection(collection, query_embedding, limit=2):
    """Performs vector similarity search across a MongoDB collection."""
    cursor = collection.find({})
    results = []
    async for doc in cursor:
        if "embedding" in doc:
            db_vector = np.array(doc["embedding"])
            # Cosine similarity calculation
            similarity = np.dot(query_embedding, db_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(db_vector))
            results.append((similarity, doc))
    
    # Sort by highest similarity score
    results.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in results[:limit]]

async def query_rag_engine(query_text: str) -> str:
    query_embedding = embedding_model.encode(query_text).tolist()

    # Search across intelligence collections
    attack_results = await search_vector_collection(mitre_attack_collection, query_embedding, limit=1)
    cve_results = await search_vector_collection(cve_collection, query_embedding, limit=1)
    advisory_results = await search_vector_collection(advisories_collection, query_embedding, limit=1)

    context_snippets = []
    for doc in attack_results:
        context_snippets.append(f"MITRE ATT&CK ({doc.get('mitre_id')}): {doc.get('name')} - {doc.get('description')}")
    for doc in cve_results:
        context_snippets.append(f"CVE ({doc.get('cve_id')}): {doc.get('description')}")
    for doc in advisory_results:
        context_snippets.append(f"Advisory ({doc.get('id')}): {doc.get('title')} - {doc.get('overview')}")

    if not context_snippets:
        return "No matching threat intelligence found in the vector store for this query."

    # Formulate final context response or pass to LLM
    return "Relevant Threat Intelligence Found:\n" + "\n".join(context_snippets)