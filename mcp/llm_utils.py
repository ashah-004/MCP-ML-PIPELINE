# # llm_utils.py
# import requests

# OLLAMA_URL = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "mistral"  # or "phi3", "llama3", etc.

# def infer_healing_action(logs: str) -> dict:
#     prompt = f"""
# You are a Kubernetes DevOps assistant. Analyze the following pod logs and provide a recommended healing action.

# Logs:
# {logs}

# Respond with one of the following actions:
# - restart: if restarting the deployment might fix it
# - manual: if human intervention is needed
# - unknown: if the error cannot be inferred

# Also include a short description explaining the reason.
# Reply in JSON format with keys: action, description.
# """

#     payload = {
#         "model": OLLAMA_MODEL,
#         "prompt": prompt,
#         "stream": False
#     }

#     try:
#         response = requests.post(OLLAMA_URL, json=payload)
#         response.raise_for_status()
#         content = response.json()["response"].strip()

#         # Try parsing the response as JSON
#         import json
#         parsed = json.loads(content)
#         return parsed

#     except Exception as e:
#         return {
#             "action": "unknown",
#             "description": f"Ollama_Error: {str(e)}"
#         }
import requests
import json
import time

from vertexai.language_models import TextGenerationModel
from google.cloud import aiplatform

OLLAMA_URL = "http://ollama.mcp.svc.cluster.local:11434/api/generate"
MODEL = "mistral"

PROMPT_TEMPLATE = """You are a Kubernetes pod self-healing assistant.

You will receive container logs that include a traceback or runtime error. Your job is to return only the minimal one-liner shell commands needed to fix the root cause **inside the container**.

### Pod Logs:
{logs}

### Output format:
{{"commands": ["cmd1", "cmd2"], "description": "Short explanation of the fix"}}

### Guidelines:
- Return only bash commands to fix Python/OS-level errors (e.g., `pip install tiktoken`)
- Only fix real crashes (e.g., ModuleNotFoundError, FileNotFoundError, ImportError, RuntimeError, etc.)
- Do NOT respond to warnings like FutureWarning or DeprecationWarning
- Return a single-line valid JSON. No Markdown, no explanations, no code blocks.
- Do NOT include commands like `apt`, `yum`, `rm -rf`, `shutdown`, or multi-line shell logic
"""

def extract_key_errors(logs: str, max_chars=500) -> str:
    """
    Extracts last lines with actual crash content (ignores warnings).
    Returns last max_chars of those lines.
    """
    lines = logs.strip().splitlines()
    error_lines = []
    keywords = ["Traceback", "ModuleNotFoundError", "ImportError", "FileNotFoundError", "PermissionError", "RuntimeError", "NameError"]
    exclude = ["FutureWarning", "DeprecationWarning"]

    for line in reversed(lines):
        if any(x in line for x in keywords) and not any(y in line for y in exclude):
            error_lines.insert(0, line)  # keep original order

    extracted = "\n".join(error_lines)
    return extracted[-max_chars:] if extracted else "\n".join(lines[-10:])[-max_chars:]

def infer_healing_commands(logs: str, stream_timeout: int = 120):
    prompt_logs = extract_key_errors(logs)
    prompt = PROMPT_TEMPLATE.format(logs=prompt_logs)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True
    }

    for attempt in range(3):
        try:
            response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=stream_timeout)
            response.raise_for_status()

            output = ""
            for line in response.iter_lines():
                if line:
                    try:
                        raw = line.decode("utf-8").strip()
                        if raw.startswith("data: "):
                            raw = raw[len("data: "):]
                        data = json.loads(raw)
                        output += data.get("response", "")
                    except Exception:
                        continue

            print(f"[MCP] Ollama raw accumulated output:\n{output}")

            json_start = output.find("{")
            json_end = output.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("No valid JSON block found.")

            healing = json.loads(output[json_start:json_end])

            if not isinstance(healing, dict):
                raise ValueError("Expected a JSON object")

            if "commands" not in healing or not isinstance(healing["commands"], list):
                raise ValueError("Missing or invalid 'commands' key")

            if "description" not in healing:
                healing["description"] = "Auto-generated healing commands."

            blacklist = ["rm -rf", "shutdown", "reboot", "apt", "yum", "apk", "uninstall", "input(", "&& read", "curl | sh", "wget | sh"]
            filtered = [
                cmd for cmd in healing["commands"]
                if not any(bad in cmd for bad in blacklist) and "\n" not in cmd and ";" not in cmd
            ]

            if not filtered:
                raise ValueError("All commands were filtered out")

            healing["commands"] = filtered
            return healing

        except Exception as e:
            print(f"[MCP] Ollama error (attempt {attempt + 1}): {e}")
            time.sleep(2)

    return {
        "commands": [],
        "description": "Ollama failure: Unable to infer valid healing commands."
    }
