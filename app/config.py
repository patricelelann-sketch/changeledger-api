"""Chargement de la configuration depuis les variables d'environnement.

En local, un fichier .env (non commité) peut fournir ces valeurs.
Sur Railway, elles se définissent directement dans les Variables du service.
"""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./changeledger.db")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
