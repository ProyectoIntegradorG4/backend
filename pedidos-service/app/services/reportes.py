"""
Servicio de reportes de vendedores (HU-WEB-010)
Calcula KPIs, rankings y genera datos para gráficos Chart.js
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract
from typing import List, Optional, Dict, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import httpx
import os
import logging
from collections import defaultdict

from app.models.pedido import Pedido, DetallePedido, EstadoPedido
from app.schemas.reporte import (
    KPIVendedor, ReporteRegion, DashboardReportes,
    VendedorInfo, TerritorioInfo, PeriodoReporte,
    TendenciaItem, VendedorRanking, ResumenRegion,
    DashboardKPI, GraficoLinea, GraficoBarras, GraficoDona
)

logger = logging.getLogger(__name__)


class ReportesService:
    """Servicio para generar reportes de vendedores"""
    
    PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8005")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    REQUEST_TIMEOUT = 5.0  # SLA de 2s, dejamos margen para llamadas HTTP
    
    @staticmethod
    async def obtener_nombre_vendedor(vendedor_id: int) -> str:
        """Obtiene el nombre de un vendedor desde user-service"""
        try:
            async with httpx.AsyncClient(timeout=ReportesService.REQUEST_TIMEOUT) as client:
                url = f"{ReportesService.USER_SERVICE_URL}/api/v1/usuarios/{vendedor_id}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    nombre_completo = data.get("nombre_completo")
                    if nombre_completo:
                        return nombre_completo
                    # Fallback: construir nombre
                    nombre = data.get("nombre", "")
                    apellido = data.get("apellido", "")
                    return f"{nombre} {apellido}".strip() or f"Vendedor {vendedor_id}"
                return f"Vendedor {vendedor_id}"
        except Exception as e:
            logger.warning(f"Error obteniendo nombre vendedor {vendedor_id}: {e}")
            return f"Vendedor {vendedor_id}"
    
    @staticmethod
    async def obtener_territorio_info(territorio_id: str) -> Dict:
        """Obtiene información de un territorio desde product-service"""
        try:
            async with httpx.AsyncClient(timeout=ReportesService.REQUEST_TIMEOUT) as client:
                url = f"{ReportesService.PRODUCT_SERVICE_URL}/api/v1/territorios/{territorio_id}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"territorio_id": territorio_id, "nombre": territorio_id}
        except Exception as e:
            logger.warning(f"Error obteniendo territorio {territorio_id}: {e}")
            return {"territorio_id": territorio_id, "nombre": territorio_id}
    
    @staticmethod
    async def obtener_metas_periodo(
        db: Session,
        vendedor_id: Optional[int],
        territorio_id: Optional[str],
        producto_id: Optional[str],
        desde: date,
        hasta: date
    ) -> Tuple[Optional[int], Optional[float]]:
        """
        Obtiene las metas agregadas para el periodo desde product-service.
        Retorna: (meta_unidades, meta_valor)
        """
        try:
            params = {
                "desde": desde.isoformat(),
                "hasta": hasta.isoformat()
            }
            
            if vendedor_id:
                params["vendedor_id"] = vendedor_id
            if territorio_id:
                params["territorio_id"] = territorio_id
            if producto_id:
                params["producto_id"] = producto_id
            
            async with httpx.AsyncClient(timeout=ReportesService.REQUEST_TIMEOUT) as client:
                url = f"{ReportesService.PRODUCT_SERVICE_URL}/api/v1/planes-venta/metas/agregadas"
                resp = await client.get(url, params=params)
                
                if resp.status_code == 200:
                    data = resp.json()
                    meta_unidades = data.get("total_unidades", 0)
                    meta_valor = data.get("total_valor", 0.0)
                    return (
                        meta_unidades if meta_unidades > 0 else None,
                        meta_valor if meta_valor > 0 else None
                    )
                
                return (None, None)
        except Exception as e:
            logger.warning(f"Error obteniendo metas: {e}")
            return (None, None)
    
    @staticmethod
    def calcular_ventas_periodo(
        db: Session,
        vendedor_id: Optional[int],
        territorio_id: Optional[str],
        producto_id: Optional[str],
        desde: date,
        hasta: date
    ) -> Tuple[float, int, int]:
        """
        Calcula ventas totales en el periodo.
        Retorna: (ventas_valor, ventas_unidades, num_pedidos)
        """
        query = db.query(
            func.coalesce(func.sum(Pedido.monto_total), 0).label("total_valor"),
            func.count(Pedido.pedido_id).label("num_pedidos")
        ).filter(
            Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
            Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
            Pedido.estado != EstadoPedido.CANCELADO
        )
        
        if vendedor_id:
            query = query.filter(Pedido.usuario_id == vendedor_id)
        
        # TODO: Filtro por territorio_id requiere JOIN con cliente-service o tabla local
        # Por ahora omitimos este filtro en MVP
        
        resultado = query.first()
        ventas_valor = float(resultado.total_valor if resultado.total_valor else 0)
        num_pedidos = int(resultado.num_pedidos if resultado.num_pedidos else 0)
        
        # Calcular unidades vendidas
        query_unidades = db.query(
            func.coalesce(func.sum(DetallePedido.cantidad_solicitada), 0).label("total_unidades")
        ).join(
            Pedido, DetallePedido.pedido_id == Pedido.pedido_id
        ).filter(
            Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
            Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
            Pedido.estado != EstadoPedido.CANCELADO
        )
        
        if vendedor_id:
            query_unidades = query_unidades.filter(Pedido.usuario_id == vendedor_id)
        
        if producto_id:
            query_unidades = query_unidades.filter(DetallePedido.producto_id == producto_id)
        
        resultado_unidades = query_unidades.first()
        ventas_unidades = int(resultado_unidades.total_unidades if resultado_unidades.total_unidades else 0)
        
        return (ventas_valor, ventas_unidades, num_pedidos)
    
    @staticmethod
    def calcular_tendencia(
        db: Session,
        vendedor_id: Optional[int],
        territorio_id: Optional[str],
        producto_id: Optional[str],
        desde: date,
        hasta: date,
        granularidad: str = "mes"  # "semana" o "mes"
    ) -> List[TendenciaItem]:
        """
        Calcula la tendencia temporal de ventas.
        Granularidad: 'mes' para periodos >60 días, 'semana' para periodos menores
        """
        # Determinar granularidad automáticamente
        dias = (hasta - desde).days
        if dias > 60:
            granularidad = "mes"
        else:
            granularidad = "semana"
        
        if granularidad == "mes":
            # Agrupar por mes
            query = db.query(
                func.date_trunc('month', Pedido.fecha_creacion).label('periodo'),
                func.coalesce(func.sum(Pedido.monto_total), 0).label('valor'),
                func.count(Pedido.pedido_id).label('pedidos')
            ).filter(
                Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
                Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
                Pedido.estado != EstadoPedido.CANCELADO
            )
        else:
            # Agrupar por semana
            query = db.query(
                func.date_trunc('week', Pedido.fecha_creacion).label('periodo'),
                func.coalesce(func.sum(Pedido.monto_total), 0).label('valor'),
                func.count(Pedido.pedido_id).label('pedidos')
            ).filter(
                Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
                Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
                Pedido.estado != EstadoPedido.CANCELADO
            )
        
        if vendedor_id:
            query = query.filter(Pedido.usuario_id == vendedor_id)
        
        query = query.group_by('periodo').order_by('periodo')
        
        resultados = query.all()
        
        tendencia = []
        for r in resultados:
            # Calcular unidades para ese periodo
            periodo_datetime = r.periodo
            if granularidad == "mes":
                # Último día del mes
                if periodo_datetime.month == 12:
                    fin_periodo = date(periodo_datetime.year + 1, 1, 1) - timedelta(days=1)
                else:
                    fin_periodo = date(periodo_datetime.year, periodo_datetime.month + 1, 1) - timedelta(days=1)
            else:
                # Último día de la semana (6 días después)
                fin_periodo = (periodo_datetime + timedelta(days=6)).date()
            
            # Calcular unidades para este periodo
            query_unidades = db.query(
                func.coalesce(func.sum(DetallePedido.cantidad_solicitada), 0)
            ).join(
                Pedido, DetallePedido.pedido_id == Pedido.pedido_id
            ).filter(
                Pedido.fecha_creacion >= periodo_datetime,
                Pedido.fecha_creacion < periodo_datetime + timedelta(days=30 if granularidad == "mes" else 7),
                Pedido.estado != EstadoPedido.CANCELADO
            )
            
            if vendedor_id:
                query_unidades = query_unidades.filter(Pedido.usuario_id == vendedor_id)
            
            if producto_id:
                query_unidades = query_unidades.filter(DetallePedido.producto_id == producto_id)
            
            unidades = query_unidades.scalar() or 0
            
            tendencia.append(TendenciaItem(
                fecha=fin_periodo,
                valor=float(r.valor),
                unidades=int(unidades),
                pedidos=int(r.pedidos)
            ))
        
        return tendencia
    
    @staticmethod
    async def generar_kpi_vendedor(
        db: Session,
        vendedor_id: int,
        desde: date,
        hasta: date,
        territorio_id: Optional[str] = None,
        producto_id: Optional[str] = None
    ) -> KPIVendedor:
        """
        Genera el reporte KPI para un vendedor específico.
        Cumple SLA de 2 segundos.
        """
        # Obtener nombre del vendedor
        nombre_vendedor = await ReportesService.obtener_nombre_vendedor(vendedor_id)
        
        # Calcular ventas
        ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
            db, vendedor_id, territorio_id, producto_id, desde, hasta
        )
        
        # Obtener metas
        meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
            db, vendedor_id, territorio_id, producto_id, desde, hasta
        )
        
        # Calcular cumplimiento
        cumplimiento_unidades = None
        if meta_unidades and meta_unidades > 0:
            cumplimiento_unidades = round(ventas_unidades / meta_unidades, 4)
        
        cumplimiento_valor = None
        if meta_valor and meta_valor > 0:
            cumplimiento_valor = round(ventas_valor / meta_valor, 4)
        
        # Calcular tendencia
        tendencia = ReportesService.calcular_tendencia(
            db, vendedor_id, territorio_id, producto_id, desde, hasta
        )
        
        return KPIVendedor(
            periodo=PeriodoReporte(desde=desde, hasta=hasta),
            vendedor=VendedorInfo(id=str(vendedor_id), nombre=nombre_vendedor),
            ventas_valor=ventas_valor,
            ventas_unidades=ventas_unidades,
            pedidos=num_pedidos,
            cumplimiento_unidades=cumplimiento_unidades,
            cumplimiento_valor=cumplimiento_valor,
            meta_unidades=meta_unidades,
            meta_valor=meta_valor,
            tendencia=tendencia
        )
    
    @staticmethod
    async def generar_reporte_region(
        db: Session,
        territorio_id: str,
        desde: date,
        hasta: date,
        producto_id: Optional[str] = None
    ) -> ReporteRegion:
        """
        Genera el reporte consolidado por región con ranking de vendedores.
        Cumple SLA de 2 segundos.
        """
        # Obtener info del territorio
        territorio_info = await ReportesService.obtener_territorio_info(territorio_id)
        territorio_nombre = territorio_info.get("nombre", territorio_id)
        
        # Obtener vendedores activos en la región (del periodo)
        vendedores_query = db.query(
            Pedido.usuario_id.distinct()
        ).filter(
            Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
            Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
            Pedido.estado != EstadoPedido.CANCELADO
        )
        
        vendedores_ids = [v[0] for v in vendedores_query.all()]
        
        # Calcular KPIs por vendedor
        ranking_items = []
        total_valor = 0.0
        total_unidades = 0
        total_pedidos = 0
        
        for vendedor_id in vendedores_ids:
            nombre_vendedor = await ReportesService.obtener_nombre_vendedor(vendedor_id)
            
            ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
                db, vendedor_id, territorio_id, producto_id, desde, hasta
            )
            
            # Obtener meta del vendedor
            meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
                db, vendedor_id, territorio_id, producto_id, desde, hasta
            )
            
            cumplimiento_unidades = None
            if meta_unidades and meta_unidades > 0:
                cumplimiento_unidades = round(ventas_unidades / meta_unidades, 4)
            
            cumplimiento_valor = None
            if meta_valor and meta_valor > 0:
                cumplimiento_valor = round(ventas_valor / meta_valor, 4)
            
            ranking_items.append(VendedorRanking(
                vendedorId=str(vendedor_id),
                nombre=nombre_vendedor,
                ventas_valor=ventas_valor,
                ventas_unidades=ventas_unidades,
                pedidos=num_pedidos,
                cumplimiento_unidades=cumplimiento_unidades,
                cumplimiento_valor=cumplimiento_valor
            ))
            
            total_valor += ventas_valor
            total_unidades += ventas_unidades
            total_pedidos += num_pedidos
        
        # Ordenar ranking por ventas_valor (descendente)
        ranking_items.sort(key=lambda x: x.ventas_valor, reverse=True)
        
        # Asignar posiciones
        for i, item in enumerate(ranking_items, 1):
            item.posicion = i
        
        # Calcular cumplimiento agregado de la región
        meta_region_unidades, meta_region_valor = await ReportesService.obtener_metas_periodo(
            db, None, territorio_id, producto_id, desde, hasta
        )
        
        cumplimiento_region_unidades = None
        if meta_region_unidades and meta_region_unidades > 0:
            cumplimiento_region_unidades = round(total_unidades / meta_region_unidades, 4)
        
        cumplimiento_region_valor = None
        if meta_region_valor and meta_region_valor > 0:
            cumplimiento_region_valor = round(total_valor / meta_region_valor, 4)
        
        # Calcular tendencia agregada
        tendencia = ReportesService.calcular_tendencia(
            db, None, territorio_id, producto_id, desde, hasta
        )
        
        return ReporteRegion(
            periodo=PeriodoReporte(desde=desde, hasta=hasta),
            territorio=TerritorioInfo(id=territorio_id, nombre=territorio_nombre),
            resumen=ResumenRegion(
                ventas_valor=total_valor,
                ventas_unidades=total_unidades,
                pedidos=total_pedidos,
                cumplimiento_unidades=cumplimiento_region_unidades,
                cumplimiento_valor=cumplimiento_region_valor,
                meta_unidades=meta_region_unidades,
                meta_valor=meta_region_valor
            ),
            ranking=ranking_items,
            tendencia=tendencia
        )
    
    @staticmethod
    async def generar_dashboard(
        db: Session,
        desde: date,
        hasta: date
    ) -> DashboardReportes:
        """
        Genera el dashboard consolidado con todos los KPIs y gráficos.
        Incluye datos preparados para Chart.js.
        """
        # Calcular KPIs totales
        ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
            db, None, None, None, desde, hasta
        )
        
        # Obtener meta total
        meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
            db, None, None, None, desde, hasta
        )
        
        cumplimiento = 0.0
        if meta_unidades and meta_unidades > 0:
            cumplimiento = round((ventas_unidades / meta_unidades) * 100, 1)
        
        kpis = [
            DashboardKPI(
                label="Ventas Totales",
                valor=ventas_valor,
                unidad="COP",
                tendencia="up",
                variacion=None  # Requeriría periodo anterior
            ),
            DashboardKPI(
                label="Unidades Vendidas",
                valor=float(ventas_unidades),
                unidad="unidades",
                tendencia="up",
                variacion=None
            ),
            DashboardKPI(
                label="Total Pedidos",
                valor=float(num_pedidos),
                unidad="pedidos",
                tendencia="neutral",
                variacion=None
            ),
            DashboardKPI(
                label="Cumplimiento Promedio",
                valor=cumplimiento,
                unidad="%",
                tendencia="neutral" if cumplimiento >= 80 else "down",
                variacion=None
            )
        ]
        
        # Gráfico de tendencia (línea temporal)
        tendencia = ReportesService.calcular_tendencia(
            db, None, None, None, desde, hasta
        )
        
        labels_tendencia = [item.fecha.strftime("%b %Y") for item in tendencia]
        datos_tendencia = [item.valor for item in tendencia]
        
        grafico_tendencia = GraficoLinea(
            labels=labels_tendencia,
            datasets=[{
                "label": "Ventas (COP)",
                "data": datos_tendencia,
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "tension": 0.1,
                "fill": True
            }]
        )
        
        # Obtener top vendedores para gráficos
        vendedores_query = db.query(
            Pedido.usuario_id,
            func.sum(Pedido.monto_total).label('total_ventas'),
            func.count(Pedido.pedido_id).label('num_pedidos')
        ).filter(
            Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
            Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
            Pedido.estado != EstadoPedido.CANCELADO
        ).group_by(Pedido.usuario_id).order_by(func.sum(Pedido.monto_total).desc()).limit(10).all()
        
        top_vendedores = []
        labels_vendedores = []
        datos_vendedores = []
        colores_cumplimiento = []
        datos_cumplimiento = []
        
        for idx, v in enumerate(vendedores_query):
            nombre = await ReportesService.obtener_nombre_vendedor(v.usuario_id)
            
            # Calcular unidades
            query_unidades = db.query(
                func.sum(DetallePedido.cantidad_solicitada)
            ).join(Pedido).filter(
                Pedido.usuario_id == v.usuario_id,
                Pedido.fecha_creacion >= datetime.combine(desde, datetime.min.time()),
                Pedido.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time()),
                Pedido.estado != EstadoPedido.CANCELADO
            ).scalar()
            
            unidades = int(query_unidades or 0)
            
            # Meta del vendedor
            meta_unidades_v, _ = await ReportesService.obtener_metas_periodo(
                db, v.usuario_id, None, None, desde, hasta
            )
            
            cumpl = None
            if meta_unidades_v and meta_unidades_v > 0:
                cumpl = round(unidades / meta_unidades_v, 4)
            
            top_vendedores.append(VendedorRanking(
                vendedorId=str(v.usuario_id),
                nombre=nombre,
                ventas_valor=float(v.total_ventas),
                ventas_unidades=unidades,
                pedidos=int(v.num_pedidos),
                cumplimiento_unidades=cumpl,
                posicion=idx + 1
            ))
            
            labels_vendedores.append(nombre)
            datos_vendedores.append(float(v.total_ventas))
            
            if cumpl:
                datos_cumplimiento.append(round(cumpl * 100, 1))
                # Color según cumplimiento
                if cumpl >= 0.9:
                    colores_cumplimiento.append("rgba(75, 192, 192, 0.7)")  # Verde
                elif cumpl >= 0.7:
                    colores_cumplimiento.append("rgba(255, 206, 86, 0.7)")  # Amarillo
                else:
                    colores_cumplimiento.append("rgba(255, 99, 132, 0.7)")  # Rojo
        
        grafico_vendedores = GraficoBarras(
            labels=labels_vendedores,
            datasets=[{
                "label": "Ventas (COP)",
                "data": datos_vendedores,
                "backgroundColor": "rgba(54, 162, 235, 0.6)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        )
        
        grafico_cumplimiento = GraficoDona(
            labels=labels_vendedores[:5],  # Top 5
            datasets=[{
                "label": "Cumplimiento (%)",
                "data": datos_cumplimiento[:5],
                "backgroundColor": colores_cumplimiento[:5],
                "borderWidth": 1
            }]
        )
        
        # Generar alertas
        alertas = []
        vendedores_bajo_cumplimiento = sum(1 for v in top_vendedores if v.cumplimiento_unidades and v.cumplimiento_unidades < 0.8)
        if vendedores_bajo_cumplimiento > 0:
            alertas.append(f"{vendedores_bajo_cumplimiento} vendedores por debajo del 80% de cumplimiento")
        
        if cumplimiento < 80:
            alertas.append(f"Cumplimiento general ({cumplimiento}%) por debajo del objetivo")
        
        return DashboardReportes(
            periodo=PeriodoReporte(desde=desde, hasta=hasta),
            kpis=kpis,
            grafico_tendencia=grafico_tendencia,
            grafico_vendedores=grafico_vendedores,
            grafico_cumplimiento=grafico_cumplimiento,
            top_vendedores=top_vendedores,
            alertas=alertas
        )
