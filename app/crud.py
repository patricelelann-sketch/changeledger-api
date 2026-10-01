"""Opérations de base de données (CRUD) pour sources, snapshots et changements."""
from typing import Optional

from sqlalchemy.orm import Session

from . import models


def create_source(db: Session, supplier_name: str, label: Optional[str], url: str) -> models.Source:
    source = models.Source(supplier_name=supplier_name, label=label, url=url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def list_sources(db: Session) -> list[models.Source]:
    return db.query(models.Source).order_by(models.Source.created_at.desc()).all()


def get_source(db: Session, source_id: str) -> Optional[models.Source]:
    return db.query(models.Source).filter(models.Source.id == source_id).first()


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


def list_changes(db: Session, source_id: Optional[str] = None) -> list[models.Change]:
    query = db.query(models.Change)
    if source_id:
        query = query.filter(models.Change.source_id == source_id)
    return query.order_by(models.Change.detected_at.desc()).all()


def get_change(db: Session, change_id: str) -> Optional[models.Change]:
    return db.query(models.Change).filter(models.Change.id == change_id).first()
