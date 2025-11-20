"""
Seed de datos de prueba para visita-service
"""

from sqlalchemy.orm import Session
from app.models.visita import Visita, RutaVisita, EstadoVisita, PrioridadVisita, OrigenRuta
from datetime import date, time, datetime, timezone, timedelta
import logging

logger = logging.getLogger("uvicorn")


def run_seeds(db: Session):
    """
    Ejecutar seeds de datos de prueba
    """
    try:
        # Verificar si ya hay datos
        existing_visitas = db.query(Visita).count()
        
        if existing_visitas > 0:
            logger.info("⏭️ Ya existen visitas, saltando seed")
            return
        
        logger.info("🌱 Iniciando seed de datos de prueba para visita-service...")
        
        # Fecha de hoy y mañana para ejemplos
        hoy = date.today()
        manana = hoy + timedelta(days=1)
        
        # Visitas de ejemplo para Gerente ID 1 (Colombia)
        # Basadas en clientes seed de cliente-service
        
        visitas_seed = [
            # Visitas para HOY
            Visita(
                gerente_id=1,
                cliente_id=1,  # Hospital San José - Bogotá
                fecha_visita=hoy,
                hora_inicio_sugerida=time(9, 0),
                hora_fin_sugerida=time(10, 0),
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.ALTA,
                latitud=4.6533,  # Bogotá aprox
                longitud=-74.0836,
                nombre_cliente="Hospital San José",
                direccion_cliente="Calle 10 #20-30, Bogotá",
                observaciones="Primera visita del día - Cliente prioritario"
            ),
            Visita(
                gerente_id=1,
                cliente_id=2,  # Clínica Los Andes - Bogotá
                fecha_visita=hoy,
                hora_inicio_sugerida=time(11, 0),
                hora_fin_sugerida=time(12, 0),
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.MEDIA,
                latitud=4.6697,
                longitud=-74.0560,
                nombre_cliente="Clínica Los Andes",
                direccion_cliente="Carrera 15 #100-50, Bogotá",
                observaciones="Seguimiento mensual"
            ),
            Visita(
                gerente_id=1,
                cliente_id=3,  # IPS Salud Total - Medellín
                fecha_visita=hoy,
                hora_inicio_sugerida=time(14, 0),
                hora_fin_sugerida=time(15, 0),
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.BAJA,
                latitud=6.2442,  # Medellín aprox
                longitud=-75.5812,
                nombre_cliente="IPS Salud Total",
                direccion_cliente="Calle 50 #45-20, Medellín",
                observaciones="Visita de rutina"
            ),
            
            # Visitas para MAÑANA
            Visita(
                gerente_id=1,
                cliente_id=4,  # EPS Sanitas - Bogotá
                fecha_visita=manana,
                hora_inicio_sugerida=time(8, 30),
                hora_fin_sugerida=time(9, 30),
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.ALTA,
                latitud=4.6800,
                longitud=-74.0500,
                nombre_cliente="EPS Sanitas",
                direccion_cliente="Av. El Dorado #50-20, Bogotá",
                observaciones="Presentación de nuevos productos"
            ),
            Visita(
                gerente_id=1,
                cliente_id=5,  # Laboratorio Clínico ABC - Cali
                fecha_visita=manana,
                hora_inicio_sugerida=time(10, 30),
                hora_fin_sugerida=time(11, 30),
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.MEDIA,
                latitud=3.4516,  # Cali aprox
                longitud=-76.5320,
                nombre_cliente="Laboratorio Clínico ABC",
                direccion_cliente="Carrera 5 #10-15, Cali",
                observaciones="Renovación de contrato"
            ),
        ]
        
        # Agregar visitas
        for visita in visitas_seed:
            db.add(visita)
        
        db.commit()
        
        logger.info(f"✅ {len(visitas_seed)} visitas de prueba creadas")
        logger.info("✅ Seed de visita-service completado exitosamente")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error en seed de visita-service: {str(e)}")
        raise

