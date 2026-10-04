"""Schémas Pydantic pour les requêtes et réponses de l'API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, field_validator


# --- Authentification ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    plan: str
    subscription_status: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Facturation ---

class CheckoutRequest(BaseModel):
    plan: str  # "essentiel" | "pro"


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


# --- Sources / changements (inchangé, hors propriétaire implicite) ---

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
