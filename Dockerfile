FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# COPY app/model /app/app/model
COPY app/*.py /app/app/

# Create protected directory and file with root-only write
RUN mkdir -p /app/protected && \
    touch /app/protected/locked.txt && \
    echo "protected content" > /app/protected/locked.txt && \
    chmod 400 /app/protected/locked.txt && \
    chown root:root /app/protected/locked.txt

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser /app
USER appuser

EXPOSE 8000

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
