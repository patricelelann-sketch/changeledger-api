# ChangeLedger API — V2 (comptes utilisateurs + facturation)

Moteur de veille des conditions fournisseurs : surveille une source (page de CGV,
grille tarifaire...), détecte les changements, les classe et en résume l'impact
en langage clair via Claude. Cette V2 ajoute les comptes utilisateurs (JWT) et
la facturation par abonnement (Stripe, paliers Essentiel / Pro / Entreprise).

## Périmètre

Inclus (V1 + V2) :
- Comptes utilisateurs : inscription/connexion par email + mot de passe (JWT),
  avec réinitialisation de mot de passe par email
- Chaque source surveillée appartient à un utilisateur (multi-tenant)
- Trois paliers d'abonnement : **Essentiel** (5 sources), **Pro** (25 sources),
  **Entreprise** (illimité, activé manuellement après contact commercial — pas
  de paiement en ligne pour ce palier)
- Paiement par abonnement via Stripe Checkout (Essentiel/Pro), mensuel ou annuel
  au choix, avec 14 jours d'essai (carte bancaire enregistrée dès l'inscription), +
  portail client Stripe pour gérer/annuler l'abonnement
- Ajouter / lister / supprimer une source à surveiller (URL)
- Déclencher une vérification manuelle, ou groupée pour toutes les sources
  (endpoint système `/check-all`, protégé par un secret de cron)
- Détection de changement (diff texte), filtrage des changements triviaux
- Classification + résumé de l'impact via l'API Anthropic (Claude)
- Historique consultable des changements détectés
- Email de bienvenue à l'inscription (présentation du service, rappel pour choisir un
  palier, lien vers l'application — via Resend)
- Alerte automatique par email au propriétaire du compte dès qu'un changement de
  sévérité "urgent" ou "attention" est détecté sur une de ses sources (via Resend)
- Webhook optionnel configurable par chaque utilisateur (self-service), reçoit une
  copie de chaque alerte en plus de l'email — compatible Slack Incoming Webhook
- Frontend minimal (`GET /app`) : inscription/connexion, gestion des sources et
  consultation de l'historique des changements, compte (palier, facturation, webhook,
  mot de passe) — voir la section dédiée ci-dessous
- Limitation de débit (par IP) sur les endpoints d'authentification exposés sans secret
  ni session (`/auth/signup`, `/auth/login`, `/auth/forgot-password`)
- CGU, CGV et politique de confidentialité (`/legal/cgu`, `/legal/cgv`,
  `/legal/confidentialite`), liées depuis le frontend — voir la section dédiée ci-dessous

Volontairement hors périmètre, à construire ensuite :
- Import de PDF et de contrats signés (seules les pages web texte/HTML sont supportées pour l'instant)

## Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Puis éditez .env : renseignez au minimum ANTHROPIC_API_KEY et JWT_SECRET_KEY
# (générez ce dernier avec `openssl rand -hex 32`)
```

Lancer le serveur :

```bash
uvicorn app.main:app --reload
```

L'API est alors disponible sur http://localhost:8000, avec une documentation
interactive auto-générée sur http://localhost:8000/docs.

**Important** : si vous avez une base de données existante de la V1 (sans
comptes utilisateurs), elle est incompatible avec le nouveau schéma (colonne
`user_id` requise sur `sources`). En local, supprimez simplement le fichier
`changeledger.db` avant de relancer le serveur — il sera recréé automatiquement
avec le nouveau schéma. Sur Railway, voir la section déploiement ci-dessous.

**Mise à jour ultérieure du schéma** (ex. ajout des colonnes `reset_token` /
`reset_token_expires_at` sur `users`) : contrairement au tout premier déploiement V2,
il ne s'agit plus de recréer les tables depuis zéro (ce qui perdrait les comptes et
abonnements existants), mais d'ajouter les nouvelles colonnes avec `ALTER TABLE` — voir
la section déploiement ci-dessous.

### Séquence de test recommandée (comptes + facturation)

```bash
BASE=http://localhost:8000

# 1. Créer un compte
curl -s -X POST $BASE/auth/signup -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "motdepasse123"}'

