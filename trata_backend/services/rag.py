import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from database import (
    advisories_collection,
    capec_collection,
    cisa_kev_collection,
    cve_collection,
    mitre_attack_collection,
    mitre_preattack_collection,
    vulnerabilities_collection
)

# Load embedding model for vector search
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize lightweight local LLM tokenizer and model directly
print("Loading lightweight local LLM for RAG synthesis...")
llm_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
llm_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small", low_cpu_mem_usage=True)

async def search_vector_collection(collection, query_embedding, limit=2):
    """Performs vector similarity search across a MongoDB collection[cite: 13]."""
    cursor = collection.find({})
    results = []
    async for doc in cursor:
        if "embedding" in doc:
            db_vector = np.array(doc["embedding"])
            similarity = np.dot(query_embedding, db_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(db_vector))
            results.append((similarity, doc))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in results[:limit]]

async def query_rag_engine(query_text: str) -> str:
    query_embedding = embedding_model.encode(query_text).tolist()

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

    raw_context = " ".join(context_snippets)
    prompt = (
        f"Answer the user query based only on the provided security context in a clear, "
        f"human-understandable explanation.\n\nContext: {raw_context}\n\nQuery: {query_text}\nAnswer:"
    )

    # Use direct model tokenization and generation to prevent pipeline registry crashes
    inputs = llm_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = llm_model.generate(**inputs, max_new_tokens=200, do_sample=False)
    answer_text = llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    if answer_text.strip():
        return answer_text.strip()
    
    return "Relevant Threat Intelligence Found:\n" + "\n".join(context_snippets)