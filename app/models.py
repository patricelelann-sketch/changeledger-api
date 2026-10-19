"""Modèles de base de données : User, Source, Snapshot, Change."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChangeCategory(str, enum.Enum):
    tarif = "tarif"
    resiliation = "resiliation"
    paiement = "paiement"
    responsabilite = "responsabilite"
    autre = "autre"


class ChangeSeverity(str, enum.Enum):
    info = "info"
    attention = "attention"
    urgent = "urgent"


class PlanType(str, enum.Enum):
    none = "none"  # inscrit mais pas encore abonné
    essentiel = "essentiel"
    pro = "pro"
    entreprise = "entreprise"  # activé manuellement après contact commercial


# Nombre de sources surveillées autorisées par palier. None = illimité.
# NB : 5/25 avaient été évoqués un temps puis révisés à 10/50 après étude plus poussée du
# marché — ce sont bien 10/50 qui ont été communiqués publiquement (page marketing, tarifs
# Stripe) ; ne pas les repasser à 5/25 sans vérifier auprès de Patrice.
PLAN_LIMITS: dict[str, "int | None"] = {
    PlanType.none.value: 0,
    PlanType.essentiel.value: 10,
    PlanType.pro.value: 50,
    PlanType.entreprise.value: None,
}

# Taille d'une tranche supplémentaire achetable en self-service, par palier (cf. tarifs
# Stripe "Tranche supplémentaire de N fournisseurs — mensuel/annuel"). Le palier Entreprise
# n'a pas de tranches : ses sources sont déjà illimitées (PLAN_LIMITS[...] is None).
TRANCHE_SIZE: dict[str, int] = {
    PlanType.essentiel.value: 10,
    PlanType.pro.value: 50,
}


def effective_limit(plan: str, extra_tranches: int) -> "int | None":
    """Limite réelle de sources pour un utilisateur, en tenant compte des tranches
    supplémentaires achetées. None = illimité (palier Entreprise)."""
    base = PLAN_LIMITS.get(plan)
    if base is None:
        return None
    return base + TRANCHE_SIZE.get(plan, 0) * (extra_tranches or 0)


class User(Base):
    """Un compte client ChangeLedger."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)

    plan = Column(Enum(PlanType), default=PlanType.none, nullable=False)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, nullable=True)  # ex. active, past_due, canceled

    # Réinitialisation de mot de passe : un jeton à usage unique, à durée de vie limitée.
    # Stocké en UTC naïf (sans fuseau) volontairement, pour une comparaison simple côté code
    # sans risquer de mélanger naïf/conscient selon le moteur de base (SQLite vs Postgres).
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    # Alertes webhook (Slack, Zapier, système interne...), en complément de l'alerte email.
    # Self-service : l'utilisateur configure sa propre URL via PUT /auth/webhook.
    webhook_url = Column(String, nullable=True)

    # Nombre de tranches supplémentaires de fournisseurs achetées en self-service (cf.
    # TRANCHE_SIZE), en plus du quota de base du palier. Synchronisé depuis Stripe (source
    # de vérité) à chaque paiement/màj d'abonnement — voir billing.handle_webhook_event.
    extra_tranches = Column(Integer, default=0, nullable=False)

    sources = relationship("Source", back_populates="owner", cascade="all, delete-orphan")

    @property
    def sources_limit(self) -> "int | None":
        """Limite de sources actuelle de ce compte, tranches supplémentaires incluses."""
        plan_value = self.plan.value if hasattr(self.plan, "value") else self.plan
        return effective_limit(plan_value, self.extra_tranches)


class Source(Base):
    """Une source surveillée : un document ou une page (CGV, tarifs...) d'un fournisseur."""

    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    supplier_name = Column(String, nullable=False)
    label = Column(String, nullable=True)  # ex. "CGV", "Grille tarifaire"
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)

    owner = relationship("User", back_populates="sources")
    snapshots = relationship(
        "Snapshot", back_populates="source", cascade="all, delete-orphan", order_by="Snapshot.captured_at"
    )
    changes = relationship(
        "Change", back_populates="source", cascade="all, delete-orphan", order_by="Change.detected_at.desc()"
    )


class Snapshot(Base):
    """Le contenu textuel capturé à un instant T pour une source."""

    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=_now)

    source = relationship("Source", back_populates="snapshots")


class Change(Base):
    """Un changement détecté entre deux snapshots, avec sa classification et son résumé."""

    __tablename__ = "changes"

    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    previous_snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=True)
    new_snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)

    diff_text = Column(Text, nullable=False)  # diff brut, format unifié (avant/après)
    category = Column(Enum(ChangeCategory), default=ChangeCategory.autre)
    severity = Column(Enum(ChangeSeverity), default=ChangeSeverity.info)
    summary = Column(Text, nullable=True)  # résumé en langage clair généré par l'IA

    detected_at = Column(DateTime, default=_now)

    source = relationship("Source", back_populates="changes")
