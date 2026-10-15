"""Envoi d'alertes email lors de la détection d'un changement significatif.

Utilise l'API HTTP de Resend (https://resend.com) via httpx, déjà une dépendance
du projet — pas besoin d'ajouter un SDK supplémentaire.
"""
from . import models
from .config import ALERT_FROM_EMAIL, RESEND_API_KEY

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
