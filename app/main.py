"""ChangeLedger API — moteur de veille des conditions fournisseurs.

Comptes utilisateurs (JWT) et facturation (Stripe, paliers Essentiel/Pro/Entreprise)
ajoutés au-dessus du moteur de veille V1. Chaque source surveillée appartient à un
utilisateur ; /check-all reste un endpoint système protégé par un secret partagé
(CRON_SECRET), destiné à un planificateur externe (ex. cron-job.org).
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from . import auth, billing, crud, models, notifier, schemas
from .admin_ui import ADMIN_UI_HTML
from .app_ui import APP_UI_HTML
from .landing_page import LANDING_HTML
from .legal_pages import CGU_HTML, CGV_HTML, PRIVACY_HTML
from .analyzer import analyze_change
from .config import CHECKOUT_CANCEL_URL, CHECKOUT_SUCCESS_URL, PASSWORD_RESET_EXPIRE_MINUTES
from .database import Base, engine, get_db
from .differ import compute_diff, content_hash
from .fetcher import fetch_text
from .models import PLAN_LIMITS

# Favicon : version compacte du wordmark (monogramme "C"), même couleur d'accent
# de marque que l'app, l'admin et les pages légales (app_ui.py, admin_ui.py,
# legal_pages.py, notifier.py).
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#4B3FF2"/>'
    '<text x="32" y="43" font-family="\'Space Grotesk\', system-ui, sans-serif" '
    'font-size="34" font-weight="700" fill="#FFFFFF" text-anchor="middle">C</text>'
    '</svg>'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ChangeLedger API",
    description="Veille des conditions fournisseurs (CGV, tarifs, contrats).",
    version="0.2.0",
    lifespan=lifespan,
)

# Fait confiance aux en-têtes X-Forwarded-For/X-Forwarded-Proto envoyés par le proxy de
# Railway, pour que request.client.host (utilisé par la limitation de débit ci-dessous)
# reflète la vraie IP du client plutôt que l'IP interne du réseau de Railway. Configuré en
# code plutôt que via le flag --proxy-headers du Procfile, pour éviter tout souci
# d'interprétation des guillemets selon la façon dont la commande est exécutée.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Limitation de débit (en mémoire, par IP) sur les endpoints d'authentification exposés
# sans secret ni session — cibles naturelles de spam de comptes, force brute, ou bombardement
# d'emails de réinitialisation. En mémoire : suffisant tant que l'API tourne sur une seule
# instance Railway (pas de stockage partagé type Redis pour l'instant).
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Trop de tentatives. Réessaie dans quelques instants."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


MARKETING_HOSTS = {"changeledger.io", "www.changeledger.io"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root(request: Request):
    """Sert la page marketing sur le domaine racine (changeledger.io) ; redirige
    vers l'application sur tout autre domaine (app.changeledger.io, l'URL Railway,
    etc.) — un seul service derrière les deux domaines, le routage se fait sur le
    header Host de la requête."""
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host in MARKETING_HOSTS:
        return HTMLResponse(LANDING_HTML)
    return RedirectResponse(url="/app")


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
def frontend_app():
    """Frontend minimal (inscription/connexion, sources, changements, compte)."""
    return APP_UI_HTML


@app.get("/legal/cgu", response_class=HTMLResponse, include_in_schema=False)
def legal_cgu():
    """Conditions générales d'utilisation."""
    return CGU_HTML


@app.get("/legal/cgv", response_class=HTMLResponse, include_in_schema=False)
def legal_cgv():
    """Conditions générales de vente."""
    return CGV_HTML


@app.get("/legal/confidentialite", response_class=HTMLResponse, include_in_schema=False)
def legal_confidentialite():
    """Politique de confidentialité (RGPD)."""
    return PRIVACY_HTML


# --- Authentification ---

