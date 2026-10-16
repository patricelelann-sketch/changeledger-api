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
    webhook_url: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        return v


class WebhookRequest(BaseModel):
    # None (ou absent du JSON) efface le webhook configuré.
    webhook_url: Optional[str] = None

    @field_validator("webhook_url")
    @classmethod
    def webhook_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith("https://"):
            raise ValueError("L'URL du webhook doit commencer par https://.")
        return v


# --- Administration ---

class AdminSetPlanRequest(BaseModel):
    email: EmailStr
    plan: str  # "none" | "essentiel" | "pro" | "entreprise"

    @field_validator("plan")
    @classmethod
    def plan_must_be_valid(cls, v: str) -> str:
        valid = {"none", "essentiel", "pro", "entreprise"}
        if v not in valid:
            raise ValueError(f"Palier invalide. Valeurs possibles : {', '.join(sorted(valid))}.")
        return v


class AdminDeleteUserRequest(BaseModel):
    email: EmailStr


# --- Facturation ---

class CheckoutRequest(BaseModel):
    plan: str  # "essentiel" | "pro"
    cycle: str = "monthly"  # "monthly" | "annual"


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
