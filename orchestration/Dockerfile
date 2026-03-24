FROM python:3.11.8-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY memory-layer ./memory-layer
COPY config.py orchestrator.py ./
ENV PYTHONUNBUFFERED=1
CMD ["python", "orchestrator.py"]
