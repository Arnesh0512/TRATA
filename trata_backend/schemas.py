from pydantic import BaseModel, Field
from typing import Optional, List, Any

class PacketSchema(BaseModel):
    timestamp: str
    verdict: str
    event: str
    packets: int
    duration: Optional[str] = "0s"
    sourceIp: Optional[str] = None
    sourcePort: Optional[int] = None
    protocol: Optional[str] = None
    attackType: Optional[str] = "None"
    transferred: Optional[int] = 0
    intel: Optional[str] = None
    mitre: Optional[str] = "None"
    cve: Optional[str] = "None"
    cert: Optional[str] = None

class LogSchema(BaseModel):
    timestamp: str
    verdict: str
    event: str
    packets: int
    processId: Optional[int] = None
    generatedTimestamp: Optional[str] = None
    generatedBy: Optional[str] = None
    command: Optional[str] = None
    yara: Optional[str] = None
    sigma: Optional[str] = None
    intel: Optional[str] = None
    mitre: Optional[str] = "None"
    cve: Optional[str] = "None"
    cert: Optional[str] = None

class FileRecordSchema(BaseModel):
    timestamp: str
    verdict: str
    event: str
    packets: int
    location: str
    parentProcess: Optional[str] = None
    size: str
    yara: Optional[str] = None
    executable: Optional[str] = "No"
    running: Optional[str] = "No"
    intel: Optional[str] = None
    mitre: Optional[str] = "None"
    cve: Optional[str] = "None"
    cert: Optional[str] = None
    gridfs_file_id: Optional[str] = None # Reference ID if stored in GridFS

class ProxySchema(BaseModel):
    ip: str
    domain: Optional[str] = None
    description: Optional[str] = None
    attacks: Optional[int] = 0
    timestamp: Optional[str] = None
    status: str
    reason: Optional[str] = None
    suggested: Optional[bool] = False

class ProfileSchema(BaseModel):
    name: str
    role: str
    organization: str
    team: str
    email: str
    device: str
    apiKey: Optional[str] = None

class MetricSchema(BaseModel):
    detectionAccuracy: str
    graphDetectionAccuracy: str
    embeddingsLastUpdated: str
    monthlyUserIncrement: str

class RagQuerySchema(BaseModel):
    query: str

class ApiKeySchema(BaseModel):
    apiKey: str

class VerifySessionSchema(BaseModel):
    apiKey: str

class ManualLoginSchema(BaseModel):
    username: str
    password: str



class RagQuerySchema(BaseModel):
    query: str

class ProxyBlockSchema(BaseModel):
    ip: str
    reason: Optional[str] = "Suspicious activity detected"

class ProxyStatusUpdateSchema(BaseModel):
    status: str