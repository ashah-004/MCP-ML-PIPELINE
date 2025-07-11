# import logging
# from k8s_utils import restart_deployment
# from llm_utils import infer_healing_action
# import os
# import json
# from datetime import datetime

# LOG_DIR = "/app/healing_logs"
# os.makedirs(LOG_DIR, exist_ok=True)

# def analyze_logs_and_heal(namespace: str, deployment_name: str, pod_logs: str) -> dict:
#     log_entry = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "namespace": namespace,
#         "deployment_name": deployment_name,
#         "logs": pod_logs,
#         "action": None,
#         "description": None,
#         "success": False
#     }

#     # Step 1: Use LLM to infer action
#     result = infer_healing_action(pod_logs)
#     action = result.get("action")
#     description = result.get("description")
#     log_entry.update({"action": action, "description": description})

#     # Step 2: Perform Action
#     if action == "restart":
#         restarted = restart_deployment(namespace, deployment_name)
#         log_entry["success"] = restarted
#     elif action == "unknown":
#         log_entry["success"] = False
#     else:
#         log_entry["success"] = False  # for now, only restart is supported

#     # Step 3: Persist structured log
#     log_file = os.path.join(LOG_DIR, "healing_dataset.json")
#     if os.path.exists(log_file):
#         with open(log_file, "r+") as f:
#             data = json.load(f)
#             data.append(log_entry)
#             f.seek(0)
#             json.dump(data, f, indent=2)
#     else:
#         with open(log_file, "w") as f:
#             json.dump([log_entry], f, indent=2)

#     return {
#         "success": log_entry["success"],
#         "action_taken": log_entry["action"],
#         "message": log_entry["description"]
#     }
import logging
import os
import json
import time
from datetime import datetime
from k8s_utils import restart_deployment, exec_command_in_pod, find_target_pod, wait_for_pod_ready
from llm_utils import infer_healing_commands

LOG_DIR = "/app/healing_logs"
os.makedirs(LOG_DIR, exist_ok=True)

def extract_relevant_logs(logs: str) -> str:
    # Extract last 100 lines to capture tracebacks/errors, removing leading warnings
    lines = logs.strip().splitlines()
    if len(lines) > 100:
        return "\n".join(lines[-100:])
    return logs

def analyze_logs_and_heal(namespace: str, deployment_name: str, pod_logs: str) -> dict:
    print(f"[MCP] Healing triggered for namespace={namespace}, deployment={deployment_name}")
    pod_name = find_target_pod(namespace, deployment_name)
    print(f"[MCP] Target pod identified: {pod_name}")

    pod_logs = extract_relevant_logs(pod_logs)

    result = infer_healing_commands(pod_logs)
    commands = result.get("commands", [])
    description = result.get("description", "")
    print(f"[MCP] Inferred commands: {commands}")
    print(f"[MCP] Healing description: {description}")

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "namespace": namespace,
        "deployment_name": deployment_name,
        "pod_name": pod_name,
        "logs": pod_logs,
        "healing_action": commands,
        "message": "",
        "success": False
    }

    filtered_commands = [cmd for cmd in commands if cmd.strip() and '<' not in cmd and '>' not in cmd]
    if len(filtered_commands) < len(commands):
        print("[MCP] Warning: Some placeholder commands were removed.")
    if not filtered_commands:
        log_entry.update({"message": "No valid healing commands found", "success": False})
        save_healing_log(log_entry)
        return {"success": False, "action_taken": "none", "message": "No healing commands to run"}

    pod_ready = wait_for_pod_ready(namespace, pod_name, timeout=10)
    if not pod_ready:
        print(f"[MCP] Pod {pod_name} not ready. Restarting deployment...")
        restarted = restart_deployment(namespace, deployment_name)
        if not restarted:
            message = f"Failed to restart deployment {deployment_name}."
            log_entry.update({"message": message, "success": False})
            save_healing_log(log_entry)
            return {"success": False, "action_taken": "restart_failed", "message": message}

        time.sleep(5)
        pod_name = find_target_pod(namespace, deployment_name)
        print(f"[MCP] New target pod after restart: {pod_name}")
        pod_ready = wait_for_pod_ready(namespace, pod_name, timeout=60)
        if not pod_ready:
            message = f"New pod {pod_name} not ready after restart."
            log_entry.update({"message": message, "success": False})
            save_healing_log(log_entry)
            return {"success": False, "action_taken": "new_pod_not_ready", "message": message}
        print(f"[MCP] Pod {pod_name} is ready after restart. Proceeding with healing commands.")

    full_output = []
    all_success = True
    for cmd in filtered_commands:
        print(f"[MCP] Executing command in pod: {cmd}")
        result = exec_command_in_pod(namespace, pod_name, cmd)
        success = result["success"]
        output = result["output"]
        full_output.append(f"$ {cmd}\n{output}")
        if not success:
            print(f"[MCP] Command failed: {cmd}")
            all_success = False
            break

    log_entry["success"] = all_success
    log_entry["message"] = "\n\n".join(full_output)
    save_healing_log(log_entry)

    return {
        "success": all_success,
        "action_taken": "; ".join(filtered_commands),
        "message": log_entry["message"]
    }

def save_healing_log(log_entry):
    log_file = os.path.join(LOG_DIR, "healing_dataset.json")
    try:
        if os.path.exists(log_file):
            with open(log_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=2)
        else:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump([log_entry], f, indent=2)
        print("[MCP] Healing log written successfully.")
    except Exception as e:
        print(f"[MCP] Error writing healing log: {e}")
