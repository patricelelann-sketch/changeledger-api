"""Modèles de base de données : Source, Snapshot, Change."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
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


class Source(Base):
    """Une source surveillée : un document ou une page (CGV, tarifs...) d'un fournisseur."""

    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=_uuid)
    supplier_name = Column(String, nullable=False)
    label = Column(String, nullable=True)  # ex. "CGV", "Grille tarifaire"
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)

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
