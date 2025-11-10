from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_, create_engine
from app.models.cliente import (
    Cliente, GerenteClienteAsignacion, 
    ClienteListResponse, ClienteListItem, ClienteResponse,
    TiposInstitucionResponse, TipoInstitucion
)
from typing import Optional, Tuple, List
from fastapi import HTTPException
import logging
import os

logger = logging.getLogger("uvicorn")

# Conexión a user_db para consultas cross-database
USER_DB_URL = os.getenv(
    "USER_DATABASE_URL",
    "postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db"
)

# Conexión a nit_db para validar instituciones asociadas
NIT_DB_URL = os.getenv(
    "NIT_DATABASE_URL",
    "postgresql+psycopg://nit_service:nit_password@postgres-db:5432/nit_db"
)


class ClienteService:
    """
    Servicio de lógica de negocio para gestión de clientes
    """
    
    def __init__(self, db: Session):
        self.db = db

    def validate_nit_institucion(self, nit: str, pais: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validar que un NIT existe en la tabla instituciones_asociadas.
        
        Esta validación garantiza que solo se pueden crear clientes (sedes)
        para instituciones que están registradas en instituciones_asociadas.
        
        Args:
            nit: NIT a validar
            pais: País opcional para validar que coincide con la institución
            
        Returns:
            Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
            - Si es válido: (True, None)
            - Si no es válido: (False, mensaje de error)
        """
        try:
            nit_engine = create_engine(NIT_DB_URL)
            with nit_engine.connect() as conn:
                query = text("""
                    SELECT nit, nombre_institucion, pais, activo 
                    FROM instituciones_asociadas 
                    WHERE nit = :nit
                """)
                result = conn.execute(query, {"nit": nit}).fetchone()
            
            nit_engine.dispose()
            
            if not result:
                return (False, f"El NIT {nit} no existe en instituciones_asociadas")
            
            # Validar que la institución esté activa
            if not result.activo:
                return (False, f"La institución con NIT {nit} ({result.nombre_institucion}) está inactiva")
            
            # Validar que el país coincida si se proporciona
            if pais and result.pais != pais:
                return (False, f"El país '{pais}' no coincide con el país de la institución '{result.pais}'")
            
            logger.info(f"✅ NIT {nit} validado correctamente: {result.nombre_institucion} ({result.pais})")
            return (True, None)
            
        except Exception as e:
            logger.error(f"Error al validar NIT {nit}: {str(e)}")
            return (False, f"Error al validar NIT: {str(e)}")

    def get_gerente_pais(self, gerente_id: int) -> Optional[str]:
        """
        Obtener el país del gerente basado en su NIT asociado.
        
        El gerente está asociado a un NIT de MediSupply. Se hace mapeo del NIT a país.
        En un entorno de producción, esto debería ser una llamada HTTP al 
        user-service y nit-validation-service.
        
        Args:
            gerente_id: ID del gerente (usuarios.id)
            
        Returns:
            País del gerente o None si no se encuentra
        """
        try:
            # Mapeo de NITs de MediSupply a países (según NITValidationData.json)
            NIT_PAIS_MAP = {
                "111111111-1": "Colombia",
                "111111111-2": "Mexico",
                "111111111-3": "Peru",
                "111111111-4": "Ecuador"
            }
            
            # Consulta para obtener el NIT del gerente desde user_db
            # Usamos una conexión temporal a user_db
            # En producción, esto debería ser una llamada HTTP al user-service
            user_engine = create_engine(USER_DB_URL)
            with user_engine.connect() as conn:
                query = text("""
                    SELECT nit FROM usuarios WHERE id = :gerente_id
                """)
                result = conn.execute(query, {"gerente_id": gerente_id}).fetchone()
            
            user_engine.dispose()
            
            if result and result.nit:
                nit = result.nit
                # Mapear NIT a país
                pais = NIT_PAIS_MAP.get(nit)
                if pais:
                    logger.info(f"País del gerente {gerente_id} (NIT {nit}): {pais}")
                    return pais
                else:
                    logger.warning(f"NIT {nit} no está en el mapeo de MediSupply")
                    return None
                
            logger.warning(f"No se encontró NIT para gerente {gerente_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener país del gerente {gerente_id}: {str(e)}")
            return None

    def get_clientes_asignados_a_gerente(
        self,
        gerente_id: int,
        gerente_pais: str,
        tipo_institucion: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        activo: bool = True
    ) -> ClienteListResponse:
        """
        Obtener lista de clientes ASIGNADOS a un gerente específico mediante
        la tabla gerente_cuenta_clientes.
        
        Args:
            gerente_id: ID del gerente
            gerente_pais: País del gerente (para validación)
            tipo_institucion: Filtro opcional por tipo de institución
            search: Búsqueda opcional por nombre o ubicación
            page: Número de página (1-indexed)
            limit: Elementos por página
            activo: Filtrar solo clientes activos
            
        Returns:
            ClienteListResponse con resultados paginados
        """
        try:
            # Base query: clientes asignados al gerente mediante la tabla de asignaciones
            query = self.db.query(Cliente).join(
                GerenteClienteAsignacion,
                Cliente.cliente_id == GerenteClienteAsignacion.cliente_id
            ).filter(
                GerenteClienteAsignacion.gerente_id == gerente_id,
                GerenteClienteAsignacion.activo == True,
                Cliente.pais == gerente_pais,
                Cliente.activo == activo
            )

            # Aplicar filtro de tipo de institución
            if tipo_institucion:
                query = query.filter(Cliente.tipo_institucion == tipo_institucion)

            # Aplicar búsqueda por nombre o ubicación
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Cliente.nombre_comercial.ilike(search_pattern),
                        Cliente.razon_social.ilike(search_pattern),
                        Cliente.ciudad.ilike(search_pattern),
                        Cliente.direccion.ilike(search_pattern)
                    )
                )

            # Contar total de resultados
            total = query.count()

            # Aplicar paginación
            offset = (page - 1) * limit
            clientes = query.order_by(Cliente.nombre_comercial).offset(offset).limit(limit).all()

            # Convertir a response models
            clientes_list = [ClienteListItem.model_validate(cliente) for cliente in clientes]

            return ClienteListResponse(
                total=total,
                page=page,
                limit=limit,
                clientes=clientes_list
            )

        except Exception as e:
            logger.error(f"Error al obtener clientes del gerente {gerente_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener lista de clientes")

    def get_cliente_detail(
        self,
        cliente_id: int,
        gerente_id: int,
        gerente_pais: str
    ) -> ClienteResponse:
        """
        Obtener detalle completo de un cliente específico.
        Verifica que el cliente pertenezca al mismo país que el gerente.
        
        Args:
            cliente_id: ID del cliente
            gerente_id: ID del gerente solicitante
            gerente_pais: País del gerente
            
        Returns:
            ClienteResponse con detalles completos
            
        Raises:
            HTTPException 404 si no se encuentra o no tiene acceso
        """
        try:
            cliente = self.db.query(Cliente).filter(
                Cliente.cliente_id == cliente_id,
                Cliente.pais == gerente_pais
            ).first()

            if not cliente:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente no encontrado o no tiene acceso a este cliente"
                )

            return ClienteResponse.model_validate(cliente)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener detalle del cliente {cliente_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener detalle del cliente")

    def verify_gerente_access(self, gerente_id: int, cliente_id: int, gerente_pais: str) -> bool:
        """
        Verificar si un gerente tiene acceso a un cliente específico.
        
        Args:
            gerente_id: ID del gerente
            cliente_id: ID del cliente
            gerente_pais: País del gerente
            
        Returns:
            True si tiene acceso, False en caso contrario
        """
        try:
            cliente = self.db.query(Cliente).filter(
                Cliente.cliente_id == cliente_id,
                Cliente.pais == gerente_pais
            ).first()

            return cliente is not None

        except Exception as e:
            logger.error(f"Error al verificar acceso del gerente {gerente_id} al cliente {cliente_id}: {str(e)}")
            return False

    def get_tipos_institucion(self) -> TiposInstitucionResponse:
        """
        Obtener lista de tipos de institución disponibles.
        
        Returns:
            TiposInstitucionResponse con lista de tipos
        """
        tipos = [tipo.value for tipo in TipoInstitucion]
        return TiposInstitucionResponse(tipos=tipos)

    def get_clientes_simple(
        self,
        pais: Optional[str] = None,
        tipo_institucion: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        activo: bool = True
    ) -> ClienteListResponse:
        """
        Obtener lista de clientes con filtros opcionales (sin autenticación).
        
        Args:
            pais: País para filtrar (opcional)
            tipo_institucion: Filtro opcional por tipo de institución
            search: Búsqueda opcional por nombre o ubicación
            page: Número de página (1-indexed)
            limit: Elementos por página
            activo: Filtrar solo clientes activos
            
        Returns:
            ClienteListResponse con resultados paginados
        """
        try:
            # Base query
            query = self.db.query(Cliente).filter(Cliente.activo == activo)

            # Filtro por país (opcional)
            if pais:
                query = query.filter(Cliente.pais == pais)

            # Aplicar filtro de tipo de institución
            if tipo_institucion:
                query = query.filter(Cliente.tipo_institucion == tipo_institucion)

            # Aplicar búsqueda por nombre o ubicación
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Cliente.nombre_comercial.ilike(search_pattern),
                        Cliente.razon_social.ilike(search_pattern),
                        Cliente.ciudad.ilike(search_pattern),
                        Cliente.direccion.ilike(search_pattern)
                    )
                )

            # Contar total de resultados
            total = query.count()

            # Aplicar paginación
            offset = (page - 1) * limit
            clientes = query.order_by(Cliente.nombre_comercial).offset(offset).limit(limit).all()

            # Convertir a response models
            clientes_list = [ClienteListItem.model_validate(cliente) for cliente in clientes]

            return ClienteListResponse(
                total=total,
                page=page,
                limit=limit,
                clientes=clientes_list
            )

        except Exception as e:
            logger.error(f"Error al obtener clientes: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener lista de clientes")

    def get_cliente_detail_simple(self, cliente_id: int) -> ClienteResponse:
        """
        Obtener detalle completo de un cliente específico (sin autenticación).
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            ClienteResponse con detalles completos
            
        Raises:
            HTTPException 404 si no se encuentra
        """
        try:
            cliente = self.db.query(Cliente).filter(
                Cliente.cliente_id == cliente_id
            ).first()

            if not cliente:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente no encontrado"
                )

            return ClienteResponse.model_validate(cliente)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener detalle del cliente {cliente_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener detalle del cliente")

    def get_cliente_by_nit(self, nit: str) -> Optional[Cliente]:
        """
        Buscar un cliente por su NIT.
        
        Args:
            nit: NIT del cliente
            
        Returns:
            Cliente si existe, None en caso contrario
        """
        try:
            return self.db.query(Cliente).filter(Cliente.nit == nit).first()
        except Exception as e:
            logger.error(f"Error al buscar cliente por NIT {nit}: {str(e)}")
            return None

    def get_gerente_nits(self, gerente_id: int) -> List[str]:
        """
        Obtener lista de NITs únicos de los clientes asignados a un gerente.
        
        Args:
            gerente_id: ID del gerente
            
        Returns:
            Lista de NITs únicos de los clientes asignados al gerente
        """
        try:
            # Obtener NITs únicos de los clientes asignados al gerente
            nits = self.db.query(GerenteClienteAsignacion.nit).filter(
                GerenteClienteAsignacion.gerente_id == gerente_id,
                GerenteClienteAsignacion.activo == True,
                GerenteClienteAsignacion.nit.isnot(None)
            ).distinct().all()
            
            # Extraer valores de las tuplas
            nits_list = [nit[0] for nit in nits if nit[0]]
            
            logger.info(f"✅ NITs del gerente {gerente_id}: {nits_list}")
            return nits_list
            
        except Exception as e:
            logger.error(f"Error al obtener NITs del gerente {gerente_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener NITs del gerente")

    def get_gerente_cliente_ids(self, gerente_id: int) -> List[int]:
        """
        Obtener lista de cliente_ids (sedes) asignados a un gerente.
        
        Args:
            gerente_id: ID del gerente
            
        Returns:
            Lista de cliente_ids de las sedes asignadas al gerente
        """
        try:
            # Obtener cliente_ids de los clientes asignados al gerente
            cliente_ids = self.db.query(GerenteClienteAsignacion.cliente_id).filter(
                GerenteClienteAsignacion.gerente_id == gerente_id,
                GerenteClienteAsignacion.activo == True
            ).all()
            
            # Extraer valores de las tuplas
            cliente_ids_list = [cid[0] for cid in cliente_ids if cid[0]]
            
            logger.info(f"✅ Cliente IDs del gerente {gerente_id}: {cliente_ids_list}")
            return cliente_ids_list
            
        except Exception as e:
            logger.error(f"Error al obtener cliente_ids del gerente {gerente_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener cliente_ids del gerente")

    def create_asignacion(
        self,
        gerente_id: int,
        cliente_id: int,
        pais: str
    ) -> GerenteClienteAsignacion:
        """
        Crear una asignación de cliente a gerente.
        
        Args:
            gerente_id: ID del gerente
            cliente_id: ID del cliente
            pais: País de la asignación
            
        Returns:
            GerenteClienteAsignacion creada
            
        Raises:
            HTTPException si ya existe la asignación
        """
        try:
            # Verificar si ya existe la asignación
            existing = self.db.query(GerenteClienteAsignacion).filter(
                GerenteClienteAsignacion.gerente_id == gerente_id,
                GerenteClienteAsignacion.cliente_id == cliente_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="La asignación ya existe"
                )

            # Crear nueva asignación
            asignacion = GerenteClienteAsignacion(
                gerente_id=gerente_id,
                cliente_id=cliente_id,
                pais=pais,
                activo=True
            )

            self.db.add(asignacion)
            self.db.commit()
            self.db.refresh(asignacion)

            logger.info(f"✅ Asignación creada: gerente {gerente_id} -> cliente {cliente_id}")
            return asignacion

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear asignación: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al crear asignación")

