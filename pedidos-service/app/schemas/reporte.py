"""
Schemas para reportes de vendedores (HU-WEB-010)
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal


class PeriodoReporte(BaseModel):
    """Periodo del reporte"""
    desde: date
    hasta: date


class VendedorInfo(BaseModel):
    """Información básica del vendedor"""
    id: str = Field(..., description="ID del vendedor")
    nombre: str = Field(..., description="Nombre completo del vendedor")


class TerritorioInfo(BaseModel):
    """Información básica del territorio"""
    id: str = Field(..., description="ID del territorio")
    nombre: str = Field(..., description="Nombre del territorio")


class TendenciaItem(BaseModel):
    """Item de tendencia temporal (para gráficos)"""
    fecha: date = Field(..., description="Fecha del periodo (fin de semana/mes)")
    valor: float = Field(..., description="Ventas en valor")
    unidades: int = Field(..., description="Ventas en unidades")
    pedidos: int = Field(0, description="Número de pedidos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fecha": "2026-01-31",
                "valor": 4200000.0,
                "unidades": 220,
                "pedidos": 25
            }
        }


class KPIVendedor(BaseModel):
    """KPIs de un vendedor en un periodo"""
    periodo: PeriodoReporte
    vendedor: VendedorInfo
    ventas_valor: float = Field(..., description="Total de ventas en valor (COP)")
    ventas_unidades: int = Field(..., description="Total de unidades vendidas")
    pedidos: int = Field(..., description="Número total de pedidos")
    cumplimiento_unidades: Optional[float] = Field(None, description="% de cumplimiento vs meta en unidades (0-1)")
    cumplimiento_valor: Optional[float] = Field(None, description="% de cumplimiento vs meta en valor (0-1)")
    meta_unidades: Optional[int] = Field(None, description="Meta en unidades del periodo")
    meta_valor: Optional[float] = Field(None, description="Meta en valor del periodo")
    tendencia: List[TendenciaItem] = Field(default_factory=list, description="Evolución temporal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "periodo": {"desde": "2026-01-01", "hasta": "2026-03-31"},
                "vendedor": {"id": "1", "nombre": "Laura González"},
                "ventas_valor": 15000000.0,
                "ventas_unidades": 820,
                "pedidos": 96,
                "cumplimiento_unidades": 0.94,
                "cumplimiento_valor": None,
                "meta_unidades": 872,
                "meta_valor": None,
                "tendencia": [
                    {"fecha": "2026-01-31", "valor": 4200000, "unidades": 220, "pedidos": 28},
                    {"fecha": "2026-02-29", "valor": 5200000, "unidades": 300, "pedidos": 35},
                    {"fecha": "2026-03-31", "valor": 5600000, "unidades": 300, "pedidos": 33}
                ]
            }
        }


class VendedorRanking(BaseModel):
    """Item de ranking de vendedor"""
    vendedor_id: str = Field(..., alias="vendedorId")
    nombre: str
    ventas_valor: float
    ventas_unidades: int
    pedidos: int = Field(0, description="Número de pedidos")
    cumplimiento_unidades: Optional[float] = None
    cumplimiento_valor: Optional[float] = None
    posicion: Optional[int] = Field(None, description="Posición en el ranking (1-N)")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "vendedorId": "1",
                "nombre": "Laura González",
                "ventas_valor": 15000000.0,
                "ventas_unidades": 820,
                "pedidos": 96,
                "cumplimiento_unidades": 0.94,
                "cumplimiento_valor": None,
                "posicion": 1
            }
        }


class ResumenRegion(BaseModel):
    """Resumen consolidado de una región"""
    ventas_valor: float
    ventas_unidades: int
    pedidos: int
    cumplimiento_unidades: Optional[float] = None
    cumplimiento_valor: Optional[float] = None
    meta_unidades: Optional[int] = None
    meta_valor: Optional[float] = None


class ReporteRegion(BaseModel):
    """Reporte consolidado por región con ranking"""
    periodo: PeriodoReporte
    territorio: TerritorioInfo
    resumen: ResumenRegion
    ranking: List[VendedorRanking]
    tendencia: List[TendenciaItem] = Field(default_factory=list, description="Tendencia agregada de la región")
    
    class Config:
        json_schema_extra = {
            "example": {
                "periodo": {"desde": "2026-01-01", "hasta": "2026-03-31"},
                "territorio": {"id": "TERR-001", "nombre": "Bogotá Norte"},
                "resumen": {
                    "ventas_valor": 42000000.0,
                    "ventas_unidades": 2300,
                    "pedidos": 265,
                    "cumplimiento_unidades": 0.88,
                    "cumplimiento_valor": None,
                    "meta_unidades": 2614,
                    "meta_valor": None
                },
                "ranking": [
                    {
                        "vendedorId": "1",
                        "nombre": "Laura González",
                        "ventas_valor": 15000000.0,
                        "ventas_unidades": 820,
                        "pedidos": 96,
                        "cumplimiento_unidades": 0.94,
                        "posicion": 1
                    }
                ],
                "tendencia": []
            }
        }


class DashboardKPI(BaseModel):
    """KPI para dashboard general"""
    label: str = Field(..., description="Etiqueta del KPI")
    valor: float = Field(..., description="Valor numérico")
    unidad: str = Field(..., description="Unidad de medida (COP, unidades, %)")
    tendencia: Optional[str] = Field(None, description="up/down/neutral")
    variacion: Optional[float] = Field(None, description="% de variación vs periodo anterior")


class GraficoBarras(BaseModel):
    """Datos para gráfico de barras (Chart.js)"""
    labels: List[str] = Field(..., description="Etiquetas del eje X")
    datasets: List[Dict] = Field(..., description="Conjuntos de datos para Chart.js")
    
    class Config:
        json_schema_extra = {
            "example": {
                "labels": ["Ene", "Feb", "Mar"],
                "datasets": [{
                    "label": "Ventas",
                    "data": [4200000, 5200000, 5600000],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)"
                }]
            }
        }


class GraficoLinea(BaseModel):
    """Datos para gráfico de línea (Chart.js)"""
    labels: List[str]
    datasets: List[Dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
                "datasets": [{
                    "label": "Tendencia Ventas",
                    "data": [1200000, 1450000, 1680000, 1870000],
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }]
            }
        }


class GraficoDona(BaseModel):
    """Datos para gráfico de dona/pie (Chart.js)"""
    labels: List[str]
    datasets: List[Dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "labels": ["Laura González", "Carlos Ruiz", "María Pérez"],
                "datasets": [{
                    "data": [15000000, 14000000, 13000000],
                    "backgroundColor": [
                        "rgba(255, 99, 132, 0.5)",
                        "rgba(54, 162, 235, 0.5)",
                        "rgba(255, 206, 86, 0.5)"
                    ]
                }]
            }
        }


class DashboardReportes(BaseModel):
    """Dashboard consolidado con todos los reportes principales"""
    periodo: PeriodoReporte
    kpis: List[DashboardKPI] = Field(..., description="KPIs principales")
    grafico_tendencia: GraficoLinea = Field(..., description="Tendencia de ventas en el tiempo")
    grafico_vendedores: GraficoBarras = Field(..., description="Comparativo de vendedores")
    grafico_cumplimiento: GraficoDona = Field(..., description="Distribución de cumplimiento")
    top_vendedores: List[VendedorRanking] = Field(..., description="Top 10 vendedores")
    alertas: List[str] = Field(default_factory=list, description="Alertas o recomendaciones")
    
    class Config:
        json_schema_extra = {
            "example": {
                "periodo": {"desde": "2026-01-01", "hasta": "2026-03-31"},
                "kpis": [
                    {"label": "Ventas Totales", "valor": 42000000, "unidad": "COP", "tendencia": "up", "variacion": 12.5},
                    {"label": "Pedidos", "valor": 265, "unidad": "pedidos", "tendencia": "up", "variacion": 8.3},
                    {"label": "Cumplimiento Promedio", "valor": 88, "unidad": "%", "tendencia": "neutral", "variacion": -2.1}
                ],
                "grafico_tendencia": {
                    "labels": ["Ene", "Feb", "Mar"],
                    "datasets": []
                },
                "grafico_vendedores": {
                    "labels": [],
                    "datasets": []
                },
                "grafico_cumplimiento": {
                    "labels": [],
                    "datasets": []
                },
                "top_vendedores": [],
                "alertas": ["3 vendedores por debajo del 80% de cumplimiento"]
            }
        }
