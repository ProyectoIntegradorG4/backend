# app/migration/runner.py
from pathlib import Path
import logging

from sqlalchemy import text
from app.database.session import engine  # el mismo engine que usas en get_db

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent

def run_migrations():
    sql_path = MIGRATIONS_DIR / "0001_init.sql"

    if not sql_path.exists():
        logger.warning(f"[MIGRATION] No se encontró el archivo {sql_path}")
        return

    sql = sql_path.read_text(encoding="utf-8")

    # Ejecutamos sentencia por sentencia para evitar problemas con múltiples statements
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    logger.info(f"[MIGRATION] Ejecutando {len(statements)} sentencias de {sql_path.name}")

    with engine.begin() as conn:  # abre transacción y hace commit al final
        for stmt in statements:
            conn.execute(text(stmt))

    logger.info("[MIGRATION] Migraciones aplicadas correctamente")
