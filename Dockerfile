FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy source code and prebuilt frontend
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY reports/ ./reports/

WORKDIR /app/backend

EXPOSE 8000

ENV PORT=8000
ENV ENV=production

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
