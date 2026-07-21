from fastapi import Header, HTTPException
from database import users_collection

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key header (X-API-Key)")
    
    user = await users_collection.find_one({"apiKey": x_api_key})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or unauthorized API key")
    
    # Return user record if needed by the route
    user["_id"] = str(user["_id"])
    return user