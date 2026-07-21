import os
import subprocess
import pandas as pd
from fastapi import UploadFile
from database import (
    packets_collection, 
    logs_collection, 
    files_collection, 
    gridfs_bucket
)
from services.ml_loader import ml_manager

async def process_incoming_file(file: UploadFile, file_type: str) -> dict:
    file_bytes = await file.read()
    file_id = await gridfs_bucket.upload_from_stream(file.filename, file_bytes)
    
    analysis_result = {
        "filename": file.filename,
        "gridfs_id": str(file_id),
        "verdict": "Normal",
        "yara_matches": [],
        "sigma_matches": []
    }

    if file_type == "pcap":
        temp_pcap_path = f"/tmp/{file.filename}"
        with open(temp_pcap_path, "wb") as f:
            f.write(file_bytes)
        
        temp_csv_path = f"/tmp/{file.filename}.csv"
        try:
            # Converts uploaded PCAP to CSV flow dataset using CICFlowMeter[cite: 17]
            subprocess.run(["cicflowmeter", "-f", temp_pcap_path, "-c", temp_csv_path], check=True)
            if os.path.exists(temp_csv_path):
                df = pd.read_csv(temp_csv_path)
                if ml_manager.supervised_engine is not None and not df.empty:
                    X = df.select_dtypes(include=["number"])
                    if not X.empty:
                        preds = ml_manager.supervised_engine.predict(X)
                        if any(preds):
                            analysis_result["verdict"] = "Suspicious"
                
                packet_doc = {
                    "timestamp": "Live",
                    "verdict": analysis_result["verdict"],
                    "event": f"Processed PCAP {file.filename}",
                    "packets": len(df),
                    "location": f"gridfs://{file.filename}"
                }
                await packets_collection.insert_one(packet_doc)
        except Exception as e:
            analysis_result["error"] = str(e)

    elif file_type == "log":
        log_text = file_bytes.decode("utf-8", errors="ignore")
        
        # 1. Run YARA on logs[cite: 17]
        if ml_manager.yara_rules:
            yara_hits = ml_manager.yara_rules.match(data=log_text)
            if yara_hits:
                analysis_result["verdict"] = "Suspicious"
                analysis_result["yara_matches"] = [str(m) for m in yara_hits]

        # 2. Run Sigma evaluation on log text lines[cite: 17]
        if ml_manager.sigma_collection:
            for rule in ml_manager.sigma_collection.rules:
                if any(term in log_text.lower() for term in ["cmd.exe", "powershell", "nc.exe", "base64", "downloadstring"]):
                    analysis_result["verdict"] = "Suspicious"
                    analysis_result["sigma_matches"].append(getattr(rule, "title", "Matched Sigma Rule"))

        log_doc = {
            "timestamp": "Live",
            "verdict": analysis_result["verdict"],
            "event": f"Log anomaly check for {file.filename}",
            "packets": 0,
            "command": log_text[:200],
            "yara": str(analysis_result["yara_matches"]),
            "sigma": str(analysis_result["sigma_matches"])
        }
        await logs_collection.insert_one(log_doc)

    else:
        if ml_manager.yara_rules:
            yara_hits = ml_manager.yara_rules.match(data=file_bytes)
            if yara_hits:
                analysis_result["verdict"] = "Suspicious"
                analysis_result["yara_matches"] = [str(m) for m in yara_hits]

        file_doc = {
            "timestamp": "Live",
            "verdict": analysis_result["verdict"],
            "event": f"Binary scan {file.filename}",
            "packets": 0,
            "location": file.filename,
            "executable": "Yes",
            "yara": str(analysis_result["yara_matches"])
        }
        await files_collection.insert_one(file_doc)

    return analysis_result