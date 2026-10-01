"""Schémas Pydantic pour les requêtes et réponses de l'API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class SourceCreate(BaseModel):
    supplier_name: str
    label: Optional[str] = None
    url: HttpUrl


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier_name: str
    label: Optional[str]
    url: str
    created_at: datetime


class ChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    diff_text: str
    category: str
    severity: str
    summary: Optional[str]
    detected_at: datetime


class CheckResult(BaseModel):
    source_id: str
    changed: bool
    change: Optional[ChangeOut] = None
    message: str