# 2. Se connecter : récupérer le token
TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "motdepasse123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 3. Ajouter une source (nécessite le token)
curl -s -X POST $BASE/sources -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"supplier_name": "Fournisseur Test", "label": "CGV", "url": "https://example.com"}'

# Noter l'"id" renvoyé, puis déclencher une vérification
curl -s -X POST $BASE/sources/<ID>/check -H "Authorization: Bearer $TOKEN"

# Consulter l'historique (uniquement les sources de cet utilisateur)
curl -s $BASE/changes -H "Authorization: Bearer $TOKEN"

# 4. (Si STRIPE_SECRET_KEY et STRIPE_PRICE_ESSENTIEL_MONTHLY configurés en mode test)
# Démarrer un paiement Checkout pour le palier Essentiel, cycle mensuel ou annuel :
curl -s -X POST $BASE/billing/checkout -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" -d '{"plan": "essentiel", "cycle": "monthly"}'
# → ouvre l'URL "checkout_url" renvoyée dans un navigateur pour payer en mode test
# (numéro de carte de test Stripe : 4242 4242 4242 4242, toute date future, tout CVC)

# 5. (Si ADMIN_SECRET configuré) Activer manuellement le palier Entreprise pour ce compte :
curl -s -X POST $BASE/admin/users/plan -H "Content-Type: application/json" \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"email": "test@example.com", "plan": "entreprise"}'

# Lister tous les comptes (utile en administration courante, sans passer par la base) :
curl -s $BASE/admin/users -H "X-Admin-Secret: $ADMIN_SECRET"
```

Si l'appel à Claude échoue (clé API absente ou invalide), le changement est quand
même enregistré avec une catégorie "autre" et un message d'erreur en résumé —
la détection ne doit jamais se bloquer à cause d'un souci sur l'analyse IA.

## Configuration Stripe

1. Créez un compte Stripe (ou utilisez votre compte existant), **en mode test**
   pour commencer.
2. Créez deux produits, "Essentiel" et "Pro", chacun avec **deux prix récurrents** :
   un mensuel et un annuel. Copiez les 4 **Price ID** (`price_...`) dans
   `STRIPE_PRICE_ESSENTIEL_MONTHLY`, `STRIPE_PRICE_ESSENTIEL_ANNUAL`,
   `STRIPE_PRICE_PRO_MONTHLY` et `STRIPE_PRICE_PRO_ANNUAL`.
3. Copiez la clé secrète (`sk_test_...` en mode test) dans `STRIPE_SECRET_KEY`.
4. Créez un endpoint webhook pointant vers `<votre URL>/billing/webhook`,
   écoutant au minimum `checkout.session.completed`,
   `customer.subscription.updated` et `customer.subscription.deleted`. Copiez
   le secret de signature (`whsec_...`) dans `STRIPE_WEBHOOK_SECRET`.
5. Le palier **Entreprise** n'a pas de prix Stripe : il s'active manuellement via
   l'endpoint protégé `POST /admin/users/plan` (voir section "Administration"
   ci-dessous) après un contact commercial.
6. La période d'essai de 14 jours (`TRIAL_PERIOD_DAYS` dans `app/billing.py`) est gérée en
   code via `subscription_data.trial_period_days` sur la session Checkout : rien à configurer
   côté Stripe pour chaque prix. Pendant l'essai, le statut renvoyé par l'API/le frontend est
   `trialing` ; Stripe prélève automatiquement à l'issue des 14 jours, sauf annulation.

## Réinitialisation de mot de passe

Pas de page web dédiée (pas de frontend pour l'instant) : le flux se fait en deux appels API.

```bash
# 1. Demander un code de réinitialisation (toujours la même réponse, que l'email existe ou non)
curl -s -X POST $BASE/auth/forgot-password -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
# → si le compte existe et que RESEND_API_KEY est configurée, un email contenant un code
#   (valable 30 minutes par défaut, voir PASSWORD_RESET_EXPIRE_MINUTES) est envoyé.

