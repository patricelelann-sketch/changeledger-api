"""Intégration Stripe : Checkout, portail client, et traitement des webhooks."""
from typing import Optional

import stripe
from fastapi import HTTPException

from . import crud, models
from .config import (
    STRIPE_PRICE_ESSENTIEL_ANNUAL,
    STRIPE_PRICE_ESSENTIEL_MONTHLY,
    STRIPE_PRICE_ESSENTIEL_TRANCHE_ANNUAL,
    STRIPE_PRICE_ESSENTIEL_TRANCHE_MONTHLY,
    STRIPE_PRICE_PRO_ANNUAL,
    STRIPE_PRICE_PRO_MONTHLY,
    STRIPE_PRICE_PRO_TRANCHE_ANNUAL,
    STRIPE_PRICE_PRO_TRANCHE_MONTHLY,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)

stripe.api_key = STRIPE_SECRET_KEY

# Période d'essai (en jours) accordée à toute souscription Essentiel/Pro. La carte bancaire
# est demandée dès l'inscription (Stripe Checkout standard) ; Stripe facture automatiquement
# à l'issue de l'essai sauf annulation. Choisie à 14 jours pour laisser le temps à un premier
# changement réel d'être détecté sur les sources surveillées.
TRIAL_PERIOD_DAYS = 14

# Un prix Stripe par palier ET par cycle de facturation (mensuel/annuel).
PRICE_BY_PLAN = {
    "essentiel": {"monthly": STRIPE_PRICE_ESSENTIEL_MONTHLY, "annual": STRIPE_PRICE_ESSENTIEL_ANNUAL},
    "pro": {"monthly": STRIPE_PRICE_PRO_MONTHLY, "annual": STRIPE_PRICE_PRO_ANNUAL},
}

# Même principe pour les tranches supplémentaires de fournisseurs (cf. models.TRANCHE_SIZE).
TRANCHE_PRICE_BY_PLAN = {
    "essentiel": {
        "monthly": STRIPE_PRICE_ESSENTIEL_TRANCHE_MONTHLY,
        "annual": STRIPE_PRICE_ESSENTIEL_TRANCHE_ANNUAL,
    },
    "pro": {"monthly": STRIPE_PRICE_PRO_TRANCHE_MONTHLY, "annual": STRIPE_PRICE_PRO_TRANCHE_ANNUAL},
}


def _require_stripe_configured() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe n'est pas configuré (STRIPE_SECRET_KEY manquante).",
        )


def create_checkout_session(
    user: models.User, plan: str, cycle: str, success_url: str, cancel_url: str
) -> str:
    """Crée une session Stripe Checkout pour un palier + cycle (mensuel/annuel) et renvoie son URL."""
    _require_stripe_configured()
    cycle = cycle if cycle in ("monthly", "annual") else "monthly"
    price_id = PRICE_BY_PLAN.get(plan, {}).get(cycle)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="Palier ou cycle de facturation inconnu, ou non disponible en self-service "
            "(palier attendu : essentiel ou pro ; cycle attendu : monthly ou annual).",
        )

    session_kwargs = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": user.id,
        "metadata": {"user_id": user.id, "plan": plan, "cycle": cycle},
        "subscription_data": {"trial_period_days": TRIAL_PERIOD_DAYS},
    }
    if user.stripe_customer_id:
        session_kwargs["customer"] = user.stripe_customer_id
    else:
        session_kwargs["customer_email"] = user.email

    session = stripe.checkout.Session.create(**session_kwargs)
    return session.url


def _billing_cycle_of_subscription(subscription, plan: str) -> Optional[str]:
    """Détermine si un abonnement est mensuel ou annuel, en repérant lequel des deux prix de
    base du palier (cf. PRICE_BY_PLAN) figure parmi ses lignes. Plus fiable que de lire
    l'intervalle du premier item, qui pourrait être une tranche plutôt que le prix de base."""
    base_prices = PRICE_BY_PLAN.get(plan, {})
    item_price_ids = {item["price"]["id"] for item in subscription["items"]["data"]}
    if base_prices.get("monthly") in item_price_ids:
        return "monthly"
    if base_prices.get("annual") in item_price_ids:
        return "annual"
    return None


