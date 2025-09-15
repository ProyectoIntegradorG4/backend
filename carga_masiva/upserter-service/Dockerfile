
FROM python:3.11-slim

WORKDIR /app

# Copia dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del servicio
COPY . .

# Levanta la app FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
