from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from database import packets_collection, logs_collection, files_collection, proxy_collection, database
from dependencies import verify_api_key
from services.pipeline import process_incoming_file

router = APIRouter()

@router.get("/stream")
async def get_telemetry_stream(current_user: dict = Depends(verify_api_key)):
    packets = await packets_collection.find().to_list(length=100)
    logs = await logs_collection.find().to_list(length=100)
    files = await files_collection.find().to_list(length=100)
    proxy = await proxy_collection.find().to_list(length=100)
    
    for item in packets + logs + files + proxy:
        if "_id" in item:
            item["_id"] = str(item["_id"])

    return {
        "packets": packets,
        "logs": logs,
        "files": files,
        "proxy": proxy,
        "suspicious": any(p.get("verdict") == "Suspicious" for p in packets + logs + files)
    }

@router.post("/upload/pcap")
async def upload_pcap_file(file: UploadFile = File(...), current_user: dict = Depends(verify_api_key)):
    """Receives PCAP, converts via CICFlowMeter, runs model prediction, and stores in DB."""
    result = await process_incoming_file(file, "pcap")
    return {"status": "success", "analysis": result}

@router.post("/upload/log")
async def upload_log_file(file: UploadFile = File(...), current_user: dict = Depends(verify_api_key)):
    """Receives log files, applies YARA / Sigma detection, and stores in DB."""
    result = await process_incoming_file(file, "log")
    return {"status": "success", "analysis": result}

@router.post("/upload/binary")
async def upload_binary_file(file: UploadFile = File(...), current_user: dict = Depends(verify_api_key)):
    """Receives generic/executable files, applies YARA rules, and stores in GridFS/DB."""
    result = await process_incoming_file(file, "binary")
    return {"status": "success", "analysis": result}

@router.post("/attack-trigger")
async def trigger_attack(current_user: dict = Depends(verify_api_key)):
    attack_doc = await database.get_collection("threat_simulations").find_one({"type": "ftp_ingress_payload"})
    if not attack_doc:
        raise HTTPException(status_code=404, detail="Attack simulation profile not found in database")
    
    attack_doc["_id"] = str(attack_doc["_id"])
    return {
        "packet": attack_doc.get("packet"),
        "log": attack_doc.get("log"),
        "file": attack_doc.get("file"),
        "proxy": attack_doc.get("proxy")
    }

@router.get("/status-message")
async def get_status_message(current_user: dict = Depends(verify_api_key)):
    status_doc = await database.get_collection("system_status").find_one({"key": "active_alert_notice"})
    if not status_doc:
        raise HTTPException(status_code=404, detail="System status message not found in database")
    
    return {
        "message": status_doc.get("message"),
        "chatNotice": status_doc.get("chatNotice")
    }