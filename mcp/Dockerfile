FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl git python3 python3-pip wget libssl-dev libcurl4-openssl-dev && \
    apt-get clean

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | bash

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/healing_logs

# Expose ports
EXPOSE 9000
EXPOSE 11434

# Start Ollama server, wait, pull model, and then launch MCP server
CMD bash -c "ollama serve & sleep 5 && ollama pull mistral && uvicorn main:app --host 0.0.0.0 --port 9000"
