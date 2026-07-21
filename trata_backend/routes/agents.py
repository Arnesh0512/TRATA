from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import users_collection, database

router = router = APIRouter()

class ApiKeyValidateSchema(BaseModel):
    api_key: Optional[str] = ""

class SettingsUpdateSchema(BaseModel):
    value: Optional[str | int] = None

@router.get("/")
def home():
    return {"message": "Cyber Resilience backend is running"}

@router.post("/auth/validate")
async def validate_api_key(payload: ApiKeyValidateSchema):
    if not payload.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Query database for matching API key
    user = await users_collection.find_one({"apiKey": payload.api_key})
    if not user:
        return {"valid": False, "error": "invalid_api_key"}
    
    return {
        "valid": True,
        "org_id": str(user.get("_id")),
        "org_name": user.get("fullName", "Unknown Organization"),
        "agent_id": user.get("agent_id", "agent_default"),
        "permissions": user.get("permissions", ["ingest:pcap", "ingest:logs", "read:config"]),
        "min_poll_interval_minutes": user.get("min_poll_interval_minutes", 5),
        "max_poll_interval_minutes": user.get("max_poll_interval_minutes", 30)
    }

@router.get("/config")
async def get_agent_config(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_authorization")

    config_doc = await database.get_collection("system_config").find_one({"key": "agent_config"})
    if not config_doc:
        raise HTTPException(status_code=404, detail="Agent configuration not initialized in database")
    
    return {
        "poll_interval_minutes": config_doc.get("poll_interval_minutes"),
        "pcap_watch_dir": config_doc.get("pcap_watch_dir"),
        "log_watch_dir": config_doc.get("log_watch_dir"),
        "last_sync": config_doc.get("last_sync")
    }

@router.get("/settings")
async def get_settings():
    settings_doc = await database.get_collection("system_settings").find_one({"type": "agent_settings"})
    if not settings_doc:
        raise HTTPException(status_code=404, detail="Settings not found in database")
    
    settings_doc["_id"] = str(settings_doc["_id"])
    return settings_doc

@router.post("/settings/pcap-dir")
async def update_pcap_dir(payload: SettingsUpdateSchema):
    if payload.value is None:
        raise HTTPException(status_code=400, detail="Value cannot be null")
    await database.get_collection("system_settings").update_one(
        {"type": "agent_settings"},
        {"$set": {"pcap_watch_dir": payload.value}},
        upsert=True
    )
    return {"status": "ok", "pcap_watch_dir": payload.value}

@router.post("/settings/log-dir")
async def update_log_dir(payload: SettingsUpdateSchema):
    if payload.value is None:
        raise HTTPException(status_code=400, detail="Value cannot be null")
    await database.get_collection("system_settings").update_one(
        {"type": "agent_settings"},
        {"$set": {"log_watch_dir": payload.value}},
        upsert=True
    )
    return {"status": "ok", "log_watch_dir": payload.value}

@router.post("/settings/pcap-time-window")
async def update_pcap_time_window(payload: SettingsUpdateSchema):
    if payload.value is None:
        raise HTTPException(status_code=400, detail="Value cannot be null")
    val = int(payload.value)
    await database.get_collection("system_settings").update_one(
        {"type": "agent_settings"},
        {"$set": {"pcap_time_window_minutes": val}},
        upsert=True
    )
    return {"status": "ok", "pcap_time_window_minutes": val}

@router.post("/settings/log-time-window")
async def update_log_time_window(payload: SettingsUpdateSchema):
    if payload.value is None:
        raise HTTPException(status_code=400, detail="Value cannot be null")
    val = int(payload.value)
    await database.get_collection("system_settings").update_one(
        {"type": "agent_settings"},
        {"$set": {"log_time_window_minutes": val}},
        upsert=True
    )
    return {"status": "ok", "log_time_window_minutes": val}

@router.post("/settings/api-expiry")
async def update_api_expiry(payload: SettingsUpdateSchema):
    if payload.value is None:
        raise HTTPException(status_code=400, detail="Value cannot be null")
    val = int(payload.value)
    await database.get_collection("system_settings").update_one(
        {"type": "agent_settings"},
        {"$set": {"api_key_expiry_days": val}},
        upsert=True
    )
    return {"status": "ok", "api_key_expiry_days": val}

@router.post("/connection/disconnect")
async def disconnect():
    await database.get_collection("connection_state").update_one(
        {"singleton": True},
        {"$set": {"state": "disconnected"}},
        upsert=True
    )
    return {"status": "ok"}

@router.post("/connection/pause")
async def pause_connection():
    await database.get_collection("connection_state").update_one(
        {"singleton": True},
        {"$set": {"state": "paused"}},
        upsert=True
    )
    return {"status": "paused"}

@router.post("/connection/resume")
async def resume_connection():
    await database.get_collection("connection_state").update_one(
        {"singleton": True},
        {"$set": {"state": "resumed"}},
        upsert=True
    )
    return {"status": "resumed"}

@router.post("/api-key/delete")
async def delete_api_key():
    await users_collection.update_one(
        {"username": "trata.admin"},
        {"$unset": {"apiKey": ""}}
    )
    return {"status": "deleted"}

@router.post("/heartbeat")
async def heartbeat():
    await database.get_collection("system_status").update_one(
        {"key": "heartbeat"},
        {"$set": {"status": "active", "timestamp": "live"}},
        upsert=True
    )
    return {"status": "ok"}