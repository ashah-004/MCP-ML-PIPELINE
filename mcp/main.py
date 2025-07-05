from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from k8s_utils import get_pod_logs
from healing import analyze_logs_and_heal
from prometheus_client import start_http_server, Counter

# Start Prometheus metrics server on port 8001
start_http_server(8081)

# Define custom metrics
healing_actions_counter = Counter('mcp_healing_actions_total', 'Total number of healing actions performed')

# Increment this counter whenever MCP performs healing
def perform_healing():
    healing_actions_counter.inc()

app = FastAPI(title="Model-Centric Pipeline (MCP) Server")

class HealRequest(BaseModel):
    namespace: str
    deployment_name: str
    pod_name: str
    logs: str = None  # optional, if provided by caller

class HealResponse(BaseModel):
    success: bool
    action_taken: str = None
    message: str = None

@app.post("/mcp/heal", response_model=HealResponse)
async def heal(req: HealRequest):
    logging.info(f"Received heal request for pod {req.pod_name} in namespace {req.namespace}")

    # If logs not provided, fetch from Kubernetes API
    pod_logs = req.logs
    if not pod_logs:
        pod_logs = get_pod_logs(req.namespace, req.pod_name)

    if not pod_logs:
        raise HTTPException(status_code=404, detail="Could not retrieve pod logs")

    # Call healing logic
    result = analyze_logs_and_heal(req.namespace, req.deployment_name, pod_logs)

    return HealResponse(**result)

@app.get("/")
async def root():
    return {"message": "MCP Server is running"}
