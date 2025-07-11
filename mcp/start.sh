#!/bin/bash

# # Start Ollama server
# ollama serve &

# # Wait for it to become ready
# until curl -s http://localhost:11434/ | grep -q 'Ollama'; do
#   echo "[MCP] Waiting for Ollama to be ready..."
#   sleep 2
# done

# # Pull and preload model
# ollama pull mistral
# echo "[MCP] Preloading model..."
# ollama run mistral <<< "Say hello" > /dev/null

# # Change directory to mcp before starting MCP server
# cd /app/mcp
# uvicorn main:app --host 0.0.0.0 --port 9000

# Change directory to app
cd /app/mcp

# Start MCP server
uvicorn main:app --host 0.0.0.0 --port 9000