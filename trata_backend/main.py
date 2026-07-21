from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routes import agents, ai, auth, profile, proxy, rag, rag, telemetry
from routes import topology


load_dotenv()

app = FastAPI(
    title="TRATA Backend Service",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(rag.router, prefix="/rag", tags=["RAG Engine"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
app.include_router(proxy.router, prefix="/proxy", tags=["Proxy"])
app.include_router(topology.router, prefix="/topology", tags=["Topology"])
app.include_router(ai.router, prefix="/ai", tags=["AI Engine"])
app.include_router(agents.router, prefix='/agents', tags=["Agents"])



@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trata-backend"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)