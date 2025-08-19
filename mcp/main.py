from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
from k8s_utils import get_pod_logs
from healing import analyze_logs_and_heal
from prometheus_client import start_http_server, Counter
import os
import json
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='[MCP] %(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Prometheus metrics server
start_http_server(8001)
healing_actions_counter = Counter('mcp_healing_actions_total', 'Total number of healing actions performed')

LOG_DIR = "/app/healing_logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "heal_log.jsonl")

def perform_healing():
    healing_actions_counter.inc()

def log_healing_event(namespace, deployment_name, pod_name, logs, result):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "namespace": namespace,
        "deployment_name": deployment_name,
        "pod_name": pod_name,
        "logs": logs,
        "healing_action": result.get("action_taken"),
        "message": result.get("message"),
        "success": result.get("success")
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

app = FastAPI(title="Model-Centric Pipeline (MCP) Server")

class HealRequest(BaseModel):
    namespace: str
    deployment_name: str
    pod_name: str
    logs: str = None

class HealResponse(BaseModel):
    success: bool
    action_taken: str = None
    message: str = None

@app.post("/mcp/heal", response_model=HealResponse)
async def heal(req: HealRequest):
    logging.info(f"Received heal request for pod {req.pod_name} in namespace {req.namespace}")

    pod_logs = req.logs or get_pod_logs(req.namespace, req.pod_name)
    if not pod_logs:
        raise HTTPException(status_code=404, detail="Could not retrieve pod logs")

    result = analyze_logs_and_heal(req.namespace, req.deployment_name, pod_logs)
    perform_healing()
    log_healing_event(req.namespace, req.deployment_name, req.pod_name, pod_logs, result)

    return HealResponse(**result)

@app.post("/mcp/heal/auto")
async def auto_heal(request: Request):
    payload = await request.json()
    try:
        logging.info(f"[AUTO] Received raw payload from Alertmanager:\n{json.dumps(payload, indent=2)}")
    except Exception:
        print(f"[AUTO] Received payload (fallback): {payload}")

    alerts = payload.get("alerts", [])
    if not alerts:
        raise HTTPException(status_code=400, detail="No alerts received")

    responses = []
    for alert in alerts:
        if alert.get("status") != "firing":
            continue

        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        namespace = labels.get("mcp_namespace") or annotations.get("mcp_namespace")
        deployment = labels.get("mcp_deployment") or annotations.get("mcp_deployment")
        pod_name = labels.get("mcp_pod") or annotations.get("mcp_pod")

        if not all([namespace, deployment, pod_name]):
            logging.warning(f"[AUTO] Skipping alert, missing namespace/deployment/pod: {alert}")
            continue

        logging.info(f"[AUTO] Healing alert triggered for pod {pod_name} in ns {namespace}")

        pod_logs = get_pod_logs(namespace, pod_name) or annotations.get("description", "")
        if not pod_logs:
            logging.warning(f"[AUTO] No logs found for pod {pod_name}")
            continue

        result = analyze_logs_and_heal(namespace, deployment, pod_logs)
        perform_healing()
        log_healing_event(namespace, deployment, pod_name, pod_logs, result)

        responses.append({
            "pod": pod_name,
            "namespace": namespace,
            "result": result
        })

    return {"healed": responses}

@app.get("/")
async def root():
    return {"message": "MCP Server is running"}
