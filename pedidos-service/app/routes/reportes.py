"""
Rutas de reportes de vendedores (HU-WEB-010)
Endpoints para consulta de KPIs, rankings y dashboard
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
import logging

from app.database.connection import get_db
from app.services.reportes import ReportesService
from app.schemas.reporte import KPIVendedor, ReporteRegion, DashboardReportes
# from app.services.rbac import require_supervisor_ventas  # TODO: Implementar RBAC

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])
logger = logging.getLogger(__name__)


@router.get(
    "/vendedores/kpi",
    response_model=KPIVendedor,
    summary="Obtener KPI de vendedor",
    description="""
    Retorna los KPIs de un vendedor específico en un periodo.
    
    Incluye:
    - Ventas totales (valor y unidades)
    - Número de pedidos
    - Metas y cumplimiento vs objetivos
    - Tendencia temporal
    
    **SLA**: ≤2 segundos p95
    **RBAC**: Supervisor de Ventas, Gerente de Cuenta
    """
)
async def obtener_kpi_vendedor(
    vendedor_id: int = Query(..., description="ID del vendedor", gt=0),
    desde: date = Query(..., description="Fecha de inicio del periodo (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha de fin del periodo (YYYY-MM-DD)"),
    territorio_id: Optional[str] = Query(None, description="Filtrar por territorio específico"),
    producto_id: Optional[str] = Query(None, description="Filtrar por producto específico"),
    db: Session = Depends(get_db)
    # current_user: dict = Depends(require_supervisor_ventas)  # TODO: Implementar RBAC
):
    """
    Endpoint para obtener KPIs de un vendedor en un periodo.
    """
    try:
        # Validar periodo
        if desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha 'desde' debe ser anterior o igual a 'hasta'"
            )
        
        # Validar que el periodo no sea mayor a 1 año
        dias = (hasta - desde).days
        if dias > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El periodo no puede ser mayor a 365 días"
            )
        
        # Generar reporte
        kpi = await ReportesService.generar_kpi_vendedor(
            db=db,
            vendedor_id=vendedor_id,
            desde=desde,
            hasta=hasta,
            territorio_id=territorio_id,
            producto_id=producto_id
        )
        
        logger.info(f"KPI generado para vendedor {vendedor_id}, periodo {desde} - {hasta}")
        return kpi
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando KPI vendedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el reporte"
        )


@router.get(
    "/vendedores/region",
    response_model=ReporteRegion,
    summary="Obtener reporte por región",
    description="""
    Retorna el reporte consolidado de una región con ranking de vendedores.
    
    Incluye:
    - Resumen agregado de la región
    - Ranking de vendedores por ventas
    - Cumplimiento vs metas por vendedor
    - Tendencia temporal de la región
    
    **SLA**: ≤2 segundos p95
    **RBAC**: Supervisor de Ventas, Gerente de Cuenta
    """
)
async def obtener_reporte_region(
    territorio_id: str = Query(..., description="ID del territorio/región"),
    desde: date = Query(..., description="Fecha de inicio del periodo (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha de fin del periodo (YYYY-MM-DD)"),
    producto_id: Optional[str] = Query(None, description="Filtrar por producto específico"),
    db: Session = Depends(get_db)
    # current_user: dict = Depends(require_supervisor_ventas)  # TODO: Implementar RBAC
):
    """
    Endpoint para obtener reporte consolidado de una región con ranking.
    """
    try:
        # Validar periodo
        if desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha 'desde' debe ser anterior o igual a 'hasta'"
            )
        
        if (hasta - desde).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El periodo no puede ser mayor a 365 días"
            )
        
        # Generar reporte
        reporte = await ReportesService.generar_reporte_region(
            db=db,
            territorio_id=territorio_id,
            desde=desde,
            hasta=hasta,
            producto_id=producto_id
        )
        
        logger.info(f"Reporte región generado para {territorio_id}, periodo {desde} - {hasta}")
        return reporte
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando reporte región: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el reporte"
        )


@router.get(
    "/vendedores/dashboard",
    response_model=DashboardReportes,
    summary="Obtener dashboard consolidado",
    description="""
    Retorna el dashboard ejecutivo con KPIs principales y gráficos.
    
    Incluye:
    - KPIs principales (ventas, pedidos, cumplimiento)
    - Gráfico de tendencia temporal (Chart.js LineChart)
    - Gráfico de ranking de vendedores (Chart.js BarChart)
    - Gráfico de distribución de cumplimiento (Chart.js DoughnutChart)
    - Top vendedores del periodo
    - Alertas y recomendaciones
    
    Todos los gráficos incluyen datos formateados para Chart.js.
    
    **SLA**: ≤2 segundos p95
    **RBAC**: Supervisor de Ventas, Gerente de Cuenta
    """
)
async def obtener_dashboard(
    desde: date = Query(
        ...,
        description="Fecha de inicio del periodo (YYYY-MM-DD)",
        example="2026-01-01"
    ),
    hasta: date = Query(
        ...,
        description="Fecha de fin del periodo (YYYY-MM-DD)",
        example="2026-03-31"
    ),
    db: Session = Depends(get_db)
    # current_user: dict = Depends(require_supervisor_ventas)  # TODO: Implementar RBAC
):
    """
    Endpoint para obtener el dashboard ejecutivo consolidado.
    Datos listos para Chart.js en el frontend.
    """
    try:
        # Validar periodo
        if desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha 'desde' debe ser anterior o igual a 'hasta'"
            )
        
        if (hasta - desde).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El periodo no puede ser mayor a 365 días"
            )
        
        # Si no se especifica periodo, usar últimos 90 días
        if desde is None or hasta is None:
            hasta = date.today()
            desde = hasta - timedelta(days=90)
        
        # Generar dashboard
        dashboard = await ReportesService.generar_dashboard(
            db=db,
            desde=desde,
            hasta=hasta
        )
        
        logger.info(f"Dashboard generado para periodo {desde} - {hasta}")
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el dashboard"
        )


@router.get(
    "/vendedores/kpi/resumen",
    summary="Resumen rápido de KPIs (opcional)",
    description="Endpoint simplificado para obtener solo métricas principales sin tendencia"
)
async def obtener_resumen_kpis(
    vendedor_id: int = Query(..., gt=0),
    desde: date = Query(...),
    hasta: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint ligero para obtener solo las métricas principales de un vendedor.
    Útil para vistas rápidas o widgets.
    """
    try:
        if desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Periodo inválido"
            )
        
        ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
            db, vendedor_id, None, None, desde, hasta
        )
        
        meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
            db, vendedor_id, None, None, desde, hasta
        )
        
        cumplimiento = None
        if meta_unidades and meta_unidades > 0:
            cumplimiento = round((ventas_unidades / meta_unidades) * 100, 1)
        
        return {
            "vendedor_id": vendedor_id,
            "periodo": {"desde": desde, "hasta": hasta},
            "ventas_valor": ventas_valor,
            "ventas_unidades": ventas_unidades,
            "pedidos": num_pedidos,
            "cumplimiento_porcentaje": cumplimiento
        }
        
    except Exception as e:
        logger.error(f"Error en resumen KPIs: {e}")
        raise HTTPException(status_code=500, detail="Error generando resumen")
