from fastapi import APIRouter, Depends
from schemas import RagQuerySchema
from services.rag import query_rag_engine
from dependencies import verify_api_key

router = APIRouter()

@router.post("/query")
async def query_rag(payload: RagQuerySchema, current_user: dict = Depends(verify_api_key)):
    answer_text = await query_rag_engine(payload.query)
    return {"answer": answer_text}