"""Classification et résumé en langage clair d'un changement détecté, via Claude."""
import json
from typing import Optional

from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_client: Optional[Anthropic] = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY n'est pas configurée. "
                "Ajoutez-la comme variable d'environnement (voir .env.example)."
            )
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


ANALYSIS_PROMPT = """Tu analyses un changement détecté dans les conditions générales de vente \
ou le contrat d'un fournisseur. Voici le diff (format unifié : les lignes commençant par -\
sont supprimées, celles commençant par + sont ajoutées) :

{diff_text}

Réponds UNIQUEMENT avec un objet JSON de cette forme, sans texte autour :
{{
  "category": "tarif" | "resiliation" | "paiement" | "responsabilite" | "autre",
  "severity": "info" | "attention" | "urgent",
  "summary": "une phrase en français clair, compréhensible par un non-juriste, qui explique \
ce qui change concrètement et son impact probable pour le client du fournisseur"
}}

"severity" vaut "urgent" si le changement est manifestement défavorable au client (hausse de \
prix, durcissement d'une clause de résiliation ou de responsabilité), "attention" s'il mérite \
d'être vérifié, "info" s'il est probablement neutre ou cosmétique."""


def analyze_change(diff_text: str) -> dict:
    """Appelle Claude pour classifier le changement et en résumer l'impact.

    En cas d'erreur d'appel IA, renvoie un résultat de repli neutre plutôt que de
    faire échouer toute la détection : mieux vaut une alerte non classifiée
    qu'une alerte perdue.
    """
    try:
        client = _get_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(diff_text=diff_text[:6000])}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - on isole volontairement toute panne IA
        return {
            "category": "autre",
            "severity": "attention",
            "summary": f"Changement détecté mais non classifié automatiquement ({exc}). "
            "Vérification manuelle recommandée.",
        }
