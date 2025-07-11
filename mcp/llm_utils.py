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
# llm_utils.py

import json
import time
from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(project="ai-detector-pipeline", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-001")

PROMPT_TEMPLATE = """You are a Kubernetes pod self-healing assistant.

You will receive container logs that include a traceback or runtime error. Your job is to return only the minimal one-liner shell commands needed to fix the root cause **inside the container**.

### Pod Logs:
{logs}

### Output format:
{{"commands": ["cmd1", "cmd2"], "description": "Short explanation of the fix"}}

### Guidelines:
- Return only bash commands to fix Python/OS-level errors (e.g., `pip install xyz package`)
- Only fix real crashes (e.g., ModuleNotFoundError, FileNotFoundError, ImportError, RuntimeError, etc.)
- Do NOT respond to warnings like FutureWarning or DeprecationWarning
- Return a single-line valid JSON. No Markdown, no explanations, no code blocks.
- Do NOT include commands like `apt`, `yum`, `rm -rf`, `shutdown`, or multi-line shell logic
"""

def extract_key_errors(logs: str, max_chars=500) -> str:
    """
    Extracts crash-related lines from logs and returns last `max_chars` characters.
    """
    lines = logs.strip().splitlines()
    error_lines = []
    keywords = ["Traceback", "ModuleNotFoundError", "ImportError", "FileNotFoundError", "PermissionError", "RuntimeError", "NameError"]
    exclude = ["FutureWarning", "DeprecationWarning"]

    for line in reversed(lines):
        if any(x in line for x in keywords) and not any(y in line for y in exclude):
            error_lines.insert(0, line)

    extracted = "\n".join(error_lines)
    return extracted[-max_chars:] if extracted else "\n".join(lines[-10:])[-max_chars:]

def infer_healing_commands(logs: str) -> dict:
    prompt_logs = extract_key_errors(logs)
    prompt = PROMPT_TEMPLATE.format(logs=prompt_logs)

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 512
                }
            )

            output = response.text.strip()
            print(f"[MCP] Gemini raw response:\n{output}")

            # Extract JSON block
            json_start = output.find("{")
            json_end = output.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("No valid JSON block found.")

            healing = json.loads(output[json_start:json_end])

            # Validate and filter commands
            if not isinstance(healing, dict):
                raise ValueError("Expected a JSON object")

            if "commands" not in healing or not isinstance(healing["commands"], list):
                raise ValueError("Missing or invalid 'commands' key")

            if "description" not in healing:
                healing["description"] = "Auto-generated healing commands."

            blacklist = [
                "rm -rf", "shutdown", "reboot", "apt", "yum", "apk", "uninstall",
                "input(", "&& read", "curl | sh", "wget | sh"
            ]

            filtered = [
                cmd for cmd in healing["commands"]
                if not any(bad in cmd for bad in blacklist)
                and "\n" not in cmd
                and ";" not in cmd
            ]

            if not filtered:
                raise ValueError("All commands were filtered out")

            healing["commands"] = filtered
            return healing

        except Exception as e:
            print(f"[MCP] Gemini error (attempt {attempt + 1}): {e}")
            time.sleep(2)

    return {
        "commands": [],
        "description": "Gemini failure: Unable to infer valid healing commands."
    }

