# visit-service
Microservicio para registrar visitas a clientes (FastAPI + PostgreSQL) con adjuntos y RBAC.


**Carpetas:** database, models, routes, services, test


## Endpoints
- POST /visits
- POST /visits/{visit_id}/evidence
- GET /api/v1/visits/client/{client_id}
- GET /api/v1/visits/{visit_id}


## Desarrollo rápido
cp .env.sample .env
psql $DATABASE_URL -f /app/migrations/0001_init.sql
uvicorn main:app --reload --port 8011