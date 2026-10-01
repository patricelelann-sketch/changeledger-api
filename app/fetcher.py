"""Récupération et nettoyage du contenu d'une source surveillée.

Limite assumée de cette V1 : pages web (HTML) et texte brut uniquement.
Le support des PDF et des documents contractuels importés est prévu pour
une version ultérieure — voir le README.
"""
import httpx
from bs4 import BeautifulSoup

USER_AGENT = "ChangeLedgerBot/0.1 (+https://changeledger.example)"


async def fetch_text(url: str) -> str:
    """Télécharge l'URL donnée et retourne son texte visible, nettoyé du HTML."""
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        # Texte brut ou type non-HTML : renvoyé tel quel, normalisé.
        return response.text.strip()

    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