# 2. Réinitialiser avec ce code
curl -s -X POST $BASE/auth/reset-password -H "Content-Type: application/json" \
  -d '{"token": "<code reçu par email>", "new_password": "nouveaumotdepasse123"}'
```

Le code est à usage unique : il est invalidé dès qu'il est utilisé (ou remplacé par une
nouvelle demande via `/auth/forgot-password`).

## Configuration des alertes email

1. Créez un compte sur [Resend](https://resend.com) (un plan gratuit suffit pour démarrer).
2. Vérifiez un domaine d'envoi (onglet "Domains") — Resend exige un domaine vérifié
   pour envoyer autre chose qu'à votre propre adresse de test (sinon seule l'adresse
   du compte Resend peut recevoir des emails, via `onboarding@resend.dev`). Un
   sous-domaine dédié (ex. `mail.votre-domaine.fr`) est recommandé plutôt que le
   domaine racine, pour ne pas interférer avec une éventuelle configuration email existante.
   Pour ChangeLedger : domaine `mail.changeledger.io` vérifié (DNS chez Hostinger).
3. Créez une clé API et copiez-la dans `RESEND_API_KEY`.
4. Renseignez `ALERT_FROM_EMAIL` avec une adresse de ce domaine (ex.
   `alertes@mail.changeledger.io`).
5. Si `RESEND_API_KEY` n'est pas définie, les alertes sont simplement désactivées — la
   détection de changement continue de fonctionner normalement, sans email envoyé.

Un email est envoyé au propriétaire du compte (son adresse de connexion) dès qu'un
changement de sévérité "urgent" ou "attention" est détecté sur une de ses sources —
que ce soit via une vérification manuelle (`/sources/{id}/check`) ou automatique
(`/check-all`). Les changements "info" ne déclenchent pas d'alerte.

## Webhooks

En plus de l'alerte email, chaque utilisateur peut enregistrer sa propre URL de
webhook (self-service, pas besoin d'intervention admin) :

```bash
# Enregistrer un webhook (doit être en https://)
curl -s -X PUT $BASE/auth/webhook -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"webhook_url": "https://hooks.slack.com/services/..."}'

