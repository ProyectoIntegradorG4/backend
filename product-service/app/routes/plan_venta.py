# app/routes/plan_venta.py
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.plan_venta import (
    PlanVentaCreate,
    PlanVentaCreateResponse,
    PlanVentaOut,
    PlanVentaDetailOut,
    TerritorioOut,
    MetaOut
)
from app.service.plan_venta_service import PlanVentaService
from app.service.rbac import require_role_admin_ventas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/planes-venta", tags=["planes-venta"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PlanVentaCreateResponse,
    dependencies=[Depends(require_role_admin_ventas)]
)
def crear_plan_venta(
    payload: PlanVentaCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un plan de venta con metas por producto, territorio y vendedor.
    
    **Requisitos:**
    - Rol: Administrador de Ventas
    - Nombre único
    - Periodo válido (hasta >= desde)
    - Al menos 1 territorio y 1 meta
    - Productos, territorios y vendedores deben existir
    - No puede haber metas duplicadas (producto + territorio + vendedor)
    - Cada meta debe tener al menos un objetivo (cantidad o valor) > 0
    
    **SLA:** Respuesta en ≤ 2 segundos (p95)
    """
    try:
        plan = PlanVentaService.crear_plan_venta(db, payload)
        
        return PlanVentaCreateResponse(
            planId=str(plan.plan_id),
            estado=plan.estado,
            metas_creadas=len(payload.metas),
            mensaje="Plan de venta creado exitosamente"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado creando plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear plan de venta: {str(e)}"
        )


@router.get(
    "",
    response_model=dict,
    dependencies=[Depends(require_role_admin_ventas)]
)
def listar_planes_venta(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Búsqueda por nombre (case-insensitive)"),
    estado: Optional[str] = Query(None, pattern="^(activo|borrador|cerrado|archivado)$", description="Filtro por estado"),
    periodo_from: Optional[str] = Query(None, description="Filtro por período - fecha inicio (YYYY-MM-DD)"),
    periodo_to: Optional[str] = Query(None, description="Filtro por período - fecha fin (YYYY-MM-DD)"),
    territorioId: Optional[str] = Query(None, description="Filtro por territorio incluido en el plan"),
    productoId: Optional[str] = Query(None, description="Filtro por producto incluido en metas (opcional)"),
    sort: str = Query("updated_at", pattern="^(nombre|periodo_desde|updated_at)$", description="Campo de ordenamiento"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Dirección de ordenamiento"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(25, ge=1, le=50, description="Tamaño de página (máximo 50)")
):
    """
    Lista los planes de venta con búsqueda, filtros y paginación (HU-WEB-009)
    
    **Requisitos:**
    - Rol: Administrador de Ventas
    
    **Búsqueda:**
    - q: Busca en el nombre del plan (case-insensitive)
    
    **Filtros opcionales:**
    - estado: activo, borrador, cerrado, archivado
    - periodo_from, periodo_to: Rango de fechas (intersección con período del plan)
    - territorioId: Planes que incluyan este territorio
    - productoId: Planes con metas que incluyan este producto
    
    **Ordenamiento:**
    - sort: nombre, periodo_desde, updated_at (default: updated_at)
    - order: asc, desc (default: desc)
    
    **SLA:** p95 ≤ 2 segundos; p50 ≤ 500 ms
    """
    try:
        from datetime import date
        
        # Parsear fechas si se proporcionan
        periodo_from_date = date.fromisoformat(periodo_from) if periodo_from else None
        periodo_to_date = date.fromisoformat(periodo_to) if periodo_to else None
        
        planes, total = PlanVentaService.listar_planes_venta(
            db=db,
            q=q,
            estado=estado,
            periodo_from=periodo_from_date,
            periodo_to=periodo_to_date,
            territorio_id=territorioId,
            producto_id=productoId,
            sort=sort,
            order=order,
            page=page,
            page_size=page_size
        )
        
        items = []
        for plan in planes:
            items.append({
                "planId": str(plan.plan_id),
                "nombre": plan.nombre,
                "periodo": {
                    "desde": plan.periodo_desde.isoformat(),
                    "hasta": plan.periodo_hasta.isoformat()
                },
                "estado": plan.estado,
                "territorios_count": len(plan.territorios),
                "metas_count": len(plan.metas),
                "actualizado_en": plan.updated_at.isoformat() if plan.updated_at else None
            })
        
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items
        }
    
    except ValueError as e:
        logger.error(f"Error de validación en filtros: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listando planes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar planes de venta: {str(e)}"
        )


@router.get(
    "/{plan_id}",
    response_model=dict,
    dependencies=[Depends(require_role_admin_ventas)]
)
def obtener_plan_venta(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Obtiene el detalle completo de un plan de venta incluyendo territorios y metas.
    
    **Requisitos:**
    - Rol: Administrador de Ventas
    """
    try:
        plan = PlanVentaService.obtener_plan_por_id(db, str(plan_id))
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan de venta con ID {plan_id} no encontrado"
            )
        
        # Construir respuesta manualmente para evitar problemas de serialización
        territorios = []
        for pt in plan.territorios:
            territorios.append({
                "territorio_id": pt.territorio.territorio_id,
                "nombre": pt.territorio.nombre,
                "codigo": pt.territorio.codigo,
                "pais": pt.territorio.pais,
                "activo": pt.territorio.activo
            })
        
        metas = []
        for meta in plan.metas:
            metas.append({
                "meta_id": str(meta.meta_id),
                "producto_id": meta.producto_id,
                "territorio_id": meta.territorio_id,
                "vendedor_id": meta.vendedor_id,
                "objetivo_cantidad": meta.objetivo_cantidad,
                "objetivo_valor": float(meta.objetivo_valor) if meta.objetivo_valor else None,
                "nota": meta.nota
            })
        
        return {
            "plan_id": str(plan.plan_id),
            "nombre": plan.nombre,
            "periodo_desde": plan.periodo_desde.isoformat(),
            "periodo_hasta": plan.periodo_hasta.isoformat(),
            "estado": plan.estado,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "territorios": territorios,
            "metas": metas
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener plan de venta: {str(e)}"
        )


@router.get(
    "/territorios/catalogo",
    response_model=dict,
    dependencies=[Depends(require_role_admin_ventas)]
)
def listar_territorios(
    db: Session = Depends(get_db),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo")
):
    """
    Lista el catálogo de territorios disponibles para asignar a planes.
    
    **Requisitos:**
    - Rol: Administrador de Ventas
    """
    try:
        territorios = PlanVentaService.listar_territorios(db, activo)
        
        items = []
        for territorio in territorios:
            items.append({
                "territorio_id": territorio.territorio_id,
                "nombre": territorio.nombre,
                "codigo": territorio.codigo,
                "pais": territorio.pais,
                "activo": territorio.activo
            })
        
        return {
            "total": len(items),
            "items": items
        }
    
    except Exception as e:
        logger.error(f"Error listando territorios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar territorios: {str(e)}"
        )
