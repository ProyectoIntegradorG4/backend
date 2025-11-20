from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.database.connection import get_db
from app.models.entrega import Entrega, EventoEntrega, EstadoEntrega

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entregas", tags=["entregas"])


@router.get("/{nit}")
def listar_entregas(
    nit: str,
    estado: Optional[str] = Query(None, description="Estado de la entrega"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Lista entregas asociadas a un NIT, con filtro opcional por estado.
    """
    try:
        query = db.query(Entrega).filter(Entrega.nit == nit)
        if estado:
            try:
                estado_enum = EstadoEntrega[estado.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Estado inválido. Válidos: {[e.value for e in EstadoEntrega]}")
            query = query.filter(Entrega.estado_entrega == estado_enum)
        total = query.count()
        entregas = (
            query.order_by(Entrega.fecha_hora_programada.desc().nullslast())
            .offset((pagina - 1) * por_pagina)
            .limit(por_pagina)
            .all()
        )
        items = [
            {
                "entrega_id": str(e.entrega_id),
                "pedido_id": str(e.pedido_id),
                "nit": e.nit,
                "estado_entrega": e.estado_entrega.value,
                "fecha_hora_programada": e.fecha_hora_programada,
                "fecha_hora_estimada_llegada": e.fecha_hora_estimada_llegada,
                "fecha_hora_entrega_real": e.fecha_hora_entrega_real,
                "vehiculo_id": e.vehiculo_id,
                "conductor_id": e.conductor_id,
                "placa_vehiculo": e.placa_vehiculo,
            }
            for e in entregas
        ]
        return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "entregas": items}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listar_entregas: {e}")
        raise HTTPException(status_code=500, detail="ERROR_INTERNO")


@router.get("/{entrega_id}/tracking")
def tracking_entrega(
    entrega_id: str,
    db: Session = Depends(get_db),
):
    """
    Retorna tracking de una entrega: última posición, ETA y últimos eventos.
    """
    try:
        entrega = db.query(Entrega).filter(Entrega.entrega_id == entrega_id).first()
        if not entrega:
            raise HTTPException(status_code=404, detail="Entrega no encontrada")
        eventos = (
            db.query(EventoEntrega)
            .filter(EventoEntrega.entrega_id == entrega_id)
            .order_by(EventoEntrega.timestamp.desc())
            .limit(20)
            .all()
        )
        ultima = eventos[0] if eventos else None
        return {
            "entrega_id": entrega_id,
            "estado_entrega": entrega.estado_entrega.value,
            "ultima_posicion": {
                "latitud": ultima.latitud,
                "longitud": ultima.longitud,
                "timestamp": ultima.timestamp,
            }
            if ultima
            else None,
            "eta": entrega.fecha_hora_estimada_llegada,
            "eventos": [
                {
                    "evento_id": str(ev.evento_id),
                    "timestamp": ev.timestamp,
                    "latitud": ev.latitud,
                    "longitud": ev.longitud,
                    "tipo_evento": ev.tipo_evento,
                    "descripcion": ev.descripcion,
                }
                for ev in eventos
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking_entrega: {e}")
        raise HTTPException(status_code=500, detail="ERROR_INTERNO")


