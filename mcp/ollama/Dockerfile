FROM ollama/ollama

# Update package lists and install curl and bash
RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

COPY start-ollama.sh /start-ollama.sh
RUN chmod +x /start-ollama.sh

ENTRYPOINT ["/start-ollama.sh"]
