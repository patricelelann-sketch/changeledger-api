# ChangeLedger API — V1 (moteur de veille)

Moteur de veille des conditions fournisseurs : surveille une source (page de CGV,
grille tarifaire...), détecte les changements, les classe et en résume l'impact
en langage clair via Claude.

## Périmètre de cette V1

Inclus :
- Ajouter / lister / supprimer une source à surveiller (URL)
- Déclencher une vérification manuelle, ou groupée pour toutes les sources
- Détection de changement (diff texte), filtrage des changements triviaux
- Classification + résumé de l'impact via l'API Anthropic (Claude)
- Historique consultable des changements détectés

Volontairement hors périmètre, à construire ensuite :
- Comptes utilisateurs / authentification / multi-tenant
- Facturation (Stripe)
- Alertes automatiques par email / Slack / webhook
- Import de PDF et de contrats signés (seules les pages web texte/HTML sont supportées pour l'instant)
- Planification automatique des vérifications (voir plus bas pour la brancher)

## Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Puis éditez .env : renseignez ANTHROPIC_API_KEY
```

Lancer le serveur :

```bash
uvicorn app.main:app --reload
```

L'API est alors disponible sur http://localhost:8000, avec une documentation
interactive auto-générée sur http://localhost:8000/docs.

## Important — non testé en exécution dans cet environnement

Ce code a été relu avec soin et vérifié syntaxiquement (`python -m py_compile`
sur chaque fichier), mais je n'ai pas pu l'installer ni le lancer ici : l'accès
à PyPI est bloqué par la politique réseau de cet environnement (erreur 403).
Avant de considérer la V1 comme acquise, lancez vous-même la séquence de test
ci-dessous en local — c'est rapide et ça confirme que tout s'enchaîne bien,
en particulier le stockage de la catégorie/sévérité en base (un point que je
n'ai pas pu vérifier en conditions réelles).

### Séquence de test recommandée

```bash
# 1. Démarrer le serveur (voir ci-dessus), puis dans un autre terminal :

# Ajouter une source
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"supplier_name": "Fournisseur Test", "label": "CGV", "url": "https://example.com"}'

# Noter l'"id" renvoyé, puis déclencher une première capture (aucun changement possible encore)
curl -X POST http://localhost:8000/sources/<ID>/check

# Modifier légèrement la page surveillée (ou pointer vers une autre URL avec un contenu différent),
# puis relancer la même commande : un changement devrait être détecté, classifié et résumé.
curl -X POST http://localhost:8000/sources/<ID>/check

# Consulter l'historique
curl http://localhost:8000/changes
```

Si l'appel à Claude échoue (clé API absente ou invalide), le changement est quand
même enregistré avec une catégorie "autre" et un message d'erreur en résumé —
la détection ne doit jamais se bloquer à cause d'un souci sur l'analyse IA.

## Déploiement sur Railway

1. Poussez ce dossier sur un dépôt GitHub.
2. Dans Railway : New Project → Deploy from GitHub repo.
3. Ajoutez un plugin **Postgres** au projet : Railway injecte automatiquement
   la variable `DATABASE_URL` dans le service de l'API.
4. Dans les Variables du service API, ajoutez `ANTHROPIC_API_KEY` (et
   éventuellement `ANTHROPIC_MODEL` si vous voulez forcer un modèle précis).
5. Railway détecte `requirements.txt` et `Procfile` automatiquement (via Nixpacks)
   et démarre `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Planifier les vérifications automatiques

Cette V1 n'inclut pas de planificateur interne. Deux options simples :
- **Railway Cron Jobs** (dans les paramètres du projet) : configurez un job qui
  appelle `POST /check-all` à l'intervalle souhaité (ex. toutes les heures).
- Un service externe de type cron-job.org qui appelle la même route.

## Structure du projet

```
app/
  main.py        → routes de l'API
  models.py       → modèles de base de données (Source, Snapshot, Change)
  schemas.py      → schémas Pydantic (requêtes/réponses)
  database.py     → configuration SQLAlchemy
  config.py       → variables d'environnement
  fetcher.py      → récupération et nettoyage du contenu d'une source
  differ.py       → calcul du diff et filtrage des changements triviaux
  analyzer.py     → appel à Claude pour classifier et résumer un changement
  crud.py         → opérations de base de données
```

## Prochaines étapes suggérées

1. Valider la séquence de test ci-dessus en local.
2. Brancher les alertes (email via un fournisseur type Resend/Postmark, ou
   webhook Slack) sur un changement détecté avec `severity` "urgent" ou "attention".
3. Ajouter les comptes utilisateurs une fois qu'un premier fournisseur-pilote
   confirme que la détection fonctionne sur de vraies pages de CGV.
