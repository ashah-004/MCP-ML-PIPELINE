#!/bin/sh

ollama serve &

echo "⏳ Waiting for Ollama server to start..."
until curl -s http://localhost:11434; do
  echo "🕒 Server not ready. Sleeping..."
  sleep 2
done

echo "✅ Pulling mistral model..."
curl -X POST http://localhost:11434/api/pull -d '{"name":"mistral"}' -H "Content-Type: application/json"

echo "🎉 Model pulled!"

# Wait forever to keep container alive
wait
