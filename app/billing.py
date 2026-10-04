"""Intégration Stripe : Checkout, portail client, et traitement des webhooks."""
from typing import Optional

import stripe
from fastapi import HTTPException

from . import crud, models
from .config import (
    STRIPE_PRICE_ESSENTIEL,
    STRIPE_PRICE_PRO,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)

stripe.api_key = STRIPE_SECRET_KEY

PRICE_BY_PLAN = {
    "essentiel": STRIPE_PRICE_ESSENTIEL,
    "pro": STRIPE_PRICE_PRO,
}


def _require_stripe_configured() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe n'est pas configuré (STRIPE_SECRET_KEY manquante).",
        )


def create_checkout_session(user: models.User, plan: str, success_url: str, cancel_url: str) -> str:
    """Crée une session Stripe Checkout pour un palier (essentiel ou pro) et renvoie son URL."""
    _require_stripe_configured()
    price_id = PRICE_BY_PLAN.get(plan)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="Palier inconnu ou non disponible en self-service (attendu : essentiel ou pro).",
        )

    session_kwargs = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": user.id,
        "metadata": {"user_id": user.id, "plan": plan},
    }
    if user.stripe_customer_id:
        session_kwargs["customer"] = user.stripe_customer_id
    else:
        session_kwargs["customer_email"] = user.email

    session = stripe.checkout.Session.create(**session_kwargs)
    return session.url


def create_portal_session(user: models.User, return_url: str) -> str:
    """Crée un lien vers le portail client Stripe (gérer/annuler l'abonnement)."""
    _require_stripe_configured()
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Aucun abonnement Stripe associé à ce compte.")
    session = stripe.billing_portal.Session.create(customer=user.stripe_customer_id, return_url=return_url)
    return session.url


def construct_webhook_event(payload: bytes, signature: Optional[str]):
    _require_stripe_configured()
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET non configurée.")
    try:
        return stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail=f"Webhook Stripe invalide : {exc}")


def handle_webhook_event(db, event) -> None:
    """Met à jour le plan/abonnement de l'utilisateur en fonction de l'événement Stripe reçu."""
    event_type = event["type"]
    raw_data = event["data"]["object"]
    data = raw_data.to_dict() if hasattr(raw_data, "to_dict") else raw_data

    if event_type == "checkout.session.completed":
        user_id = data.get("client_reference_id") or (data.get("metadata") or {}).get("user_id")
        plan = (data.get("metadata") or {}).get("plan")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        if not user_id:
            return
        user = crud.get_user(db, user_id)
        if not user:
            return
        if customer_id and not user.stripe_customer_id:
            crud.set_user_stripe_customer(db, user, customer_id)
        crud.update_subscription(db, user, plan or user.plan, subscription_id, "active")

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = data.get("customer")
        if not customer_id:
            return
        user = crud.get_user_by_stripe_customer_id(db, customer_id)
        if not user:
            return
        status = data.get("status")  # active, past_due, canceled, incomplete...
        if event_type == "customer.subscription.deleted" or status == "canceled":
            crud.update_subscription(db, user, "none", None, "canceled")
        else:
            crud.update_subscription(db, user, user.plan, data.get("id"), status)
