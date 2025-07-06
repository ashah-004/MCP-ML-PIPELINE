# llm_utils.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"  # or "phi3", "llama3", etc.

def infer_healing_action(logs: str) -> dict:
    prompt = f"""
You are a Kubernetes DevOps assistant. Analyze the following pod logs and provide a recommended healing action.

Logs:
{logs}

Respond with one of the following actions:
- restart: if restarting the deployment might fix it
- manual: if human intervention is needed
- unknown: if the error cannot be inferred

Also include a short description explaining the reason.
Reply in JSON format with keys: action, description.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        content = response.json()["response"].strip()

        # Try parsing the response as JSON
        import json
        parsed = json.loads(content)
        return parsed

    except Exception as e:
        return {
            "action": "unknown",
            "description": f"Ollama_Error: {str(e)}"
        }
