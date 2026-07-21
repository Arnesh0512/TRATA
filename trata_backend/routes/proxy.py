from fastapi import APIRouter, Depends
from database import proxy_collection
from schemas import ProxyBlockSchema, ProxyStatusUpdateSchema
from dependencies import verify_api_key

router = APIRouter()

@router.post("/block")
async def block_proxy(payload: ProxyBlockSchema, current_user: dict = Depends(verify_api_key)):
    await proxy_collection.update_one(
        {"ip": payload.ip},
        {"$set": {"status": "Blocked", "reason": payload.reason}},
        upsert=True
    )
    return {"status": "success", "ip": payload.ip, "action": "blocked"}

@router.put("/{ip}/status")
async def update_proxy_status(ip: str, payload: ProxyStatusUpdateSchema, current_user: dict = Depends(verify_api_key)):
    await proxy_collection.update_one(
        {"ip": ip},
        {"$set": {"status": payload.status}}
    )
    return {"status": "success", "ip": ip, "newStatus": payload.status}