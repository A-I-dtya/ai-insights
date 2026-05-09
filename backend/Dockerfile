# ─── Backend container ────────────────────────────────────────────────
FROM python:3.12-slim

# Don't write .pyc, flush stdout/stderr immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and pre-generated data files
COPY app ./app
COPY data ./data

EXPOSE 8000

# Bind to 0.0.0.0 so the container is reachable from the host
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