# L'effacer
curl -s -X PUT $BASE/auth/webhook -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" -d '{"webhook_url": null}'
```

À chaque changement "urgent" ou "attention" détecté, un `POST` JSON est envoyé sur
cette URL (en plus de l'email), avec une clé `text` (message prêt à l'emploi,
compatible webhook entrant Slack) et des objets `source`/`change` structurés pour
les receveurs génériques (Zapier, système interne...). Même logique de repli que
les autres alertes : un échec d'envoi (URL injoignable, webhook supprimé côté
destinataire) n'interrompt jamais la détection de changement elle-même.

## Frontend

Une page unique, `GET /app`, sert de parcours client complet : inscription/connexion,
tableau de bord (ajout/suppression de sources, vérification manuelle, historique des
changements détectés avec leur diff), et compte (palier actuel, lien vers Stripe Checkout
ou le portail client selon le palier, configuration du webhook personnel, réinitialisation
de mot de passe). Autonome comme `/admin/ui` : HTML/CSS/JS inline, aucune dépendance de
build, servie directement par l'API. Le jeton JWT est stocké dans `localStorage` du
navigateur (persistant, cohérent avec sa durée de vie de 7 jours côté API).

Les URLs de retour Stripe (succès/annulation de paiement, portail client) pointent par
défaut vers `/app` plutôt que `/docs`.

## Mentions légales / CGU / CGV / confidentialité

Trois pages statiques, servies par l'API comme `/app` et `/admin/ui` (HTML inline, pas
de dépendance de build) :

- `GET /legal/cgu` — conditions générales d'utilisation
- `GET /legal/cgv` — conditions générales de vente (clientèle B2B uniquement, pas de
  droit de rétractation)
- `GET /legal/confidentialite` — politique de confidentialité RGPD (sous-traitants :
  Anthropic, Stripe, Resend, Railway)

Le contenu (`app/legal_pages.py`) reflète la structure donnée par l'éditeur : service
exploité par **ITEC FRANCE** (SAS, RCS Paris 921 573 051), la marque et le SaaS
ChangeLedger restant la propriété personnelle de Patrice Le Lann, concédés en licence à
ITEC FRANCE pour la France. **C'est un premier brouillon : à faire relire par un
professionnel (avocat ou service juridique en ligne) avant toute utilisation réelle,
en particulier avant le passage de Stripe en mode live** — notamment la formalisation de
la licence de marque, et le décalage entre le code APE d'ITEC FRANCE (gestion de fonds)
et l'activité réellement exercée (édition de SaaS).

## Administration

Une petite interface web, `GET /admin/ui`, permet de lister les comptes et de
changer leur palier sans passer par des commandes curl ou la console Postgres
de Railway : ouvrez `<votre URL>/admin/ui` dans un navigateur, saisissez le
secret admin (stocké uniquement en mémoire de l'onglet, jamais envoyé ailleurs
qu'à votre propre API), et utilisez le tableau pour consulter ou modifier un
compte. C'est le moyen normal d'activer le palier **Entreprise** après un
contact commercial (il n'y a pas de paiement en ligne pour ce palier).

Elle s'appuie sur trois endpoints JSON, protégés par un secret partagé
(`ADMIN_SECRET`, à fournir dans l'en-tête `X-Admin-Secret`) — toujours
utilisables directement si besoin (scripts, automatisation) :

- `GET /admin/users` — liste tous les comptes (email, palier, statut d'abonnement).
- `POST /admin/users/plan` — change le palier d'un compte, identifié par son
  email : `{"email": "client@exemple.com", "plan": "entreprise"}`.
- `DELETE /admin/users` — supprime définitivement un compte et toutes ses données
  (sources, changements), identifié par son email : `{"email": "client@exemple.com"}`.
  Utile pour nettoyer un compte de test, ou répondre à une demande de suppression de
  compte (droit RGPD à l'effacement). Ne touche pas à Stripe : annulez/supprimez
  séparément l'abonnement ou le client côté Stripe si besoin.

Contrairement à `CRON_SECRET`, `ADMIN_SECRET` n'a pas de mode "ouvert" : si la
variable n'est pas définie, ces trois endpoints refusent systématiquement
l'appel (403) plutôt que de rester accessibles sans protection — ils permettent
de changer le palier, ou de supprimer, n'importe quel compte. Générez une vraie valeur avec
`openssl rand -hex 32`, distincte de `CRON_SECRET` et des autres secrets. La
page `/admin/ui` elle-même n'est pas protégée par un mot de passe (comme les
commandes curl équivalentes, c'est le secret qui protège les données, pas
l'accès à la page) : évitez de partager son URL inutilement.

## Déploiement sur Railway

1. Poussez ce dossier sur un dépôt GitHub.
2. Dans Railway : New Project → Deploy from GitHub repo.
3. Ajoutez un plugin **Postgres** — **dans le même projet** que le service web
   (Postgres et le service API doivent être dans le même projet Railway pour
   pouvoir se parler via le réseau interne `*.railway.internal`).
4. Dans les Variables du service API, ajoutez son `DATABASE_URL` en copiant la
   valeur depuis l'onglet Variables **du service Postgres** (ne pas saisir une
   URL SQLite ou une adresse interne d'un autre service par erreur).
5. Ajoutez aussi : `ANTHROPIC_API_KEY`, `JWT_SECRET_KEY` et `ADMIN_SECRET`
   (chacune générée avec `openssl rand -hex 32`, jamais la valeur par défaut du
   code, et distincte de leur équivalent en local), les variables Stripe si la
   facturation doit être active en production, et `RESEND_API_KEY` /
   `ALERT_FROM_EMAIL` si les alertes email doivent être actives en production.
6. Railway détecte `requirements.txt` et `Procfile` automatiquement (via Nixpacks)
   et démarre `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. **Base de données existante** : si le service tournait déjà en V1 (sans
   comptes utilisateurs), le nouveau schéma (`user_id` sur `sources`) n'est pas
   appliqué automatiquement (`create_all` ne modifie pas les tables
   existantes). Avant le premier déploiement de cette V2, videz les tables via
   la console Postgres de Railway : `DROP TABLE changes, snapshots, sources
   CASCADE;` — elles seront recréées avec le bon schéma au démarrage.
