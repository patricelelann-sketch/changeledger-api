# ChangeLedger API — V2 (comptes utilisateurs + facturation)

Moteur de veille des conditions fournisseurs : surveille une source (page de CGV,
grille tarifaire...), détecte les changements, les classe et en résume l'impact
en langage clair via Claude. Cette V2 ajoute les comptes utilisateurs (JWT) et
la facturation par abonnement (Stripe, paliers Essentiel / Pro / Entreprise).

## Périmètre

Inclus (V1 + V2) :
- Comptes utilisateurs : inscription/connexion par email + mot de passe (JWT)
- Chaque source surveillée appartient à un utilisateur (multi-tenant)
- Trois paliers d'abonnement : **Essentiel** (5 sources), **Pro** (25 sources),
  **Entreprise** (illimité, activé manuellement après contact commercial — pas
  de paiement en ligne pour ce palier)
- Paiement par abonnement via Stripe Checkout (Essentiel/Pro) + portail client
  Stripe pour gérer/annuler l'abonnement
- Ajouter / lister / supprimer une source à surveiller (URL)
- Déclencher une vérification manuelle, ou groupée pour toutes les sources
  (endpoint système `/check-all`, protégé par un secret de cron)
- Détection de changement (diff texte), filtrage des changements triviaux
- Classification + résumé de l'impact via l'API Anthropic (Claude)
- Historique consultable des changements détectés

Volontairement hors périmètre, à construire ensuite :
- Alertes automatiques par email / Slack / webhook
- Import de PDF et de contrats signés (seules les pages web texte/HTML sont supportées pour l'instant)
- Frontend (cette V2 reste une API pure ; les URLs de retour Stripe pointent
  par défaut vers `/docs` faute de frontend dédié)

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

# 4. (Si STRIPE_SECRET_KEY et STRIPE_PRICE_ESSENTIEL configurés en mode test)
# Démarrer un paiement Checkout pour le palier Essentiel :
curl -s -X POST $BASE/billing/checkout -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" -d '{"plan": "essentiel"}'
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
2. Créez deux produits avec un prix récurrent mensuel : "Essentiel" et "Pro".
   Copiez leur **Price ID** (`price_...`) dans `STRIPE_PRICE_ESSENTIEL` et
   `STRIPE_PRICE_PRO`.
3. Copiez la clé secrète (`sk_test_...` en mode test) dans `STRIPE_SECRET_KEY`.
4. Créez un endpoint webhook pointant vers `<votre URL>/billing/webhook`,
   écoutant au minimum `checkout.session.completed`,
   `customer.subscription.updated` et `customer.subscription.deleted`. Copiez
   le secret de signature (`whsec_...`) dans `STRIPE_WEBHOOK_SECRET`.
5. Le palier **Entreprise** n'a pas de prix Stripe : il s'active manuellement via
   l'endpoint protégé `POST /admin/users/plan` (voir section "Administration"
   ci-dessous) après un contact commercial.

## Administration

Deux endpoints protégés par un secret partagé (`ADMIN_SECRET`, à fournir dans
l'en-tête `X-Admin-Secret`) permettent de gérer les comptes sans passer par la
console Postgres de Railway :

- `GET /admin/users` — liste tous les comptes (email, palier, statut d'abonnement).
- `POST /admin/users/plan` — change le palier d'un compte, identifié par son
  email. C'est le moyen normal d'activer le palier **Entreprise** après un
  contact commercial (il n'y a pas de paiement en ligne pour ce palier) :
  `{"email": "client@exemple.com", "plan": "entreprise"}`.

Contrairement à `CRON_SECRET`, `ADMIN_SECRET` n'a pas de mode "ouvert" : si la
variable n'est pas définie, ces deux endpoints refusent systématiquement
l'appel (403) plutôt que de rester accessibles sans protection — ils permettent
de changer le palier de n'importe quel compte. Générez une vraie valeur avec
`openssl rand -hex 32`, distincte de `CRON_SECRET` et des autres secrets.

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
   code, et distincte de leur équivalent en local), et les variables Stripe si
   la facturation doit être active en production.
6. Railway détecte `requirements.txt` et `Procfile` automatiquement (via Nixpacks)
   et démarre `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. **Base de données existante** : si le service tournait déjà en V1 (sans
   comptes utilisateurs), le nouveau schéma (`user_id` sur `sources`) n'est pas
   appliqué automatiquement (`create_all` ne modifie pas les tables
   existantes). Avant le premier déploiement de cette V2, videz les tables via
   la console Postgres de Railway : `DROP TABLE changes, snapshots, sources
   CASCADE;` — elles seront recréées avec le bon schéma au démarrage.

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
  models.py      → modèles de base de données (User, Source, Snapshot, Change)
  schemas.py     → schémas Pydantic (requêtes/réponses)
  database.py    → configuration SQLAlchemy
  config.py      → variables d'environnement
  fetcher.py     → récupération et nettoyage du contenu d'une source
  differ.py      → calcul du diff et filtrage des changements triviaux
  analyzer.py    → appel à Claude pour classifier et résumer un changement
  crud.py        → opérations de base de données
```

## Prochaines étapes suggérées

1. Valider la séquence de test ci-dessus en local, puis en conditions Stripe
   test avant tout paiement réel.
2. Brancher les alertes (email via un fournisseur type Resend/Postmark, ou
   webhook Slack) sur un changement détecté avec `severity` "urgent" ou "attention".
3. Réinitialisation de mot de passe (actuellement absente).
