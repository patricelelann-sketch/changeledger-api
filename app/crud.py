"""Opérations de base de données (CRUD) pour users, sources, snapshots et changements."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from . import models


# --- Users ---

def create_user(db: Session, email: str, hashed_password: str) -> models.User:
    user = models.User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_stripe_customer_id(db: Session, stripe_customer_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.stripe_customer_id == stripe_customer_id).first()


def set_user_stripe_customer(db: Session, user: models.User, stripe_customer_id: str) -> models.User:
    user.stripe_customer_id = stripe_customer_id
    db.commit()
    db.refresh(user)
    return user


def update_subscription(
    db: Session,
    user: models.User,
    plan: str,
    stripe_subscription_id: Optional[str],
    subscription_status: Optional[str],
) -> models.User:
    user.plan = plan
    user.stripe_subscription_id = stripe_subscription_id
    user.subscription_status = subscription_status
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[models.User]:
    """Tous les comptes — utilisé par l'endpoint d'administration /admin/users."""
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


def set_plan(db: Session, user: models.User, plan: str) -> models.User:
    """Change manuellement le palier d'un utilisateur (ex. activation Entreprise après
    contact commercial). Ne touche pas aux champs Stripe : utile aussi bien pour un compte
    sans abonnement Stripe (Entreprise) que pour corriger ponctuellement un palier existant."""
    user.plan = plan
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User) -> None:
    """Supprime définitivement un compte et toutes ses données associées (sources, snapshots,
    changements), via la cascade ORM définie sur User.sources. Utilisé pour nettoyer un compte
    de test, ou pour répondre à une demande de suppression de compte (droit RGPD à l'effacement).
    Ne touche pas à Stripe : annuler/supprimer séparément l'abonnement ou le client côté Stripe
    si besoin."""
    db.delete(user)
    db.commit()


def set_reset_token(db: Session, user: models.User, token: str, expires_at: datetime) -> models.User:
    user.reset_token = token
    user.reset_token_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return user


def get_user_by_reset_token(db: Session, token: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.reset_token == token).first()


def reset_password(db: Session, user: models.User, hashed_password: str) -> models.User:
    """Change le mot de passe et invalide le jeton (usage unique)."""
    user.hashed_password = hashed_password
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def set_webhook_url(db: Session, user: models.User, webhook_url: Optional[str]) -> models.User:
    """Enregistre (ou efface, si webhook_url est None) le webhook d'alerte de l'utilisateur."""
    user.webhook_url = webhook_url
    db.commit()
    db.refresh(user)
    return user


# --- Sources (scopées à un utilisateur) ---

def create_source(db: Session, user_id: str, supplier_name: str, label: Optional[str], url: str) -> models.Source:
    source = models.Source(user_id=user_id, supplier_name=supplier_name, label=label, url=url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def count_sources_for_user(db: Session, user_id: str) -> int:
    return db.query(models.Source).filter(models.Source.user_id == user_id).count()


def list_sources(db: Session, user_id: str) -> list[models.Source]:
    return (
        db.query(models.Source)
        .filter(models.Source.user_id == user_id)
        .order_by(models.Source.created_at.desc())
        .all()
    )


def list_all_sources(db: Session) -> list[models.Source]:
    """Toutes les sources, tous utilisateurs confondus — utilisé par /check-all."""
    return db.query(models.Source).all()


def get_source(db: Session, user_id: str, source_id: str) -> Optional[models.Source]:
    return (
        db.query(models.Source)
        .filter(models.Source.id == source_id, models.Source.user_id == user_id)
        .first()
    )


def delete_source(db: Session, source: models.Source) -> None:
    db.delete(source)
    db.commit()


def latest_snapshot(db: Session, source_id: str) -> Optional[models.Snapshot]:
    return (
        db.query(models.Snapshot)
        .filter(models.Snapshot.source_id == source_id)
        .order_by(models.Snapshot.captured_at.desc())
        .first()
    )


def create_snapshot(db: Session, source_id: str, content: str, content_hash: str) -> models.Snapshot:
    snapshot = models.Snapshot(source_id=source_id, content=content, content_hash=content_hash)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_change(
    db: Session,
    source_id: str,
    previous_snapshot_id: Optional[str],
    new_snapshot_id: str,
    diff_text: str,
    category: str,
    severity: str,
    summary: str,
) -> models.Change:
    change = models.Change(
        source_id=source_id,
        previous_snapshot_id=previous_snapshot_id,
        new_snapshot_id=new_snapshot_id,
        diff_text=diff_text,
        category=category,
        severity=severity,
        summary=summary,
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


def list_changes(db: Session, user_id: str, source_id: Optional[str] = None) -> list[models.Change]:
    query = db.query(models.Change).join(models.Source).filter(models.Source.user_id == user_id)
    if source_id:
        query = query.filter(models.Change.source_id == source_id)
    return query.order_by(models.Change.detected_at.desc()).all()


def get_change(db: Session, user_id: str, change_id: str) -> Optional[models.Change]:
    return (
        db.query(models.Change)
        .join(models.Source)
        .filter(models.Change.id == change_id, models.Source.user_id == user_id)
        .first()
    )
