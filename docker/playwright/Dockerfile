FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "playwright>=1.39.0"

RUN playwright install-deps chromium
RUN playwright install chromium

EXPOSE 3333

CMD ["python", "-m", "playwright", "run-server", "--port", "3333", "--host", "0.0.0.0"]
