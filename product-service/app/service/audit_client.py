import os
import httpx
import logging

logger = logging.getLogger(__name__)

AUDIT_URL = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8003/api/v1/audit/events")

async def send_audit_event(event_type: str, payload: dict):
    """
    Envía un evento al Audit Service (best-effort, no bloqueante de la transacción).
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(AUDIT_URL, json={
                "type": event_type,
                "payload": payload
            })
    except Exception as e:
        logger.warning(f"[audit] No se pudo enviar evento {event_type}: {e}")
