from fastapi import APIRouter, Depends, HTTPException
from dependencies import verify_api_key
from services.ml_loader import ml_manager

router = APIRorgRouter = APIRouter()

@router.get("/graph")
async def get_topology_graph(current_user: dict = Depends(verify_api_key)):
    if ml_manager.network_graph is None:
        raise HTTPException(status_code=404, detail="Network graph model (auth_massive_network) not loaded")
    
    # Convert NetworkX graph nodes and edges into the CSV format expected by frontend parseGraphCsv()
    csv_lines = []
    for node, data in ml_manager.network_graph.nodes(data=True):
        cluster = data.get("cluster", "core")
        csv_lines.append(f"NODE,{node},{cluster},1.0,NORMAL")
        
    for u, v, data in ml_manager.network_graph.edges(data=True):
        weight = data.get("weight", 0.5)
        status = "ALERT" if data.get("alert", False) else "NORMAL"
        csv_lines.append(f"EDGE,{u},{v},{weight},{status}")
        
    csv_data = "\n".join(csv_lines)
    return {"csv": csv_data}