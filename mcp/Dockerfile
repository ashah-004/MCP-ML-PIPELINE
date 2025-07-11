# FROM ubuntu:22.04

# # Install system dependencies
# RUN apt-get update && \
#     apt-get install -y curl git python3 python3-pip wget libssl-dev libcurl4-openssl-dev && \
#     apt-get clean

# # Install Ollama
# RUN curl -fsSL https://ollama.com/install.sh | bash

# # Set up Python environment
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# RUN mkdir -p /app/healing_logs

# # Install kubectl (for accessing pod logs)
# RUN curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
#     install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
#     rm kubectl

# # Fix the script path (this was the problem)
# RUN chmod +x /app/start.sh
# CMD ["/app/start.sh"]


FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl git python3 python3-pip wget libssl-dev libcurl4-openssl-dev && \
    apt-get clean

# RUN pip install google-cloud-aiplatform google-auth

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/healing_logs

# Install kubectl (for accessing pod logs)
RUN curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
