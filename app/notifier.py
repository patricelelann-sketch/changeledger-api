"""Envoi d'alertes email lors de la détection d'un changement significatif.

Utilise l'API HTTP de Resend (https://resend.com) via httpx, déjà une dépendance
du projet — pas besoin d'ajouter un SDK supplémentaire.
"""
from . import models
from .config import ALERT_FROM_EMAIL, PASSWORD_RESET_EXPIRE_MINUTES, RESEND_API_KEY

import httpx

SEVERITY_LABELS = {
    "urgent": "Urgent",
    "attention": "À vérifier",
    "info": "Info",
}


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
    html = (
        f"<p><strong>{label}</strong> sur <strong>{source.supplier_name}</strong>"
        f" ({source.label or 'source surveillée'}) :</p>"
        f"<p>{change.summary or 'Changement détecté (résumé indisponible).'}</p>"
        f"<p><a href=\"{source.url}\">Voir la source</a></p>"
    )
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": ALERT_FROM_EMAIL, "to": [to_email], "subject": subject, "html": html},
            timeout=10,
        )
    except Exception:  # noqa: BLE001 - une alerte en échec ne doit jamais bloquer la détection
        pass


def send_password_reset_email(to_email: str, token: str) -> None:
    """Envoie le jeton de réinitialisation de mot de passe par email.

    Même logique de repli que send_change_alert : une erreur d'envoi ne doit jamais
    faire échouer bruyamment /auth/forgot-password (qui répond toujours un message
    générique, qu'un compte existe ou non, pour ne pas révéler les emails inscrits).
    """
    if not RESEND_API_KEY:
        return
    subject = "[ChangeLedger] Réinitialisation de votre mot de passe"
    html = (
        "<p>Vous avez demandé la réinitialisation de votre mot de passe ChangeLedger.</p>"
        f"<p>Utilisez ce code pour le réinitialiser (valable {PASSWORD_RESET_EXPIRE_MINUTES} minutes) "
        f"avec l'endpoint <code>POST /auth/reset-password</code> :</p>"
        f"<p><code>{token}</code></p>"
        "<p>Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email : "
        "votre mot de passe ne sera pas modifié.</p>"
    )
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": ALERT_FROM_EMAIL, "to": [to_email], "subject": subject, "html": html},
            timeout=10,
        )
    except Exception:  # noqa: BLE001 - un échec d'envoi ne doit jamais bloquer le flux
        pass
