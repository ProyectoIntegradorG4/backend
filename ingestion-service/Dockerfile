FROM python:3.12-slim

WORKDIR /app

# Instalar curl para healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del servicio
COPY . .

# Levanta la app FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]


