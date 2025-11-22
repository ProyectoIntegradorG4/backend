# app/service/plan_venta_service.py
import os
import logging
from typing import List, Tuple, Optional
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.plan_venta import PlanVenta, PlanVentaTerritorio, PlanMeta
from app.models.territorio import Territorio
from app.models.product import Producto
from app.schemas.plan_venta import PlanVentaCreate, MetaCreate

logger = logging.getLogger(__name__)

# URL para acceso cross-database a user_db
USER_DB_URL = os.getenv(
    "USER_DATABASE_URL",
    "postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db"
)

# Log the connection URL being used (without password for security)
import re
masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', USER_DB_URL)
logger.info(f"Using USER_DB_URL: {masked_url}")


class PlanVentaService:
    """
    Servicio para gestionar Planes de Venta (HU-WEB-008)
    """

    @staticmethod
    def _validar_vendedores(vendedor_ids: List[int]) -> Tuple[bool, List[int], str]:
        """
        Valida que los vendedores existan en user_db con rol='gerente_cuenta'
        
        Returns:
            Tuple[bool, List[int], str]: (éxito, ids_válidos, mensaje_error)
        """
        if not vendedor_ids:
            return False, [], "No se proporcionaron IDs de vendedores"
        
        try:
            user_engine = create_engine(USER_DB_URL)
            with user_engine.connect() as conn:
                # Consultar usuarios con rol 'gerente_cuenta'
                query = text("""
                    SELECT id FROM usuarios 
                    WHERE id = ANY(:ids) 
                    AND rol = 'gerente_cuenta' 
                    AND activo = true
                """)
                result = conn.execute(query, {"ids": vendedor_ids})
                vendedores_validos = [row[0] for row in result.fetchall()]
            
            user_engine.dispose()
            
            if len(vendedores_validos) != len(set(vendedor_ids)):
                invalidos = set(vendedor_ids) - set(vendedores_validos)
                return False, vendedores_validos, f"Vendedores inválidos o inactivos: {list(invalidos)}"
            
            return True, vendedores_validos, ""
            
        except Exception as e:
            logger.error(f"Error validando vendedores: {e}")
            return False, [], f"Error al validar vendedores: {str(e)}"

    @staticmethod
    def _validar_territorios(db: Session, territorio_ids: List[str]) -> Tuple[bool, str]:
        """
        Valida que los territorios existan y estén activos
        """
        territorios = db.query(Territorio).filter(
            Territorio.territorio_id.in_(territorio_ids),
            Territorio.activo == True
        ).all()
        
        if len(territorios) != len(set(territorio_ids)):
            encontrados = {t.territorio_id for t in territorios}
            faltantes = set(territorio_ids) - encontrados
            return False, f"Territorios no encontrados o inactivos: {list(faltantes)}"
        
        return True, ""

    @staticmethod
    def _validar_productos(db: Session, producto_ids: List[str]) -> Tuple[bool, str]:
        """
        Valida que los productos existan y estén activos
        """
        productos = db.query(Producto).filter(
            Producto.productoId.in_(producto_ids),
            Producto.estado_producto == 'activo'
        ).all()
        
        if len(productos) != len(set(producto_ids)):
            encontrados = {p.productoId for p in productos}
            faltantes = set(producto_ids) - encontrados
            return False, f"Productos no encontrados o inactivos: {list(faltantes)}"
        
        return True, ""

    @staticmethod
    def _validar_metas_duplicadas(metas: List[MetaCreate]) -> Tuple[bool, str]:
        """
        Valida que no haya metas duplicadas (producto + territorio + vendedor)
        """
        combinaciones = set()
        for meta in metas:
            comb = (meta.productoId, meta.territorioId, meta.vendedorId)
            if comb in combinaciones:
                return False, f"Meta duplicada: Producto {meta.productoId}, Territorio {meta.territorioId}, Vendedor {meta.vendedorId}"
            combinaciones.add(comb)
        
        return True, ""

    @staticmethod
    def _validar_objetivos_metas(metas: List[MetaCreate]) -> Tuple[bool, str]:
        """
        Valida que cada meta tenga al menos un objetivo (cantidad o valor) mayor a 0
        """
        for idx, meta in enumerate(metas):
            if meta.objetivo_cantidad <= 0 and (meta.objetivo_valor is None or meta.objetivo_valor <= 0):
                return False, f"Meta {idx + 1}: Debe tener al menos un objetivo (cantidad o valor) mayor a 0"
        
        return True, ""

    @staticmethod
    def crear_plan_venta(db: Session, payload: PlanVentaCreate, usuario_id: Optional[int] = None) -> PlanVenta:
        """
        Crea un plan de venta con validaciones completas
        
        Args:
            db: Sesión de base de datos
            payload: Datos del plan a crear
            usuario_id: ID del usuario que crea el plan (opcional)
        
        Returns:
            PlanVenta: Plan creado
        
        Raises:
            HTTPException: Si hay errores de validación
        """
        
        # 1. Validar nombre único
        plan_existente = db.query(PlanVenta).filter(
            PlanVenta.nombre == payload.nombre
        ).first()
        
        if plan_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un plan con el nombre '{payload.nombre}'"
            )
        
        # 2. Validar territorios
        valido, error_msg = PlanVentaService._validar_territorios(db, payload.territorios)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 3. Extraer IDs de productos y vendedores de las metas
        producto_ids = list(set([meta.productoId for meta in payload.metas]))
        vendedor_ids = list(set([meta.vendedorId for meta in payload.metas]))
        
        # 4. Validar productos
        valido, error_msg = PlanVentaService._validar_productos(db, producto_ids)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 5. Validar vendedores (cross-database)
        valido, vendedores_validos, error_msg = PlanVentaService._validar_vendedores(vendedor_ids)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 6. Validar metas duplicadas
        valido, error_msg = PlanVentaService._validar_metas_duplicadas(payload.metas)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 7. Validar objetivos de metas
        valido, error_msg = PlanVentaService._validar_objetivos_metas(payload.metas)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 8. Validar que las metas solo usen territorios del plan
        territorios_en_metas = set([meta.territorioId for meta in payload.metas])
        if not territorios_en_metas.issubset(set(payload.territorios)):
            territorios_invalidos = territorios_en_metas - set(payload.territorios)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metas contienen territorios no incluidos en el plan: {list(territorios_invalidos)}"
            )
        
        try:
            # 9. Crear el plan de venta
            nuevo_plan = PlanVenta(
                nombre=payload.nombre,
                periodo_desde=payload.periodo['desde'],
                periodo_hasta=payload.periodo['hasta'],
                estado='activo',
                created_by=usuario_id
            )
            db.add(nuevo_plan)
            db.flush()  # Para obtener el plan_id
            
            # 10. Asociar territorios al plan
            for territorio_id in payload.territorios:
                plan_territorio = PlanVentaTerritorio(
                    plan_id=nuevo_plan.plan_id,
                    territorio_id=territorio_id
                )
                db.add(plan_territorio)
            
            # 11. Crear las metas
            for meta in payload.metas:
                nueva_meta = PlanMeta(
                    plan_id=nuevo_plan.plan_id,
                    producto_id=meta.productoId,
                    territorio_id=meta.territorioId,
                    vendedor_id=meta.vendedorId,
                    objetivo_cantidad=meta.objetivo_cantidad,
                    objetivo_valor=float(meta.objetivo_valor) if meta.objetivo_valor else 0,
                    nota=meta.nota
                )
                db.add(nueva_meta)
            
            # 12. Commit transaccional (todo o nada)
            db.commit()
            db.refresh(nuevo_plan)
            
            logger.info(f"✅ Plan de venta creado: {nuevo_plan.plan_id} - {nuevo_plan.nombre}")
            return nuevo_plan
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creando plan de venta: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear el plan de venta: {str(e)}"
            )

    @staticmethod
    def listar_planes_venta(
        db: Session,
        q: Optional[str] = None,
        estado: Optional[str] = None,
        periodo_from: Optional[date] = None,
        periodo_to: Optional[date] = None,
        territorio_id: Optional[str] = None,
        producto_id: Optional[str] = None,
        sort: str = "updated_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[List[PlanVenta], int]:
        """
        Lista los planes de venta con búsqueda, filtros, ordenamiento y paginación (HU-WEB-009)
        
        Args:
            db: Sesión de base de datos
            q: Búsqueda por nombre (ILIKE, case-insensitive)
            estado: Filtro por estado (activo, borrador, cerrado)
            periodo_from: Filtro por período - fecha inicio del rango
            periodo_to: Filtro por período - fecha fin del rango (intersección con período del plan)
            territorio_id: Filtro por territorio incluido en el plan
            producto_id: Filtro por producto incluido en metas del plan (opcional)
            sort: Campo de ordenamiento (nombre, periodo_desde, updated_at)
            order: Dirección de ordenamiento (asc, desc)
            page: Número de página (>=1)
            page_size: Tamaño de página (<=50)
        
        Returns:
            Tuple[List[PlanVenta], int]: (planes, total)
        """
        from sqlalchemy import exists, and_, or_
        
        query = db.query(PlanVenta)
        
        # Búsqueda por nombre (ILIKE - case insensitive)
        if q:
            query = query.filter(PlanVenta.nombre.ilike(f"%{q}%"))
        
        # Filtro por estado
        if estado:
            query = query.filter(PlanVenta.estado == estado)
        
        # Filtro por período (intersección de rangos)
        # Un plan intersecta el rango si:
        # plan.periodo_desde <= periodo_to AND plan.periodo_hasta >= periodo_from
        if periodo_from and periodo_to:
            query = query.filter(
                and_(
                    PlanVenta.periodo_desde <= periodo_to,
                    PlanVenta.periodo_hasta >= periodo_from
                )
            )
        elif periodo_from:
            # Solo fecha inicio: planes que terminan después de periodo_from
            query = query.filter(PlanVenta.periodo_hasta >= periodo_from)
        elif periodo_to:
            # Solo fecha fin: planes que empiezan antes de periodo_to
            query = query.filter(PlanVenta.periodo_desde <= periodo_to)
        
        # Filtro por territorio (EXISTS en plan_venta_territorio)
        if territorio_id:
            query = query.filter(
                exists().where(
                    and_(
                        PlanVentaTerritorio.plan_id == PlanVenta.plan_id,
                        PlanVentaTerritorio.territorio_id == territorio_id
                    )
                )
            )
        
        # Filtro por producto (EXISTS en plan_meta) - opcional
        if producto_id:
            query = query.filter(
                exists().where(
                    and_(
                        PlanMeta.plan_id == PlanVenta.plan_id,
                        PlanMeta.producto_id == producto_id
                    )
                )
            )
        
        # Total antes de paginar
        total = query.count()
        
        # Ordenamiento dinámico
        sort_column = {
            "nombre": PlanVenta.nombre,
            "periodo_desde": PlanVenta.periodo_desde,
            "updated_at": PlanVenta.updated_at
        }.get(sort, PlanVenta.updated_at)
        
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Paginación
        planes = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return planes, total

    @staticmethod
    def obtener_plan_por_id(db: Session, plan_id: str) -> Optional[PlanVenta]:
        """
        Obtiene un plan de venta por su ID con todas sus relaciones
        """
        from sqlalchemy.orm import joinedload
        
        plan = db.query(PlanVenta).options(
            joinedload(PlanVenta.territorios).joinedload(PlanVentaTerritorio.territorio),
            joinedload(PlanVenta.metas).joinedload(PlanMeta.territorio)
        ).filter(PlanVenta.plan_id == plan_id).first()
        
        return plan

    @staticmethod
    def listar_territorios(db: Session, activo: Optional[bool] = True) -> List[Territorio]:
        """
        Lista todos los territorios disponibles
        """
        query = db.query(Territorio)
        
        if activo is not None:
            query = query.filter(Territorio.activo == activo)
        
        return query.order_by(Territorio.nombre).all()
