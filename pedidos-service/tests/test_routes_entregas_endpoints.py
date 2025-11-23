"""
Tests para endpoints de entregas (app/routes/entregas.py)
Cubre listar_entregas y tracking_entrega
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.models.entrega import Entrega, EventoEntrega, EstadoEntrega


class TestListarEntregasEndpoint:
    """Tests para GET /api/v1/entregas/{nit}"""
    
    def test_listar_entregas_sin_entregas(self, client, db_session):
        """Test listar entregas cuando no hay ninguna"""
        nit = "123456789"
        
        response = client.get(f"/api/v1/entregas/{nit}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["entregas"]) == 0
    
    def test_listar_entregas_con_entregas(self, client, db_session):
        """Test listar entregas existentes"""
        nit = "123456789"
        pedido_id = str(uuid4())
        
        entrega1 = Entrega(
            pedido_id=pedido_id,
            nit=nit,
            estado_entrega=EstadoEntrega.PROGRAMADA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        entrega2 = Entrega(
            pedido_id=str(uuid4()),
            nit=nit,
            estado_entrega=EstadoEntrega.EN_RUTA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        db_session.add_all([entrega1, entrega2])
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{nit}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["entregas"]) == 2
    
    def test_listar_entregas_filtro_por_estado(self, client, db_session):
        """Test listar entregas filtrando por estado"""
        nit = "123456789"
        
        entrega1 = Entrega(
            pedido_id=str(uuid4()),
            nit=nit,
            estado_entrega=EstadoEntrega.PROGRAMADA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        entrega2 = Entrega(
            pedido_id=str(uuid4()),
            nit=nit,
            estado_entrega=EstadoEntrega.ENTREGADA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        db_session.add_all([entrega1, entrega2])
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{nit}?estado=programada")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entregas"][0]["estado_entrega"] == "programada"
    
    def test_listar_entregas_estado_invalido(self, client):
        """Test listar entregas con estado inválido"""
        nit = "123456789"
        
        response = client.get(f"/api/v1/entregas/{nit}?estado=estado_invalido")
        
        assert response.status_code == 400
        assert "Estado inválido" in response.json()["detail"]
    
    def test_listar_entregas_con_paginacion(self, client, db_session):
        """Test listar entregas con paginación"""
        nit = "123456789"
        
        # Crear 5 entregas
        for i in range(5):
            entrega = Entrega(
                pedido_id=str(uuid4()),
                nit=nit,
                estado_entrega=EstadoEntrega.PROGRAMADA,
                fecha_hora_programada=datetime.now(timezone.utc)
            )
            db_session.add(entrega)
        db_session.commit()
        
        # Primera página (2 por página)
        response = client.get(f"/api/v1/entregas/{nit}?pagina=1&por_pagina=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["entregas"]) == 2
        assert data["pagina"] == 1
        assert data["por_pagina"] == 2
    
    def test_listar_entregas_con_datos_vehiculo(self, client, db_session):
        """Test que incluye datos de vehículo y conductor"""
        nit = "123456789"
        
        entrega = Entrega(
            pedido_id=str(uuid4()),
            nit=nit,
            estado_entrega=EstadoEntrega.EN_RUTA,
            fecha_hora_programada=datetime.now(timezone.utc),
            vehiculo_id=str(uuid4()),
            conductor_id=1,
            placa_vehiculo="ABC123"
        )
        
        db_session.add(entrega)
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{nit}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["entregas"]) == 1
        # Verificar que los datos están presentes
        entrega_data = data["entregas"][0]
        assert entrega_data["placa_vehiculo"] == "ABC123"
        assert entrega_data["conductor_id"] == "1"  # Se devuelve como string
        assert entrega_data["estado_entrega"] == "en_ruta"


class TestTrackingEntregaEndpoint:
    """Tests para GET /api/v1/entregas/{entrega_id}/tracking"""
    
    def test_tracking_entrega_no_encontrada(self, client):
        """Test tracking de entrega que no existe"""
        entrega_id = str(uuid4())
        
        response = client.get(f"/api/v1/entregas/{entrega_id}/tracking")
        
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()
    
    def test_tracking_entrega_sin_eventos(self, client, db_session):
        """Test tracking de entrega sin eventos"""
        entrega_id = str(uuid4())
        
        entrega = Entrega(
            entrega_id=entrega_id,
            pedido_id=str(uuid4()),
            nit="123456789",
            estado_entrega=EstadoEntrega.PROGRAMADA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        db_session.add(entrega)
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{entrega_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        assert data["entrega_id"] == entrega_id
        assert data["estado_entrega"] == "programada"
        assert data["ultima_posicion"] is None
        assert len(data["eventos"]) == 0
    
    def test_tracking_entrega_con_eventos(self, client, db_session):
        """Test tracking de entrega con eventos"""
        entrega_id = str(uuid4())
        
        entrega = Entrega(
            entrega_id=entrega_id,
            pedido_id=str(uuid4()),
            nit="123456789",
            estado_entrega=EstadoEntrega.EN_RUTA,
            fecha_hora_programada=datetime.now(timezone.utc),
            fecha_hora_estimada_llegada=datetime.now(timezone.utc)
        )
        
        evento1 = EventoEntrega(
            entrega_id=entrega_id,
            timestamp=datetime.now(timezone.utc),
            latitud=4.6097,
            longitud=-74.0817,
            tipo_evento="inicio_ruta",
            descripcion="Inicio de ruta"
        )
        
        evento2 = EventoEntrega(
            entrega_id=entrega_id,
            timestamp=datetime.now(timezone.utc),
            latitud=4.6150,
            longitud=-74.0850,
            tipo_evento="en_transito",
            descripcion="En tránsito"
        )
        
        db_session.add_all([entrega, evento1, evento2])
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{entrega_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        assert data["entrega_id"] == entrega_id
        assert data["estado_entrega"] == "en_ruta"
        assert data["ultima_posicion"] is not None
        assert data["ultima_posicion"]["latitud"] is not None
        assert data["ultima_posicion"]["longitud"] is not None
        assert len(data["eventos"]) == 2
        assert data["eta"] is not None
    
    def test_tracking_entrega_limite_eventos(self, client, db_session):
        """Test que tracking retorna máximo 20 eventos"""
        entrega_id = str(uuid4())
        
        entrega = Entrega(
            entrega_id=entrega_id,
            pedido_id=str(uuid4()),
            nit="123456789",
            estado_entrega=EstadoEntrega.EN_RUTA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        db_session.add(entrega)
        db_session.flush()
        
        # Crear 25 eventos
        for i in range(25):
            evento = EventoEntrega(
                entrega_id=entrega_id,
                timestamp=datetime.now(timezone.utc),
                latitud=4.6097 + (i * 0.001),
                longitud=-74.0817 + (i * 0.001),
                tipo_evento="checkpoint",
                descripcion=f"Checkpoint {i}"
            )
            db_session.add(evento)
        
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{entrega_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        # Debe retornar máximo 20 eventos (los más recientes)
        assert len(data["eventos"]) == 20
    
    def test_tracking_entrega_ultima_posicion(self, client, db_session):
        """Test que última posición es el evento más reciente"""
        entrega_id = str(uuid4())
        
        entrega = Entrega(
            entrega_id=entrega_id,
            pedido_id=str(uuid4()),
            nit="123456789",
            estado_entrega=EstadoEntrega.EN_RUTA,
            fecha_hora_programada=datetime.now(timezone.utc)
        )
        
        # Evento antiguo
        evento1 = EventoEntrega(
            entrega_id=entrega_id,
            timestamp=datetime(2025, 11, 23, 10, 0, 0, tzinfo=timezone.utc),
            latitud=4.6097,
            longitud=-74.0817,
            tipo_evento="inicio",
            descripcion="Inicio"
        )
        
        # Evento más reciente
        evento2 = EventoEntrega(
            entrega_id=entrega_id,
            timestamp=datetime(2025, 11, 23, 12, 0, 0, tzinfo=timezone.utc),
            latitud=4.7000,
            longitud=-74.1000,
            tipo_evento="actual",
            descripcion="Posición actual"
        )
        
        db_session.add_all([entrega, evento1, evento2])
        db_session.commit()
        
        response = client.get(f"/api/v1/entregas/{entrega_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        # Última posición debe ser la del evento más reciente
        assert data["ultima_posicion"]["latitud"] == 4.7000
        assert data["ultima_posicion"]["longitud"] == -74.1000
