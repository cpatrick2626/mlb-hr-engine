FROM python:3.12-slim

WORKDIR /app

# gcc needed by some scipy/numpy wheels
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY mlb_hr_engine_v4/requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy engine source (WORKDIR = /app, so imports resolve directly)
COPY mlb_hr_engine_v4/ .

EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
