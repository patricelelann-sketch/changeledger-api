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

# --- Authentification ---
# Secret utilisé pour signer les tokens JWT. À générer avec `openssl rand -hex 32`
# et à garder strictement privé. Une valeur par défaut est fournie pour le dev local
# uniquement : ne JAMAIS l'utiliser en production.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-ne-pas-utiliser-en-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 jours par défaut

# --- Cron externe (ex. cron-job.org) ---
# Secret partagé à fournir dans l'en-tête "X-Cron-Secret" pour appeler /check-all.
# Si non défini, /check-all reste ouvert sans protection (pratique en dev local).
CRON_SECRET = os.getenv("CRON_SECRET")

# --- Stripe ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ESSENTIEL = os.getenv("STRIPE_PRICE_ESSENTIEL")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")
# URLs de redirection après le paiement Stripe Checkout (pas encore de frontend :
# pointent par défaut vers la documentation interactive de l'API).
CHECKOUT_SUCCESS_URL = os.getenv("CHECKOUT_SUCCESS_URL", "/docs?checkout=success")
CHECKOUT_CANCEL_URL = os.getenv("CHECKOUT_CANCEL_URL", "/docs?checkout=cancel")
