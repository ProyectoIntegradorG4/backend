from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import time

# ============= Request Schemas =============

class UbicacionRequest(BaseModel):
    """Ubicación con latitud y longitud"""
    lat: float = Field(..., ge=-90, le=90, description="Latitud")
    lon: float = Field(..., ge=-180, le=180, description="Longitud")

class VehiculoRequest(BaseModel):
    """Datos de vehículo para generar ruta"""
    id: str = Field(..., description="ID del vehículo")
    capacidad_volumen: float = Field(..., gt=0, description="Capacidad en m³")
    capacidad_peso: float = Field(..., gt=0, description="Capacidad en kg")
    cadena_frio: bool = Field(default=False, description="¿Tiene cadena de frío?")
    depot: UbicacionRequest = Field(..., description="Ubicación del depósito")
    duracion_maxima_minutos: Optional[int] = Field(None, gt=0, description="Duración máxima de ruta en minutos")

class PedidoRutaRequest(BaseModel):
    """Datos de pedido para generar ruta"""
    id: str = Field(..., description="ID del pedido")
    lat: float = Field(..., ge=-90, le=90, description="Latitud del cliente")
    lon: float = Field(..., ge=-180, le=180, description="Longitud del cliente")
    ventana_inicio: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Hora inicio ventana (HH:MM)")
    ventana_fin: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Hora fin ventana (HH:MM)")
    tiempo_servicio_minutos: int = Field(default=10, gt=0, description="Tiempo de servicio en minutos")
    requiere_frio: bool = Field(default=False, description="¿Requiere cadena de frío?")
    volumen: float = Field(..., gt=0, description="Volumen en m³")
    peso: float = Field(..., gt=0, description="Peso en kg")
    
    @validator('ventana_fin')
    def ventana_fin_debe_ser_posterior(cls, v, values):
        """Validar que ventana_fin sea posterior a ventana_inicio"""
        if 'ventana_inicio' in values and v <= values['ventana_inicio']:
            raise ValueError('ventana_fin debe ser posterior a ventana_inicio')
        return v

class LimitesRequest(BaseModel):
    """Límites y configuraciones adicionales"""
    duracion_maxima_minutos: Optional[int] = Field(None, gt=0, description="Duración máxima por ruta")
    considerar_trafico: bool = Field(default=False, description="Considerar tráfico (si disponible)")

class GenerarRutasRequest(BaseModel):
    """Request para generar rutas de entrega"""
    objetivo: str = Field(..., pattern=r"^(min_distancia|min_tiempo)$", description="Objetivo de optimización")
    vehiculos: List[VehiculoRequest] = Field(..., min_items=1, description="Lista de vehículos disponibles")
    pedidos: List[PedidoRutaRequest] = Field(..., min_items=1, description="Lista de pedidos a rutear")
    limites: Optional[LimitesRequest] = Field(default_factory=LimitesRequest, description="Límites y configuraciones")
    
    @validator('pedidos')
    def validar_cantidad_pedidos(cls, v):
        """Validar que no exceda el límite del MVP"""
        if len(v) > 100:
            raise ValueError('El MVP soporta máximo 100 pedidos')
        return v
    
    @validator('vehiculos')
    def validar_cantidad_vehiculos(cls, v):
        """Validar que no exceda el límite del MVP"""
        if len(v) > 10:
            raise ValueError('El MVP soporta máximo 10 vehículos')
        return v

class RecalcularRutaRequest(BaseModel):
    """Request para recalcular una ruta tras ajuste manual"""
    ruta_id: str = Field(..., description="ID de la ruta a recalcular")
    nueva_secuencia: List[str] = Field(..., min_items=1, description="Nueva secuencia de pedido_ids")

# ============= Response Schemas =============

class UsoCapacidadResponse(BaseModel):
    """Información de uso de capacidad"""
    volumen: float = Field(..., description="Volumen utilizado en m³")
    peso: float = Field(..., description="Peso utilizado en kg")
    porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje de capacidad utilizada")

