import httpx
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)

class AuditClient:
    def __init__(self, audit_service_url: str = "http://audit-service:8003"):
        self.audit_service_url = audit_service_url
        self.timeout = 5.0
    
    async def log_user_event(
        self,
        event: str,
        user_data: Dict[str, Any],
        outcome: str,
        action: str = "other",
        additional_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registra un evento de usuario en el audit service.
        
        Args:
            event: Tipo de evento (ej: "user_register")
            user_data: Datos del usuario (nombre, email, nit)
            outcome: "success" o "fail"
            action: "email", "nit" o "other"
            additional_details: Información adicional del evento
        
        Returns:
            True si se registró exitosamente, False en caso contrario
        """
        try:
            # Preparar datos para el audit
            audit_data = {
                "event": event,
                "request": {
                    "nombreusuario": user_data.get("nombre", ""),
                    "useremail": user_data.get("email", ""),
                    "nit": str(user_data.get("nit", ""))
                },
                "outcome": outcome,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": str(uuid.uuid4())
            }
            
            # Agregar detalles adicionales si existen
            if additional_details:
                audit_data["request"].update(additional_details)
            
            # Enviar al audit service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.audit_service_url}/audit/register",
                    json=audit_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 201:
                    logger.info(f"Evento de auditoría registrado: {event} - {outcome}")
                    return True
                else:
                    logger.warning(f"Error al registrar auditoría: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error conectando con audit service: {str(e)}")
            return False
    
    async def log_user_register_success(
        self,
        user_data: Dict[str, Any],
        user_id: int,
        institucion_id: int
    ) -> bool:
        """Registra un registro de usuario exitoso."""
        additional_details = {
            "userId": user_id,
            "institucionId": institucion_id,
            "resultado": "usuario_creado"
        }
        
        return await self.log_user_event(
            event="user_register",
            user_data=user_data,
            outcome="success",
            action="email",
            additional_details=additional_details
        )
    
    async def log_user_register_error(
        self,
        user_data: Dict[str, Any],
        error_type: str,
        error_details: str,
        action: str = "other"
    ) -> bool:
        """Registra un error en el registro de usuario."""
        additional_details = {
            "error_type": error_type,
            "error_details": error_details
        }
        
        return await self.log_user_event(
            event="user_register",
            user_data=user_data,
            outcome="fail",
            action=action,
            additional_details=additional_details
        )