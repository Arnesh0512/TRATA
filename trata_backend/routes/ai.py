from fastapi import APIRouter, HTTPException, Depends
from database import metrics_collection
from dependencies import verify_api_key

router = APIRouter()

@router.get("/engine-metrics")
async def get_engine_metrics(current_user: dict = Depends(verify_api_key)):
    metrics = await metrics_collection.find_one({})
    if not metrics:
        raise HTTPException(status_code=404, detail="AI engine metrics not initialized in database")
    metrics["_id"] = str(metrics["_id"])
    return metrics