class ParadaRutaResponse(BaseModel):
    """Detalle de una parada en la ruta"""
    pedido_id: str
    orden: int
    eta: str  # "HH:MM"
    latitud: float
    longitud: float
    ventana_inicio: Optional[str] = None
    ventana_fin: Optional[str] = None
    cumple_ventana: bool = True
    tiempo_servicio_minutos: int = 10

class RutaResponse(BaseModel):
    """Respuesta con detalle de una ruta generada"""
    vehiculo_id: str
    orden: List[str] = Field(..., description="Secuencia de pedido_ids (incluye DEPOT si aplica)")
    paradas: List[ParadaRutaResponse] = Field(..., description="Detalle de cada parada")
    distancia_km: float
    duracion_minutos: int
    uso_capacidad: UsoCapacidadResponse

class GenerarRutasResponse(BaseModel):
    """Respuesta al generar rutas"""
    ruta_id: Optional[str] = Field(None, description="ID de la ruta generada (para recálculos posteriores)")
    rutas: List[RutaResponse]
    warnings: List[str] = Field(default_factory=list, description="Advertencias (no bloqueantes)")
    tiempo_calculo_ms: Optional[int] = Field(None, description="Tiempo de cálculo en milisegundos")

class RecalcularRutaResponse(BaseModel):
    """Respuesta al recalcular una ruta"""
    ruta: RutaResponse
    warnings: List[str] = Field(default_factory=list)
    tiempo_calculo_ms: Optional[int] = None

# ============= Schemas para Vehículos =============

class CrearVehiculoRequest(BaseModel):
    """Request para crear un vehículo"""
    vehiculo_id: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=255)
    capacidad_volumen: float = Field(..., gt=0)
    capacidad_peso: float = Field(..., gt=0)
    cadena_frio: bool = Field(default=False)
    depot_latitud: float = Field(..., ge=-90, le=90)
    depot_longitud: float = Field(..., ge=-180, le=180)
    depot_direccion: Optional[str] = Field(None, max_length=500)
    duracion_maxima_minutos: Optional[int] = Field(None, gt=0)

class VehiculoResponse(BaseModel):
    """Respuesta con datos de vehículo"""
    vehiculo_id: str
    nombre: str
    capacidad_volumen: float
    capacidad_peso: float
    cadena_frio: bool
    depot_latitud: float
    depot_longitud: float
    depot_direccion: Optional[str] = None
    duracion_maxima_minutos: Optional[int] = None
    activo: bool
    
    class Config:
        from_attributes = True

class ListarVehiculosResponse(BaseModel):
    """Respuesta al listar vehículos"""
    total: int
    vehiculos: List[VehiculoResponse]


# ==================== Recalcular Ruta ====================

class RecalcularRutaRequest(BaseModel):
    """Request para recalcular una ruta con nueva secuencia"""
    ruta_id: str = Field(..., description="ID de la ruta a recalcular")
    nueva_secuencia: List[str] = Field(
        ..., 
        description="Nueva secuencia de pedidos (IDs en orden)",
        min_length=1
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ruta_id": "550e8400-e29b-41d4-a716-446655440000",
                "nueva_secuencia": ["PED-456", "PED-123", "PED-789"]
            }
        }

class RecalcularRutaResponse(BaseModel):
    """Respuesta del endpoint de recálculo"""
    ruta: RutaResponse
    warnings: List[str] = []
    tiempo_calculo_ms: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "ruta": {
                    "vehiculo_id": "VEH-001",
                    "orden": ["DEPOT", "PED-456", "PED-123", "DEPOT"],
                    "paradas": [],
                    "distancia_km": 48.1,
                    "duracion_minutos": 190,
                    "uso_capacidad": {"volumen": 25.5, "peso": 450.0, "porcentaje": 75.5}
                },
                "warnings": [],
                "tiempo_calculo_ms": 450
            }
        }
