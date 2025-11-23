# app/routes/visits.py

import os
import os.path as path
from uuid import uuid4
from datetime import datetime
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Body,
    Query,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.visit_service import VisitService
from app.models.visit import VisitEvidence
from app.services.rbac import (
    require_auth_token,
    require_role_admincompras_header,
    require_role_admincompras,
    CurrentUser,
)

router = APIRouter()

# =========================
# Configuración de archivos
# =========================
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
FILES_DIR = os.getenv("FILES_DIR", "/data/visits")

# Backend conmutable: "local" o "s3"
FILES_BACKEND = os.getenv("FILES_BACKEND", "local").lower()
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "visits")
FILES_BASE_URL = os.getenv("FILES_BASE_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3 = None
if FILES_BACKEND == "s3":
    import boto3

    s3 = boto3.client("s3", region_name=AWS_REGION)

# =========================
# Helpers de almacenamiento
# =========================
def _safe_name(filename: Optional[str], content_type: Optional[str]) -> str:
    if not filename:
        name = uuid4().hex
        ext = ""
    else:
        base = os.path.basename(filename)
        base = base.replace("..", "_").replace(" ", "_")
        name, ext = os.path.splitext(base)
        if not name:
            name = uuid4().hex

    if not ext and content_type:
        ct = content_type.lower()
        if ct in ("image/jpeg", "image/jpg"):
            ext = ".jpg"
        elif ct == "image/png":
            ext = ".png"
        elif ct == "image/webp":
            ext = ".webp"
        elif ct in ("video/mp4", "video/quicktime"):
            ext = ".mp4"
        elif ct in ("video/webm",):
            ext = ".webm"
        elif ct in ("video/x-matroska", "video/mkv"):
            ext = ".mkv"

    return f"{name}{ext}"


def _save_local(
    *,
    key: str,
    content: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> str:
    key = key.lstrip("/")
    key_looks_dir = key.endswith("/") or not path.splitext(key)[1]
    if key_looks_dir:
        final_name = _safe_name(filename, content_type)
        key = f"{key.rstrip('/')}/{final_name}"
    full_path = os.path.join(FILES_DIR, key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(content)
    return key


def _save_s3(
    *,
    key_prefix: str,
    content: bytes,
    filename: Optional[str],
    content_type: Optional[str],
) -> str:
    assert s3 is not None, "S3 client not initialized"
    final_name = _safe_name(filename, content_type)

    if S3_PREFIX:
        key = f"{S3_PREFIX.rstrip('/')}/{key_prefix.strip('/')}/{final_name}"
    else:
        key = f"{key_prefix.strip('/')}/{final_name}"

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content,
        ContentType=(content_type or "application/octet-stream"),
    )
    return key


def _save_bytes(
    *,
    visit_id: int,
    content: bytes,
    filename: Optional[str],
    content_type: Optional[str],
) -> str:
    key_prefix = f"{visit_id}/"
    if FILES_BACKEND == "s3":
        return _save_s3(
            key_prefix=key_prefix,
            content=content,
            filename=filename,
            content_type=content_type,
        )
    else:
        return _save_local(
            key=key_prefix,
            content=content,
            filename=filename,
            content_type=content_type,
        )


def _url_for(*, key: str) -> str:
    if FILES_BACKEND == "s3":
        # Generar pre-signed URL con expiración de 24 horas
        # Esto permite que la app móvil acceda a objetos privados de S3
        assert s3 is not None, "S3 client not initialized"
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=86400  # 24 horas (86400 segundos)
        )
        return url
    # Para local: URLs relativas (compatibilidad con StaticFiles mount en /files)
    return f"/files/{key.lstrip('/')}"


# =========================
# Helpers de fechas
# =========================
def _parse_visit_dt(payload: dict) -> datetime:
    """
    Admite:
      - visit_datetime: "2025-11-08T10:30:00"
      - date + time:    "2025-11-08" + "10:30"
    """
    visit_datetime = payload.get("visit_datetime")
    date = payload.get("date")
    time = payload.get("time")
    if visit_datetime:
        try:
            return datetime.fromisoformat(visit_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="visit_datetime debe estar en formato ISO 8601 (YYYY-MM-DDTHH:MM:SS)",
            )
    if date and time:
        try:
            return datetime.fromisoformat(f"{date}T{time}:00")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date/time inválidos, se espera date=YYYY-MM-DD y time=HH:MM",
            )
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="fecha y hora son obligatorios (visit_datetime o date+time)",
    )


# =========================
# Endpoints de VISITS
# =========================

@router.post(
    "/visits",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role_admincompras_header)],
)
def create_visit(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_auth_token),
):
    """
    Crea una visita.
    - client_id viene en el body.
    - account_mgr_id se toma del header X-User-Id (validado en RBAC).
    """
    client_id_raw = payload.get("client_id")
    if client_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="client_id es requerido",
        )

    try:
        client_id = int(client_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id debe ser numérico",
        )

    visit_dt = _parse_visit_dt(payload)

    svc = VisitService(db)
    visit = svc.create_visit(
        client_id=client_id,
        # Tomamos el id del usuario desde el header (X-User-Id),
        # validado en RBAC.
        account_mgr_id=current_user.user_id,
        visit_dt=visit_dt,
        title=payload.get("title"),
        notes=payload.get("notes"),
        contacto_nombre=payload.get("contacto_nombre"),
        tipo_visita=payload.get("tipo_visita"),
        objetivo_visita=payload.get("objetivo_visita"),
    )
    db.commit()

    return {"id": visit.id, "message": "Visita registrada exitosamente"}


