from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.data import csv_store

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryOut(BaseModel):
    code: str
    name: str


@router.get("", response_model=list[CategoryOut])
def list_categories() -> list[CategoryOut]:
    categories = csv_store.read_categories(settings.data_repo_path)
    return [
        CategoryOut(code=c.code, name=c.name)
        for c in sorted(categories, key=lambda c: c.name)
    ]
