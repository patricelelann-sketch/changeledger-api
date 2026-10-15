"""Authentification : hashage de mot de passe, JWT, dépendance d'utilisateur courant."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from . import crud, models
from .config import ADMIN_SECRET, CRON_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY
from .database import get_db

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré.")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")
    return user_id


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise (en-tête Authorization: Bearer <token>).",
        )
    token = authorization.split(" ", 1)[1]
    user_id = _decode_token(token)
    user = crud.get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable ou inactif.")
    return user


def verify_cron_secret(x_cron_secret: Optional[str] = Header(default=None)) -> None:
    """Protège /check-all : si CRON_SECRET est défini, l'en-tête X-Cron-Secret doit correspondre."""
    if CRON_SECRET and x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Secret de cron invalide ou manquant.")


def verify_admin_secret(x_admin_secret: Optional[str] = Header(default=None)) -> None:
    """Protège les endpoints /admin/* : l'en-tête X-Admin-Secret doit correspondre à ADMIN_SECRET.

    Contrairement à verify_cron_secret, il n'y a pas de mode "ouvert" : si ADMIN_SECRET
    n'est pas configuré, les endpoints admin refusent tout appel (403) plutôt que de rester
    accessibles sans protection — ils permettent de changer le palier de n'importe quel compte.
    """
    if not ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administration désactivée (ADMIN_SECRET non configuré).",
        )
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Secret d'administration invalide ou manquant.")
