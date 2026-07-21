import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/trata_db")

client = AsyncIOMotorClient(MONGO_URI)

# Explicitly bind to 'trata_db' to avoid missing database configurations
database = client.get_database("cyber_intelligence_rag")

# Core App Collections
packets_collection = database.get_collection("packets")
logs_collection = database.get_collection("logs")
files_collection = database.get_collection("files")
proxy_collection = database.get_collection("proxy")
users_collection = database.get_collection("users")
metrics_collection = database.get_collection("metrics")

# GridFS Bucket for storing files (creates fs.files and fs.chunks)
gridfs_bucket = AsyncIOMotorGridFSBucket(database)

# Cyber Intelligence RAG Database Collections
rag_db = client.get_database("cyber_intelligence_rag")
advisories_collection = rag_db.get_collection("advisories")
capec_collection = rag_db.get_collection("capec_embeddings")
cisa_kev_collection = rag_db.get_collection("cisa_kev_embeddings")
cve_collection = rag_db.get_collection("cve_embeddings")
mitre_attack_collection = rag_db.get_collection("mitre_attack_embeddings")
mitre_preattack_collection = rag_db.get_collection("mitre_preattack_embeddings")
vulnerabilities_collection = rag_db.get_collection("vulnerabilities")