@router.post(
    "/visits/{visit_id}/evidence",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role_admincompras_header)],
)
async def upload_evidence(
    visit_id: int,
    file: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    comment: str | None = Form(None),
    db: Session = Depends(get_db),
):
    svc = VisitService(db)
    visit = svc.get(visit_id)
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    inputs: List[tuple[str, UploadFile]] = []
    if image is not None:
        inputs.append(("image", image))
    if video is not None:
        inputs.append(("video", video))
    if file is not None:
        ct0 = (file.content_type or "").lower()
        if ct0.startswith("image/"):
            inputs.append(("image", file))
        elif ct0.startswith("video/"):
            inputs.append(("video", file))
        else:
            inputs.append(("file", file))

    if not inputs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes enviar al menos una evidencia: imagen y/o video",
        )

    results = []
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024

    for kind, up in inputs:
        content = await up.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo '{up.filename or '(sin nombre)'}' excede {MAX_UPLOAD_MB}MB",
            )

        ct = (up.content_type or "application/octet-stream").lower()
        if kind == "image" and not ct.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"'{up.filename}' no es un contenido de imagen válido",
            )
        if kind == "video" and not ct.startswith("video/"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"'{up.filename}' no es un contenido de video válido",
            )
        if kind == "file" and not (ct.startswith("image/") or ct.startswith("video/")):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"'{up.filename}' debe ser imagen o video",
            )

        storage_key = _save_bytes(
            visit_id=visit_id,
            content=content,
            filename=up.filename,
            content_type=ct,
        )

        ev = svc.add_evidence(
            visit_id=visit_id,
            filename=os.path.basename(storage_key),
            content_type=ct,
            size_bytes=len(content),
            storage_key=storage_key,
        )
        results.append(
            {
                "id": ev.id,
                "filename": ev.filename,
                "content_type": ev.content_type,
                "size_bytes": ev.size_bytes,
                "url": _url_for(key=storage_key),
            }
        )

    # Actualizar notas de la visita con el comentario (HU-MOV-006)
    if comment:
        existing_notes = visit.notes or ""
        if existing_notes:
            visit.notes = f"{existing_notes}\n\n[Evidencia] {comment}"
        else:
            visit.notes = f"[Evidencia] {comment}"
        db.add(visit)

    db.commit()
    return {"items": results, "count": len(results)}


@router.get(
    "/api/v1/visits/client/{client_id}",
    dependencies=[Depends(require_role_admincompras)],
)
def list_visits_by_client(
    client_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    svc = VisitService(db)
    items, total = svc.list_by_client(client_id, limit, offset)

    def map_visit(v):
        return {
            "id": v.id,
            "client_id": v.client_id,
            "account_mgr_id": v.account_mgr_id,
            "visit_datetime": v.visit_datetime.isoformat(),
            "title": v.title,
            "notes": v.notes,
            "contacto_nombre": v.contacto_nombre,
            "tipo_visita": v.tipo_visita,
            "objetivo_visita": v.objetivo_visita,
            "evidences": [
                {
                    "id": e.id,
                    "filename": e.filename,
                    "content_type": e.content_type,
                    "size_bytes": e.size_bytes,
                    "url": _url_for(key=e.storage_key),
                }
                for e in v.evidences
            ],
        }

    return {"items": [map_visit(v) for v in items], "total": total}


@router.get(
    "/api/v1/visits/{visit_id}",
    dependencies=[Depends(require_role_admincompras)],
)
def get_visit(
    visit_id: int,
    db: Session = Depends(get_db),
):

    svc = VisitService(db)
    v = svc.get(visit_id)
    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    return {
        "id": v.id,
        "client_id": v.client_id,
        "account_mgr_id": v.account_mgr_id,
        "visit_datetime": v.visit_datetime.isoformat(),
        "title": v.title,
        "notes": v.notes,
        "contacto_nombre": v.contacto_nombre,
        "tipo_visita": v.tipo_visita,
        "objetivo_visita": v.objetivo_visita,
        "evidences": [
            {
                "id": e.id,
                "filename": e.filename,
                "content_type": e.content_type,
                "size_bytes": e.size_bytes,
                "url": _url_for(key=e.storage_key),
            }
            for e in v.evidences
        ],
    }


@router.get(
    "/api/v1/visits/{visit_id}/evidence/{evidence_id}/url",
    dependencies=[Depends(require_role_admincompras)],
)
def regenerate_evidence_url(
    visit_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
):
    """
    Regenera URL pre-firmada para una evidencia específica.
    Útil cuando la URL expira (después de 24 horas).
    """
    evidence = db.query(VisitEvidence).filter(
        VisitEvidence.id == evidence_id,
        VisitEvidence.visit_id == visit_id
    ).first()
    
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidencia no encontrada"
        )
    
    return {
        "id": evidence.id,
        "url": _url_for(key=evidence.storage_key),
        "expires_in_seconds": 86400,  # 24 horas
    }
