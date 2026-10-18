"""Envoi d'alertes email lors de la détection d'un changement significatif.

Utilise l'API HTTP de Resend (https://resend.com) via httpx, déjà une dépendance
du projet — pas besoin d'ajouter un SDK supplémentaire.
"""
from . import models
from .config import ALERT_FROM_EMAIL, CONTACT_EMAIL, PASSWORD_RESET_EXPIRE_MINUTES, RESEND_API_KEY

import httpx

SEVERITY_LABELS = {
    "urgent": "Urgent",
    "attention": "À vérifier",
    "info": "Info",
}

# Identité visuelle ChangeLedger, reprise dans les emails (cohérente avec app_ui.py,
# admin_ui.py et legal_pages.py) : accent violet de marque + typographie système
# (les polices web ne sont pas fiables dans les clients email).
BRAND_ACCENT = "#4B3FF2"
BRAND_INK = "#12131A"
EMAIL_FONT = "-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif"


def _wrap_email(body_html: str) -> str:
    """Enveloppe le contenu d'un email dans l'habillage ChangeLedger (logo, couleurs)."""
    return (
        f'<div style="font-family: {EMAIL_FONT}; color: {BRAND_INK}; max-width: 520px; margin: 0 auto;">'
        f'<div style="font-size: 20px; font-weight: 700; margin-bottom: 20px;">'
        f'Change<span style="color: {BRAND_ACCENT}">Ledger</span></div>'
        f'{body_html}'
        '</div>'
    )


def _email_button(href: str, label: str) -> str:
    return (
        f'<p><a href="{href}" style="display: inline-block; padding: 11px 20px; '
        f'background: {BRAND_ACCENT}; color: #ffffff; border-radius: 6px; '
        f'font-weight: 600; text-decoration: none;">{label}</a></p>'
    )


