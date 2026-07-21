from fastapi import APIRouter, HTTPException, Depends
from database import users_collection
from schemas import ApiKeySchema, VerifySessionSchema, ManualLoginSchema
from dependencies import verify_api_key

router = APIRouter()

LOCAL_USERNAME = "trata.admin"
LOCAL_PASSWORD = "trata@2026"

@router.post("/initiate")
async def auth_initiate():
    return {"status": "success", "message": "Authentication flow initiated"}

@router.post("/generate-key")
async def generate_key(payload: ApiKeySchema):
    await users_collection.update_one(
        {"username": LOCAL_USERNAME},
        {"$set": {"apiKey": payload.apiKey}},
        upsert=True
    )
    return {"status": "success", "apiKey": payload.apiKey}

@router.post("/verify-session")
async def verify_session(payload: VerifySessionSchema):
    user = await users_collection.find_one({"apiKey": payload.apiKey})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or unverified API key session")
    return {"status": "verified", "email": user.get("email")}

@router.get("/confirm-connection")
async def confirm_connection(current_user: dict = Depends(verify_api_key)):
    return {"status": "connected"}

@router.post("/manual")
async def manual_login(payload: ManualLoginSchema):
    if payload.username != LOCAL_USERNAME or payload.password != LOCAL_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"status": "success", "message": "Manual authentication successful"}