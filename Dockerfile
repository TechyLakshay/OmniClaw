FROM python:3.11-slim

# system deps required by some packages (httpx, supabase, ddgs)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy requirements first — pip layer only rebuilds when this file changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# notes folder must exist inside container
RUN mkdir -p /app/notes

EXPOSE 8000

CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]