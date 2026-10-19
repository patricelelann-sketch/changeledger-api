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

# Durée de validité d'un jeton de réinitialisation de mot de passe, en minutes.
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))

# --- Cron externe (ex. cron-job.org) ---
# Secret partagé à fournir dans l'en-tête "X-Cron-Secret" pour appeler /check-all.
# Si non défini, /check-all reste ouvert sans protection (pratique en dev local).
CRON_SECRET = os.getenv("CRON_SECRET")

# --- Administration ---
# Secret partagé à fournir dans l'en-tête "X-Admin-Secret" pour appeler les endpoints /admin/*
# (notamment l'activation manuelle du palier Entreprise après contact commercial).
# Contrairement à CRON_SECRET, pas de mode "ouvert" : si ADMIN_SECRET n'est pas défini,
# les endpoints /admin/* refusent tout appel (403).
ADMIN_SECRET = os.getenv("ADMIN_SECRET")

# --- Alertes email (via l'API HTTP de Resend : https://resend.com) ---
# Si RESEND_API_KEY n'est pas définie, les alertes sont simplement désactivées
# (aucun email envoyé, mais la détection de changement continue de fonctionner normalement).
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# Adresse expéditrice des alertes. Doit appartenir à un domaine vérifié dans Resend.
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "alerts@changeledger.app")
# Adresse de contact officielle (mentions légales, reply-to des emails sortants) —
# distincte d'ALERT_FROM_EMAIL : celle-ci est une vraie boîte surveillée, l'autre
# une adresse technique d'envoi côté domaine vérifié Resend.
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@changeledger.io")

# --- Stripe ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
# Un prix Stripe distinct par palier ET par cycle de facturation (mensuel/annuel),
# pour laisser le client choisir sa périodicité à la souscription.
STRIPE_PRICE_ESSENTIEL_MONTHLY = os.getenv("STRIPE_PRICE_ESSENTIEL_MONTHLY")
STRIPE_PRICE_ESSENTIEL_ANNUAL = os.getenv("STRIPE_PRICE_ESSENTIEL_ANNUAL")
STRIPE_PRICE_PRO_MONTHLY = os.getenv("STRIPE_PRICE_PRO_MONTHLY")
STRIPE_PRICE_PRO_ANNUAL = os.getenv("STRIPE_PRICE_PRO_ANNUAL")
# Tranches supplémentaires de fournisseurs (self-service, en plus du quota de base du
# palier) : un prix Stripe par palier ET par cycle, comme pour les paliers eux-mêmes.
STRIPE_PRICE_ESSENTIEL_TRANCHE_MONTHLY = os.getenv("STRIPE_PRICE_ESSENTIEL_TRANCHE_MONTHLY")
STRIPE_PRICE_ESSENTIEL_TRANCHE_ANNUAL = os.getenv("STRIPE_PRICE_ESSENTIEL_TRANCHE_ANNUAL")
STRIPE_PRICE_PRO_TRANCHE_MONTHLY = os.getenv("STRIPE_PRICE_PRO_TRANCHE_MONTHLY")
STRIPE_PRICE_PRO_TRANCHE_ANNUAL = os.getenv("STRIPE_PRICE_PRO_TRANCHE_ANNUAL")
# URLs de redirection après le paiement Stripe Checkout : pointent par défaut vers
# le frontend (onglet Compte, qui affiche un message de succès/annulation).
CHECKOUT_SUCCESS_URL = os.getenv("CHECKOUT_SUCCESS_URL", "/app?checkout=success")
CHECKOUT_CANCEL_URL = os.getenv("CHECKOUT_CANCEL_URL", "/app?checkout=cancel")
