ARG ENV=local
FROM public.ecr.aws/lambda/python:3.11 AS lambda-base
FROM python:3.11-slim AS local-base

# Selecciona la base según entorno
FROM ${ENV}-base

WORKDIR /app

# Copia dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del servicio
COPY . .

# Levanta la app FastAPI
CMD ["bash", "-c", "if [ \"$ENV\" = 'lambda' ]; then echo 'Lambda handler ready'; else uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]


