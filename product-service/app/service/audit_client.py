
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def send_audit_event(
    action: str,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
   
    logger.debug(
        f"[AUDIT] action={action}, entity_id={entity_id}, details={details}"
    )
    return None