8. **Évolutions ultérieures du schéma** (après ce premier déploiement V2, une fois de
   vrais comptes en production) : `create_all` ne modifie jamais les tables existantes,
   donc un nouveau champ sur un modèle (ex. `reset_token` sur `User`) n'apparaît pas tout
   seul. Pas de `DROP TABLE` cette fois (ça supprimerait les comptes et abonnements
   réels) : ajoutez la colonne manuellement via la console Postgres de Railway, par
   exemple : `ALTER TABLE users ADD COLUMN reset_token VARCHAR; ALTER TABLE users ADD
   COLUMN reset_token_expires_at TIMESTAMP;` — à faire une fois, avant ou juste après le
   déploiement du code qui l'utilise.
   De même pour `webhook_url` : `ALTER TABLE users ADD COLUMN webhook_url VARCHAR;`
   avant de déployer le code qui l'utilise.

### Planifier les vérifications automatiques

Railway n'a pas de fonctionnalité native pour appeler une route HTTP à
intervalle régulier (son "Cron Schedule" redémarre un service entier, ce qui
ne convient pas ici). La solution la plus simple reste un service externe
gratuit :

- **cron-job.org** : créez un compte, configurez un cron job en **POST** vers
  `<votre URL>/check-all`, à l'intervalle voulu. Si `CRON_SECRET` est défini
  côté API, ajoutez l'en-tête personnalisé `X-Cron-Secret: <valeur>` dans la
  configuration du job (sinon la route répond 401).

## Structure du projet

```
app/
  main.py        → routes de l'API (auth, facturation, sources, changements)
  auth.py        → hashage de mot de passe, JWT, dépendance d'utilisateur courant
  billing.py     → intégration Stripe (Checkout, portail client, webhook)
  notifier.py    → alertes email (Resend) et webhook de changement
  app_ui.py      → page HTML du frontend client (/app)
  legal_pages.py → pages HTML CGU / CGV / politique de confidentialité
  admin_ui.py    → page HTML de l'interface d'administration (/admin/ui)
  models.py      → modèles de base de données (User, Source, Snapshot, Change)
  schemas.py     → schémas Pydantic (requêtes/réponses)
  database.py    → configuration SQLAlchemy
  config.py      → variables d'environnement
  fetcher.py     → récupération et nettoyage du contenu d'une source
  differ.py      → calcul du diff et filtrage des changements triviaux
  analyzer.py    → appel à Claude pour classifier et résumer un changement
  crud.py        → opérations de base de données
```

## Stripe en mode live

Depuis le 17 octobre 2026, le service `web` sur Railway utilise les clés et webhook **live**
de Stripe (compte `changeledger.io`, activé) : `STRIPE_SECRET_KEY` (clé restreinte `rk_live_...`,
"Accès complet, à l'exception des opérations sensibles"), `STRIPE_WEBHOOK_SECRET` (endpoint
"ChangeLedger production"), et les 4 `STRIPE_PRICE_...` en versions live (Essentiel 29€/mois ou
290€/an, Pro 59€/mois ou 590€/an). Validé de bout en bout avec une vraie carte (essai de 14 jours,
donc sans prélèvement immédiat). Le mode test reste disponible en parallèle sur le même compte
Stripe pour les futurs développements, sans toucher au live.

## Prochaines étapes suggérées

1. Faire relire les CGU/CGV/politique de confidentialité par un professionnel, et
   formaliser la licence de marque entre Patrice Le Lann et ITEC FRANCE.
2. Habiller le frontend (logo, charte graphique) avant un lancement public.
