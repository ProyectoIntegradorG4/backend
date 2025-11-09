# app/routes/import_products.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.import_service import process_import
from app.services.rbac import require_auth_token, require_role_admincompras

router = APIRouter(
    tags=["import"],
    dependencies=[Depends(require_auth_token), Depends(require_role_admincompras)]
)

@router.post("/import-products")
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")

    try:
        content = await file.read()
        result = process_import(db, content)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando CSV: {e}"
        )
