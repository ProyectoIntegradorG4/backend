from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
from uuid import uuid4
from passlib.context import CryptContext
from typing import Tuple

from app.schemas.vendedor import VendedorCreate, VendedorCreatedResponse
from app.schemas.user import UsuarioCreate
from app.models.user import User
from app.models.institucion import InstitucionAsociada
from app.models.vendedor import Vendedor
from app.schemas.vendedor import VendedoresResponse, VendedorListItem

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

class VendedorService:

    @staticmethod
    def _generar_password_temporal() -> str:
        import secrets, string
        alfabeto = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alfabeto) for _ in range(12))

    @staticmethod
    def _resolver_nit(db: Session, pais: str, nit_hint: str | None) -> str:
        if nit_hint:
            inst = db.query(InstitucionAsociada).filter(
                InstitucionAsociada.nit == nit_hint,
                InstitucionAsociada.activo.is_(True)
            ).first()
            if not inst:
                raise ValueError("NIT no autorizado o institución inactiva")
            return inst.nit

        # normalizamos país (case-insensitive)
        pais_norm = pais.strip()
        q = db.query(InstitucionAsociada).filter(
            func.lower(InstitucionAsociada.pais) == func.lower(pais_norm),
            InstitucionAsociada.activo.is_(True)
        )
        instituciones = q.all()
        if not instituciones:
            raise LookupError("No hay instituciones activas para el país indicado")
        if len(instituciones) > 1:
            # ambigüedad: se debe enviar nitInstitucion explícitamente
            raise RuntimeError("Múltiples instituciones activas para el país; envía nitInstitucion")
        return instituciones[0].nit

    @staticmethod
    def _crear_usuario(db: Session, payload: UsuarioCreate) -> User:
        # validación básica de duplicados por correo
        dup = db.query(User).filter(
            func.lower(User.correo_electronico) == func.lower(payload.correo_electronico)
        ).first()
        if dup:
            raise FileExistsError("Usuario ya existe (email)")

        password_hash = pwd_ctx.hash(payload.password_plano)

        user = User(
            nombre=payload.nombre,
            correo_electronico=payload.correo_electronico,
            password_hash=password_hash,
            nit=payload.nit,
            rol=payload.rol or "gerente_cuenta",
            activo=payload.activo
        )
        db.add(user)
        db.flush()  
        return user

    @staticmethod
    def crear_vendedor(db: Session, data: VendedorCreate) -> Tuple[VendedorCreatedResponse, str]:
        nit = VendedorService._resolver_nit(db, data.pais, data.nitInstitucion)

        password_temporal = VendedorService._generar_password_temporal()
        user_payload = UsuarioCreate(
            nombre=f"{data.nombres} {data.apellidos}".strip(),
            correo_electronico=data.email,
            password_plano=password_temporal,
            rol="gerente_cuenta",
            nit=nit,
            activo=True
        )
        user = VendedorService._crear_usuario(db, user_payload)
        vendedor_id = str(uuid4())

        db.commit()

        resp = VendedorCreatedResponse(
            vendedorId=vendedor_id,
            usuarioId=user.id,
            estado="activo",
            rol="gerente_cuenta",
            territorioId=data.territorioId,
            password_generada=True
        )
        return resp, password_temporal 
    

    @staticmethod
    def _normalize_pagination(page: int, page_size: int):
        page = page or 1
        page_size = min(max(page_size or 25, 1), 50)
        offset = (page - 1) * page_size
        return page, page_size, offset

    @staticmethod
    def listar_vendedores(
        db: Session,
        q: str | None,
        territorio_id: str | None,
        estado: str | None,
        pais: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
    ):
        page, page_size, offset = VendedorService._normalize_pagination(page, page_size)

        qry = db.query(Vendedor)

        # Búsqueda general
        if q:
            term = f"%{q.lower()}%"
            qry = qry.filter(
                func.lower(Vendedor.nombres + " " + Vendedor.apellidos).like(term) |
                func.lower(Vendedor.numeroDocumento).like(term) |
                func.lower(Vendedor.email).like(term)
            )

        # Filtros
        if territorio_id:
            qry = qry.filter(Vendedor.territorioId == territorio_id)

        if estado:
            qry = qry.filter(func.lower(Vendedor.estado) == func.lower(estado))

        if pais:
            qry = qry.filter(func.lower(Vendedor.pais) == func.lower(pais))

        total = qry.count()

        # Orden
        sort_map = {
            "apellidos": Vendedor.apellidos,
            "nombres": Vendedor.nombres,
            "actualizado_en": Vendedor.actualizado_en,
        }
        sort_col = sort_map.get(sort, Vendedor.apellidos)
        sort_fn = asc if order == "asc" else desc

        rows = qry.order_by(sort_fn(sort_col)).offset(offset).limit(page_size).all()

        items = [
            VendedorListItem(
                vendedorId=r.vendedorId,
                nombres=r.nombres,
                apellidos=r.apellidos,
                tipoDocumento=r.tipoDocumento,
                numeroDocumento=r.numeroDocumento,
                email=r.email,
                pais=r.pais,
                territorio=r.territorioNombre,
                territorioId=r.territorioId,
                estado=r.estado,
                actualizado_en=r.actualizado_en
            )
            for r in rows
        ]

        return VendedoresResponse(
            page=page,
            page_size=page_size,
            total=total,
            items=items
        )