def add_tranche(user: models.User) -> int:
    """Ajoute une tranche supplémentaire de fournisseurs (+1) à l'abonnement en cours de
    l'utilisateur, en incrémentant la quantité du prix de tranche correspondant à son palier
    et à son cycle de facturation (proration automatique par Stripe). Renvoie la nouvelle
    quantité totale de tranches sur l'abonnement."""
    _require_stripe_configured()
    plan = user.plan.value if hasattr(user.plan, "value") else user.plan
    if plan not in ("essentiel", "pro"):
        raise HTTPException(
            status_code=400,
            detail="Les tranches supplémentaires ne sont disponibles en self-service que pour "
            "les paliers Essentiel et Pro (le palier Entreprise est déjà illimité).",
        )
    if not user.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="Aucun abonnement actif pour ce compte.")

    subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
    cycle = _billing_cycle_of_subscription(subscription, plan)
    tranche_price_id = TRANCHE_PRICE_BY_PLAN.get(plan, {}).get(cycle or "monthly")
    if not tranche_price_id:
        raise HTTPException(
            status_code=503,
            detail="Le tarif de tranche supplémentaire n'est pas configuré pour ce palier/cycle.",
        )

    existing_item = next(
        (item for item in subscription["items"]["data"] if item["price"]["id"] == tranche_price_id),
        None,
    )
    if existing_item:
        new_quantity = existing_item["quantity"] + 1
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            items=[{"id": existing_item["id"], "quantity": new_quantity}],
        )
    else:
        new_quantity = 1
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            items=[{"price": tranche_price_id, "quantity": 1}],
        )
    return new_quantity


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


def _extract_tranche_quantity(items_data: list, plan: str) -> int:
    """Additionne la quantité de tranches supplémentaires présentes sur une liste d'items
    d'abonnement Stripe, pour un palier donné (il ne devrait y en avoir qu'un seul des deux
    prix mensuel/annuel à la fois, mais additionner les deux reste sûr dans tous les cas)."""
    tranche_price_ids = {pid for pid in TRANCHE_PRICE_BY_PLAN.get(plan, {}).values() if pid}
    return sum(item["quantity"] for item in items_data if item["price"]["id"] in tranche_price_ids)


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
        # Le statut réel (p. ex. "trialing" pendant la période d'essai, "active" sinon) est
        # récupéré auprès de Stripe plutôt que figé à "active" : avec l'essai de 14 jours, la
        # souscription créée au checkout est "trialing", pas "active".
        status = "active"
        subscription_obj = None
        if subscription_id:
            try:
                subscription_obj = stripe.Subscription.retrieve(subscription_id)
                status = subscription_obj.status
            except stripe.error.StripeError:
                pass
        final_plan = plan or user.plan
        crud.update_subscription(db, user, final_plan, subscription_id, status)
        if subscription_obj is not None:
            plan_value = final_plan.value if hasattr(final_plan, "value") else final_plan
            tranche_qty = _extract_tranche_quantity(subscription_obj["items"]["data"], plan_value)
            crud.set_extra_tranches(db, user, tranche_qty)

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
            crud.set_extra_tranches(db, user, 0)
        else:
            crud.update_subscription(db, user, user.plan, data.get("id"), status)
            # Synchronise les tranches supplémentaires depuis l'abonnement (source de vérité
            # Stripe) : couvre aussi bien l'ajout via /billing/add-tranche qu'une modification
            # faite directement depuis le portail client Stripe.
            plan_value = user.plan.value if hasattr(user.plan, "value") else user.plan
            items_data = (data.get("items") or {}).get("data", [])
            tranche_qty = _extract_tranche_quantity(items_data, plan_value)
            crud.set_extra_tranches(db, user, tranche_qty)
