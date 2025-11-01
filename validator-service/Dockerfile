FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del servicio
COPY . .

# Levanta la app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]


