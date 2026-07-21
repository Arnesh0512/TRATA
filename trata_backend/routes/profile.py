from fastapi import APIRouter, HTTPException, Depends
from database import users_collection
from schemas import ProfileSchema
from dependencies import verify_api_key

router = APIRouter()

@router.get("/details")
async def get_profile_details(current_user: dict = Depends(verify_api_key)):
    # Uses the verified user document directly from dependency context or queries via stored email/key
    current_user["_id"] = str(current_user["_id"])
    return current_user

@router.post("/register")
async def register_profile(payload: ProfileSchema, current_user: dict = Depends(verify_api_key)):
    profile_data = payload.model_dump()
    if current_user.get("apiKey"):
        profile_data["apiKey"] = current_user.get("apiKey")
        
    await users_collection.update_one(
        {"email": payload.email},
        {"$set": profile_data},
        upsert=True
    )
    return {"status": "success", "message": "Profile registered successfully"}