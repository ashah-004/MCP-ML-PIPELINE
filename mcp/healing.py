import logging
from k8s_utils import restart_deployment
from llm_utils import infer_healing_action
import os
import json
from datetime import datetime

LOG_DIR = "/app/healing_logs"
os.makedirs(LOG_DIR, exist_ok=True)

def analyze_logs_and_heal(namespace: str, deployment_name: str, pod_logs: str) -> dict:
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "namespace": namespace,
        "deployment_name": deployment_name,
        "logs": pod_logs,
        "action": None,
        "description": None,
        "success": False
    }

    # Step 1: Use LLM to infer action
    result = infer_healing_action(pod_logs)
    action = result.get("action")
    description = result.get("description")
    log_entry.update({"action": action, "description": description})

    # Step 2: Perform Action
    if action == "restart":
        restarted = restart_deployment(namespace, deployment_name)
        log_entry["success"] = restarted
    elif action == "unknown":
        log_entry["success"] = False
    else:
        log_entry["success"] = False  # for now, only restart is supported

    # Step 3: Persist structured log
    log_file = os.path.join(LOG_DIR, "healing_dataset.json")
    if os.path.exists(log_file):
        with open(log_file, "r+") as f:
            data = json.load(f)
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=2)
    else:
        with open(log_file, "w") as f:
            json.dump([log_entry], f, indent=2)

    return {
        "success": log_entry["success"],
        "action_taken": log_entry["action"],
        "message": log_entry["description"]
    }