@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
@limiter.limit("5/hour")
def signup(payload: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email.")
    user = crud.create_user(db, payload.email, auth.hash_password(payload.password))
    base_url = str(request.base_url).rstrip("/")
    notifier.send_welcome_email(user.email, base_url)
    return user


@app.post("/auth/login", response_model=schemas.Token)
@limiter.limit("10/minute")
def login(payload: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return schemas.Token(access_token=auth.create_access_token(user.id))


@app.get("/auth/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/auth/forgot-password")
@limiter.limit("5/hour")
def forgot_password(
    payload: schemas.ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)
):
    """Déclenche l'envoi d'un lien de réinitialisation si le compte existe.

    Répond toujours le même message générique, que l'email corresponde à un compte ou non,
    pour ne pas permettre de découvrir quels emails sont inscrits (énumération de comptes).
    """
    user = crud.get_user_by_email(db, payload.email)
    if user:
        token = auth.create_reset_token()
        expires_at = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
        crud.set_reset_token(db, user, token, expires_at)
        base_url = str(request.base_url).rstrip("/")
        reset_link = f"{base_url}/app?token={token}"
        notifier.send_password_reset_email(user.email, reset_link)
    return {"message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."}


@app.post("/auth/reset-password")
def reset_password_endpoint(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_reset_token(db, payload.token)
    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code de réinitialisation invalide ou expiré.")
    crud.reset_password(db, user, auth.hash_password(payload.new_password))
    return {"message": "Mot de passe réinitialisé avec succès."}


@app.put("/auth/webhook", response_model=schemas.UserOut)
def set_webhook(
    payload: schemas.WebhookRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Enregistre (ou efface, en envoyant webhook_url: null) l'URL de webhook de l'utilisateur
    connecté — reçoit une copie de chaque alerte de changement, en plus de l'email."""
    return crud.set_webhook_url(db, current_user, payload.webhook_url)


# --- Facturation ---

@app.post("/billing/checkout", response_model=schemas.CheckoutResponse)
def create_checkout(
    payload: schemas.CheckoutRequest,
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
):
    if payload.plan not in ("essentiel", "pro"):
        raise HTTPException(
            status_code=400,
            detail="Palier invalide pour un paiement en ligne (essentiel ou pro). "
            "Le palier Entreprise s'active via contact commercial.",
        )
    base_url = str(request.base_url).rstrip("/")
    success_url = CHECKOUT_SUCCESS_URL if CHECKOUT_SUCCESS_URL.startswith("http") else base_url + CHECKOUT_SUCCESS_URL
    cancel_url = CHECKOUT_CANCEL_URL if CHECKOUT_CANCEL_URL.startswith("http") else base_url + CHECKOUT_CANCEL_URL
    url = billing.create_checkout_session(
        current_user, payload.plan, payload.cycle, success_url, cancel_url
    )
    return schemas.CheckoutResponse(checkout_url=url)


@app.get("/billing/portal", response_model=schemas.PortalResponse)
def billing_portal(request: Request, current_user: models.User = Depends(auth.get_current_user)):
    base_url = str(request.base_url).rstrip("/")
    url = billing.create_portal_session(current_user, return_url=base_url + "/app")
    return schemas.PortalResponse(portal_url=url)


@app.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    event = billing.construct_webhook_event(payload, signature)
    billing.handle_webhook_event(db, event)
    return {"received": True}


# --- Administration ---
# Protégé par ADMIN_SECRET (en-tête X-Admin-Secret), sur le même principe que CRON_SECRET
# pour /check-all. Sert notamment à activer manuellement le palier Entreprise après un
# contact commercial, puisqu'il n'est pas proposé en self-service Stripe.

@app.get("/admin/ui", response_class=HTMLResponse, include_in_schema=False)
def admin_ui():
    """Petite interface web (liste des comptes + changement de palier), en remplacement
    des commandes curl sur /admin/*. Pas de protection sur la page elle-même : le secret
    admin est saisi dans le navigateur et envoyé en en-tête à chaque appel API, exactement
    comme pour les commandes curl équivalentes."""
    return ADMIN_UI_HTML


@app.get("/admin/users", response_model=list[schemas.UserOut], dependencies=[Depends(auth.verify_admin_secret)])
def admin_list_users(db: Session = Depends(get_db)):
    """Liste tous les comptes, pour éviter de passer par la console Postgres de Railway."""
    return crud.list_users(db)


@app.post(
    "/admin/users/plan", response_model=schemas.UserOut, dependencies=[Depends(auth.verify_admin_secret)]
)
def admin_set_plan(payload: schemas.AdminSetPlanRequest, db: Session = Depends(get_db)):
    """Change manuellement le palier d'un utilisateur identifié par son email."""
    user = crud.get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Aucun compte avec cet email.")
    return crud.set_plan(db, user, payload.plan)


@app.delete("/admin/users", dependencies=[Depends(auth.verify_admin_secret)])
def admin_delete_user(payload: schemas.AdminDeleteUserRequest, db: Session = Depends(get_db)):
    """Supprime définitivement un compte (et ses sources/changements) identifié par son email —
    pour nettoyer un compte de test, ou répondre à une demande de suppression de compte (droit
    RGPD à l'effacement). Ne touche pas à Stripe : pense à annuler/supprimer séparément
    l'abonnement ou le client côté Stripe si besoin."""
    user = crud.get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Aucun compte avec cet email.")
    crud.delete_user(db, user)
    return {"message": f"Compte {payload.email} supprimé."}


# --- Sources (scopées à l'utilisateur connecté) ---

@app.post("/sources", response_model=schemas.SourceOut)
def add_source(
    payload: schemas.SourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    limit = PLAN_LIMITS.get(current_user.plan.value if hasattr(current_user.plan, "value") else current_user.plan)
    if limit is not None and crud.count_sources_for_user(db, current_user.id) >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Limite de {limit} sources atteinte pour votre palier actuel. "
            "Passez à un palier supérieur pour en surveiller davantage.",
        )
    return crud.create_source(db, current_user.id, payload.supplier_name, payload.label, str(payload.url))


@app.get("/sources", response_model=list[schemas.SourceOut])
def get_sources(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.list_sources(db, current_user.id)


@app.get("/sources/{source_id}", response_model=schemas.SourceOut)
def get_source(
    source_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    source = crud.get_source(db, current_user.id, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    return source


@app.delete("/sources/{source_id}", status_code=204)
def remove_source(
    source_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    source = crud.get_source(db, current_user.id, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    crud.delete_source(db, source)


@app.post("/sources/{source_id}/check", response_model=schemas.CheckResult)
async def check_source(
    source_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    source = crud.get_source(db, current_user.id, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable.")
    return await _check_one(db, source)


@app.post("/check-all", response_model=list[schemas.CheckResult], dependencies=[Depends(auth.verify_cron_secret)])
async def check_all(db: Session = Depends(get_db)):
    """Endpoint système (protégé par CRON_SECRET) à brancher sur un planificateur externe
    (ex. cron-job.org) pour une veille automatique — vérifie les sources de tous les utilisateurs."""
    return [await _check_one(db, source) for source in crud.list_all_sources(db)]


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
    if change.severity in (models.ChangeSeverity.urgent, models.ChangeSeverity.attention):
        notifier.send_change_alert(source.owner.email, source, change)
        notifier.send_change_webhook(source.owner.webhook_url, source, change)
    return schemas.CheckResult(
        source_id=source.id,
        changed=True,
        change=change,
        message="Changement détecté et analysé.",
    )


@app.get("/changes", response_model=list[schemas.ChangeOut])
def get_changes(
    source_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.list_changes(db, current_user.id, source_id)


@app.get("/changes/{change_id}", response_model=schemas.ChangeOut)
def get_change(
    change_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    change = crud.get_change(db, current_user.id, change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Changement introuvable.")
    return change
