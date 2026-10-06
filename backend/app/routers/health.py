from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.health import HealthResponse
from app.dependencies.database import get_db

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {"message": "TaskFlow API is running"}