def send_change_alert(to_email: str, source: models.Source, change: models.Change) -> None:
    """Envoie un email d'alerte pour un changement détecté chez un fournisseur surveillé.

    N'échoue jamais bruyamment : comme pour l'appel à Claude dans analyzer.py, une alerte
    non envoyée (clé manquante, Resend indisponible...) ne doit jamais faire échouer la
    vérification elle-même — mieux vaut un changement détecté sans email qu'une détection
    bloquée.
    """
    if not RESEND_API_KEY:
        return  # alertes email non configurées : on se tait silencieusement

    severity_value = change.severity.value if hasattr(change.severity, "value") else change.severity
    label = SEVERITY_LABELS.get(severity_value, severity_value)
    subject = f"[ChangeLedger] {label} — changement détecté chez {source.supplier_name}"
    html = _wrap_email(
        f"<p><strong style=\"color: {BRAND_ACCENT}\">{label}</strong> sur <strong>{source.supplier_name}</strong>"
        f" ({source.label or 'source surveillée'}) :</p>"
        f"<p>{change.summary or 'Changement détecté (résumé indisponible).'}</p>"
        + _email_button(source.url, "Voir la source")
    )
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": ALERT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "reply_to": CONTACT_EMAIL,
            },
            timeout=10,
        )
    except Exception:  # noqa: BLE001 - une alerte en échec ne doit jamais bloquer la détection
        pass


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Envoie le lien de réinitialisation de mot de passe par email.

    Même logique de repli que send_change_alert : une erreur d'envoi ne doit jamais
    faire échouer bruyamment /auth/forgot-password (qui répond toujours un message
    générique, qu'un compte existe ou non, pour ne pas révéler les emails inscrits).
    """
    if not RESEND_API_KEY:
        return
    subject = "[ChangeLedger] Réinitialisation de votre mot de passe"
    html = _wrap_email(
        "<p>Vous avez demandé la réinitialisation de votre mot de passe ChangeLedger.</p>"
        + _email_button(reset_link, "Choisir un nouveau mot de passe")
        + f"<p style=\"font-size: 0.9em; color: #5B5E6B\">Valable {PASSWORD_RESET_EXPIRE_MINUTES} minutes. "
        "Si le bouton ne fonctionne pas, copiez-collez cette adresse dans votre navigateur :<br>"
        f"<code>{reset_link}</code></p>"
        "<p>Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email : "
        "votre mot de passe ne sera pas modifié.</p>"
    )
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": ALERT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "reply_to": CONTACT_EMAIL,
            },
            timeout=10,
        )
    except Exception:  # noqa: BLE001 - un échec d'envoi ne doit jamais bloquer le flux
        pass


def send_welcome_email(to_email: str, app_url: str) -> None:
    """Envoie un email de bienvenue à la création d'un compte.

    Rappelle les grandes lignes du service et renvoie vers l'application — le nouveau
    compte est toujours au palier "Aucun" à ce stade (aucune source possible avant de
    souscrire), donc l'email inclut un rappel explicite et un lien vers la page Compte
    plutôt qu'un état d'abonnement à afficher. Même logique de repli que les autres
    fonctions de ce module : un échec d'envoi ne doit jamais faire échouer l'inscription.
    """
    if not RESEND_API_KEY:
        return
    subject = "Bienvenue sur ChangeLedger"
    html = _wrap_email(
        "<p>Bienvenue sur ChangeLedger !</p>"
        "<p>ChangeLedger surveille pour toi les conditions de tes fournisseurs (CGV, "
        "grilles tarifaires, contrats accessibles en ligne) : dès qu'un changement est "
        "détecté, il est classé par catégorie et sévérité, résumé en langage clair, et "
        "tu reçois une alerte par email (et, si tu le souhaites, sur un webhook Slack, "
        "Zapier ou maison).</p>"
        "<p>Pour commencer :</p>"
        "<ol>"
        "<li>Choisis un palier (Essentiel ou Pro) depuis l'onglet 'Compte' — un essai "
        "de 14 jours est inclus, résiliable à tout moment.</li>"
        "<li>Ajoute les pages à surveiller depuis l'onglet 'Sources'.</li>"
        "<li>C'est tout : ChangeLedger s'occupe du reste.</li>"
        "</ol>"
        + _email_button(f"{app_url}/app", "Accéder à mon compte")
        + "<p style='color:#8A8D99;font-size:0.9em'>Des questions ? Réponds simplement à "
        "cet email.</p>"
    )
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": ALERT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "reply_to": CONTACT_EMAIL,
            },
            timeout=10,
        )
    except Exception:  # noqa: BLE001 - un échec d'envoi ne doit jamais bloquer l'inscription
        pass


def send_change_webhook(webhook_url, source: models.Source, change: models.Change) -> None:
    """Envoie une alerte de changement sur le webhook configuré par l'utilisateur
    (Slack, Zapier, système interne...), en complément de l'email.

    Le payload est au format attendu par les webhooks entrants Slack (clé "text"),
    que Slack affiche directement ; les receveurs génériques (Zapier, endpoint maison)
    peuvent utiliser ce même champ ou lire les objets "source"/"change" structurés.

    Même logique de repli que les autres fonctions de ce module : une erreur d'envoi
    (URL injoignable, webhook supprimé côté destinataire...) ne doit jamais faire
    échouer la détection de changement elle-même.
    """
    if not webhook_url:
        return

    severity_value = change.severity.value if hasattr(change.severity, "value") else change.severity
    category_value = change.category.value if hasattr(change.category, "value") else change.category
    label = SEVERITY_LABELS.get(severity_value, severity_value)

    text = (
        f"[{label}] Changement détecté chez {source.supplier_name}"
        f" ({source.label or 'source surveillée'}) : "
        f"{change.summary or 'résumé indisponible'}"
    )

    payload = {
        "text": text,
        "source": {
            "id": source.id,
            "supplier_name": source.supplier_name,
            "label": source.label,
            "url": source.url,
        },
        "change": {
            "id": change.id,
            "category": category_value,
            "severity": severity_value,
            "summary": change.summary,
        },
    }

    try:
        httpx.post(webhook_url, json=payload, timeout=10)
    except Exception:  # noqa: BLE001 - un échec d'envoi ne doit jamais bloquer la détection
        pass
