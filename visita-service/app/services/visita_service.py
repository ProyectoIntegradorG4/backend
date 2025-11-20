from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.visita import (
    Visita, RutaVisita, VisitaResponse, VisitaEnRuta, RutaVisitaResponse,
    VisitaListResponse, EstadoVisita, OrigenRuta, VisitaCreate, VisitaUpdate,
    ClienteDisponibleZona, ClientesDisponiblesZonaResponse
)
from typing import Optional, List, Tuple
from fastapi import HTTPException
from datetime import date, time, datetime, timezone, timedelta
import logging
import httpx
import os
from decimal import Decimal

logger = logging.getLogger("uvicorn")

# URL del servicio de clientes
CLIENTE_SERVICE_URL = os.getenv(
    "CLIENTE_SERVICE_URL",
    "http://cliente-service:8013"
)


class VisitaService:
    """
    Servicio de lógica de negocio para gestión de visitas y rutas
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._http_client = None

    async def get_http_client(self):
        """Obtener cliente HTTP reutilizable"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def get_cliente_info(self, cliente_id: int) -> Optional[dict]:
        """
        Obtener información de un cliente desde cliente-service
        """
        try:
            client = await self.get_http_client()
            response = await client.get(f"{CLIENTE_SERVICE_URL}/api/v1/clientes/{cliente_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Error al obtener cliente {cliente_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al conectar con cliente-service: {str(e)}")
            return None

    async def verificar_gerente_tiene_cliente(self, gerente_id: int, cliente_id: int) -> bool:
        """
        Verificar que el gerente tiene acceso al cliente mediante cliente-service
        """
        try:
            client = await self.get_http_client()
            response = await client.get(
                f"{CLIENTE_SERVICE_URL}/api/v1/clientes/mis-cliente-ids",
                params={"gerente_id": gerente_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                cliente_ids = data.get("cliente_ids", [])
                return cliente_id in cliente_ids
            else:
                logger.warning(f"No se pudo verificar acceso del gerente {gerente_id} al cliente {cliente_id}")
                return False
        except Exception as e:
            logger.error(f"Error al verificar acceso de gerente: {str(e)}")
            return False

    async def create_visita(self, visita_data: VisitaCreate) -> VisitaResponse:
        """
        Crear una nueva visita programada
        """
        try:
            # Verificar que el gerente tiene acceso al cliente
            tiene_acceso = await self.verificar_gerente_tiene_cliente(
                visita_data.gerente_id,
                visita_data.cliente_id
            )
            
            if not tiene_acceso:
                raise HTTPException(
                    status_code=403,
                    detail=f"El gerente {visita_data.gerente_id} no tiene acceso al cliente {visita_data.cliente_id}"
                )

            # Obtener información del cliente (lat/long, nombre, dirección)
            cliente_info = await self.get_cliente_info(visita_data.cliente_id)
            
            if not cliente_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"Cliente {visita_data.cliente_id} no encontrado"
                )

            # Calcular hora_fin_sugerida
            hora_fin = None
            if visita_data.hora_inicio_sugerida:
                inicio_dt = datetime.combine(date.today(), visita_data.hora_inicio_sugerida)
                fin_dt = inicio_dt + timedelta(minutes=visita_data.duracion_estimada_minutos)
                hora_fin = fin_dt.time()

            # Crear visita
            visita = Visita(
                gerente_id=visita_data.gerente_id,
                cliente_id=visita_data.cliente_id,
                fecha_visita=visita_data.fecha_visita,
                hora_inicio_sugerida=visita_data.hora_inicio_sugerida,
                hora_fin_sugerida=hora_fin,
                duracion_estimada_minutos=visita_data.duracion_estimada_minutos,
                prioridad=visita_data.prioridad,
                observaciones=visita_data.observaciones,
                estado=EstadoVisita.PROGRAMADA,
                latitud=cliente_info.get("latitud"),
                longitud=cliente_info.get("longitud"),
                nombre_cliente=cliente_info.get("nombre_comercial"),
                direccion_cliente=cliente_info.get("direccion")
            )

            self.db.add(visita)
            self.db.commit()
            self.db.refresh(visita)

            logger.info(f"✅ Visita {visita.visita_id} creada para gerente {visita_data.gerente_id}")
            return VisitaResponse.model_validate(visita)

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear visita: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al crear visita")

    def get_visitas_by_gerente_fecha(
        self,
        gerente_id: int,
        fecha: date,
        estado: Optional[EstadoVisita] = None
    ) -> List[Visita]:
        """
        Obtener visitas de un gerente para una fecha específica
        """
        try:
            query = self.db.query(Visita).filter(
                Visita.gerente_id == gerente_id,
                Visita.fecha_visita == fecha
            )

            if estado:
                query = query.filter(Visita.estado == estado)
            else:
                # Por defecto, no incluir canceladas
                query = query.filter(Visita.estado != EstadoVisita.CANCELADA)

            return query.order_by(Visita.orden_en_ruta.asc().nullslast(), Visita.hora_inicio_sugerida.asc()).all()

        except Exception as e:
            logger.error(f"Error al obtener visitas: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener visitas")

    def get_visita_by_id(self, visita_id: int, gerente_id: int) -> Optional[Visita]:
        """
        Obtener visita por ID, validando que pertenece al gerente
        """
        try:
            visita = self.db.query(Visita).filter(
                Visita.visita_id == visita_id,
                Visita.gerente_id == gerente_id
            ).first()

            return visita

        except Exception as e:
            logger.error(f"Error al obtener visita {visita_id}: {str(e)}")
            return None

    def update_visita(
        self,
        visita_id: int,
        gerente_id: int,
        visita_update: VisitaUpdate
    ) -> VisitaResponse:
        """
        Actualizar visita existente
        """
        try:
            visita = self.get_visita_by_id(visita_id, gerente_id)
            
            if not visita:
                raise HTTPException(
                    status_code=404,
                    detail=f"Visita {visita_id} no encontrada o no pertenece al gerente {gerente_id}"
                )

            # Actualizar campos proporcionados
            update_data = visita_update.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(visita, field, value)

            # Recalcular hora_fin si se actualiza hora_inicio o duración
            if visita_update.hora_inicio_sugerida or visita_update.duracion_estimada_minutos:
                if visita.hora_inicio_sugerida:
                    inicio_dt = datetime.combine(date.today(), visita.hora_inicio_sugerida)
                    fin_dt = inicio_dt + timedelta(minutes=visita.duracion_estimada_minutos)
                    visita.hora_fin_sugerida = fin_dt.time()

            self.db.commit()
            self.db.refresh(visita)

            logger.info(f"✅ Visita {visita_id} actualizada")
            return VisitaResponse.model_validate(visita)

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar visita {visita_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al actualizar visita")

    def delete_visita(self, visita_id: int, gerente_id: int) -> bool:
        """
        Cancelar visita (soft delete)
        """
        try:
            visita = self.get_visita_by_id(visita_id, gerente_id)
            
            if not visita:
                raise HTTPException(
                    status_code=404,
                    detail=f"Visita {visita_id} no encontrada o no pertenece al gerente {gerente_id}"
                )

            visita.estado = EstadoVisita.CANCELADA
            self.db.commit()

            logger.info(f"✅ Visita {visita_id} cancelada")
            return True

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al cancelar visita {visita_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al cancelar visita")

    def get_ruta_by_gerente_fecha(
        self,
        gerente_id: int,
        fecha: date
    ) -> Optional[RutaVisita]:
        """
        Obtener ruta activa para un gerente en una fecha específica
        """
        try:
            ruta = self.db.query(RutaVisita).filter(
                RutaVisita.gerente_id == gerente_id,
                RutaVisita.fecha_ruta == fecha,
                RutaVisita.activa == True
            ).first()

            return ruta

        except Exception as e:
            logger.error(f"Error al obtener ruta: {str(e)}")
            return None

    def crear_ruta_vacia(self, gerente_id: int, fecha: date) -> RutaVisita:
        """
        Crear una ruta vacía para una fecha
        """
        try:
            # Desactivar rutas anteriores para esta fecha
            self.db.query(RutaVisita).filter(
                RutaVisita.gerente_id == gerente_id,
                RutaVisita.fecha_ruta == fecha,
                RutaVisita.activa == True
            ).update({"activa": False})

            # Crear nueva ruta
            ruta = RutaVisita(
                gerente_id=gerente_id,
                fecha_ruta=fecha,
                version_ruta=1,
                origen_ruta=OrigenRuta.PLANIFICADA,
                activa=True
            )

            self.db.add(ruta)
            self.db.commit()
            self.db.refresh(ruta)

            return ruta

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear ruta vacía: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al crear ruta")

    async def get_clientes_disponibles_zona(
        self,
        gerente_id: int,
        fecha: date,
        lat: float,
        lng: float,
        radio_km: float = 20.0
    ) -> ClientesDisponiblesZonaResponse:
        """
        Obtener clientes asignados al gerente dentro de un radio específico
        """
        try:
            # Obtener clientes del gerente desde cliente-service
            client = await self.get_http_client()
            response = await client.get(
                f"{CLIENTE_SERVICE_URL}/api/v1/clientes/mis-clientes",
                params={"gerente_id": gerente_id, "limit": 100}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error al obtener clientes del gerente"
                )

            data = response.json()
            clientes = data.get("clientes", [])

            # Obtener visitas ya programadas para la fecha
            visitas_programadas = self.db.query(Visita.cliente_id).filter(
                Visita.gerente_id == gerente_id,
                Visita.fecha_visita == fecha,
                Visita.estado != EstadoVisita.CANCELADA
            ).all()
            
            clientes_con_visita = {v[0] for v in visitas_programadas}

            # Filtrar clientes por distancia y preparar respuesta
            from app.services.ruta_optimizer import calcular_distancia_haversine
            
            clientes_en_zona = []
            for cliente in clientes:
                if cliente.get("latitud") and cliente.get("longitud"):
                    distancia = calcular_distancia_haversine(
                        lat, lng,
                        float(cliente["latitud"]), float(cliente["longitud"])
                    )
                    
                    if distancia <= radio_km:
                        clientes_en_zona.append(ClienteDisponibleZona(
                            cliente_id=cliente["cliente_id"],
                            nombre_comercial=cliente["nombre_comercial"],
                            direccion=cliente.get("direccion"),
                            latitud=cliente.get("latitud"),
                            longitud=cliente.get("longitud"),
                            distancia_km=round(distancia, 2),
                            tiene_visita_programada=cliente["cliente_id"] in clientes_con_visita
                        ))

            # Ordenar por distancia
            clientes_en_zona.sort(key=lambda c: c.distancia_km or 999)

            return ClientesDisponiblesZonaResponse(
                fecha=fecha,
                gerente_id=gerente_id,
                punto_referencia={"lat": lat, "lng": lng},
                radio_km=radio_km,
                clientes=clientes_en_zona,
                total=len(clientes_en_zona)
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener clientes en zona: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener clientes en zona")

