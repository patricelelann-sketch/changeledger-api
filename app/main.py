"""ChangeLedger API — moteur de veille des conditions fournisseurs (V1).

Périmètre de cette première version :
- Ajouter une source à surveiller (URL d'une page de CGV ou de tarifs)
- Déclencher une vérification (manuelle via /sources/{id}/check, ou groupée via
  /check-all — à brancher sur un planificateur externe, ex. Railway Cron)
- Détecter un changement de contenu, le classifier et en résumer l'impact via Claude
- Consulter l'historique des changements détectés

Volontairement hors périmètre de cette V1 (voir README) : comptes utilisateurs,
facturation, alertes email/Slack automatiques, import de PDF ou de contrats signés.
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .analyzer import analyze_change
from .database import Base, engine, get_db
from .differ import compute_diff, content_hash
from .fetcher import fetch_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ChangeLedger API",
    description="Veille des conditions fournisseurs (CGV, tarifs, contrats).",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sources", response_model=schemas.SourceOut)
def add_source(payload: schemas.SourceCreate, db: Session = Depends(get_db)):
    return crud.create_source(db, payload.supplier_name, payload.label, str(payload.url))


@app.get("/sources", response_model=list[schemas.SourceOut])
def get_sources(db: Session = Depends(get_db)):
    return crud.list_sources(db)


@app.get("/sources/{source_id}", response_model=schemas.SourceOut)
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    return source


@app.delete("/sources/{source_id}", status_code=204)
def remove_source(source_id: str, db: Session = Depends(get_db)):
    source = crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    crud.delete_source(db, source)


@app.post("/sources/{source_id}/check", response_model=schemas.CheckResult)
async def check_source(source_id: str, db: Session = Depends(get_db)):
    source = crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    return await _check_one(db, source)


@app.post("/check-all", response_model=list[schemas.CheckResult])
async def check_all(db: Session = Depends(get_db)):
    """À brancher sur un planificateur externe (ex. Railway Cron) pour une veille automatique."""
    return [await _check_one(db, source) for source in crud.list_sources(db)]


async def _check_one(db: Session, source: models.Source) -> schemas.CheckResult:
    try:
        current_text = await fetch_text(source.url)
    except Exception as exc:  # noqa: BLE001 - une source en échec ne doit pas bloquer les autres
        return schemas.CheckResult(
            source_id=source.id,
            changed=False,
            message=f"Échec de récupération de la source : {exc}",
        )

    previous = crud.latest_snapshot(db, source.id)
    new_hash = content_hash(current_text)

    if previous and previous.content_hash == new_hash:
        return schemas.CheckResult(source_id=source.id, changed=False, message="Aucun changement détecté.")

    new_snapshot = crud.create_snapshot(db, source.id, current_text, new_hash)

    if not previous:
        return schemas.CheckResult(
            source_id=source.id,
            changed=False,
            message="Première capture enregistrée (rien à comparer encore).",
        )

    diff = compute_diff(previous.content, current_text)
    if not diff.is_significant:
        return schemas.CheckResult(
            source_id=source.id,
            changed=False,
            message="Changement détecté mais jugé non significatif (espaces, détail mineur).",
        )

    analysis = analyze_change(diff.diff_text)
    change = crud.create_change(
        db,
        source_id=source.id,
        previous_snapshot_id=previous.id,
        new_snapshot_id=new_snapshot.id,
        diff_text=diff.diff_text,
        category=analysis.get("category", "autre"),
        severity=analysis.get("severity", "attention"),
        summary=analysis.get("summary", ""),
    )
    return schemas.CheckResult(
        source_id=source.id,
        changed=True,
        change=change,
        message="Changement détecté et analysé.",
    )


@app.get("/changes", response_model=list[schemas.ChangeOut])
def get_changes(source_id: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.list_changes(db, source_id)


@app.get("/changes/{change_id}", response_model=schemas.ChangeOut)
def get_change(change_id: str, db: Session = Depends(get_db)):
    change = crud.get_change(db, change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Changement introuvable.")
    return change
