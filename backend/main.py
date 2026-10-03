from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import random
import datetime

app = FastAPI(title="SAANJH Edge Gateway API", description="IoT Gateway for Flexibility Node Orchestration")

class NodeTelemetry(BaseModel):
    node_id: str
    battery_soc: float
    current_load_w: float
    is_discharging: bool
    timestamp: str

class DispatchCommand(BaseModel):
    event_id: str
    target_reduction_w: float
    duration_min: int

# In-memory state
nodes = {}
active_events = {}

@app.post("/api/v1/telemetry")
async def receive_telemetry(telemetry: NodeTelemetry):
    nodes[telemetry.node_id] = telemetry
    return {"status": "success", "recorded_at": datetime.datetime.now().isoformat()}

@app.get("/api/v1/nodes")
async def get_node_status():
    return {"active_nodes": len(nodes), "nodes": nodes}

@app.post("/api/v1/dispatch")
async def trigger_dispatch(command: DispatchCommand, background_tasks: BackgroundTasks):
    active_events[command.event_id] = command
    
    # In a real system, this would send MQTT/LoRaWAN downlinks to nodes
    def simulate_lora_broadcast():
        print(f"Broadcasting LoRa command for event {command.event_id} - Target: {command.target_reduction_w}W")
        
    background_tasks.add_task(simulate_lora_broadcast)
    
    return {"status": "dispatching", "event": command.event_id, "nodes_targeted": len(nodes)}

@app.get("/api/v1/grid/health")
async def get_grid_health():
    # Simulate transformer health reading
    load = random.uniform(80.0, 98.0)
    return {
        "transformer_id": "TRF-021",
        "loading_percent": load,
        "status": "CRITICAL" if load > 95 else "HEALTHY",
        "voltage": 240 - (load / 100 * 20)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
