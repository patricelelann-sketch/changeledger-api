"""Pages légales de ChangeLedger : CGU, CGV, politique de confidentialité.

Brouillon rédigé à partir des informations fournies par l'éditeur (extrait Kbis
d'ITEC FRANCE, structure de licence de marque, clientèle professionnelle,
facturation mensuelle/annuelle au choix). À FAIRE RELIRE PAR UN PROFESSIONNEL
(avocat ou service juridique en ligne) avant toute mise en production réelle,
en particulier avant le passage de Stripe en mode live : droit de la
consommation, RGPD, et formalisation de la licence de marque entre M. Le Lann
(titulaire) et ITEC FRANCE (exploitant) restent à valider avec un conseil.

Autonome (HTML/CSS inline, pas de JS), dans le même esprit que admin_ui.py et
app_ui.py : aucune dépendance de build, servi directement par l'API.
"""

LEGAL_STYLE = """
  :root {
    color-scheme: light dark;
    --cl-accent: #4B3FF2;
    --cl-ink: #12131A;
  }
  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem 4rem; line-height: 1.65;
    color: var(--cl-ink); background: #ffffff;
  }
  h1, h2, h3 { font-family: 'Space Grotesk', system-ui, sans-serif; font-weight: 500; }
  h1 { font-size: 1.6rem; margin-bottom: 0.3rem; font-weight: 700; }
  h2 { font-size: 1.15rem; margin-top: 2.2rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
  h3 { font-size: 1rem; margin-top: 1.4rem; }
  p, li { font-size: 0.95rem; }
  .muted { color: #6b7280; font-size: 0.88rem; }
  nav.legal-nav { display: flex; gap: 1rem; margin: 1rem 0 2rem; font-size: 0.9rem; flex-wrap: wrap; }
  nav.legal-nav a { color: var(--cl-accent); text-decoration: none; }
  nav.legal-nav a:hover { text-decoration: underline; }
  nav.legal-nav a.back { color: #6b7280; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }
  th { color: #6b7280; }
"""

LEGAL_NAV = """
<nav class="legal-nav">
  <a class="back" href="/app">&larr; Retour à ChangeLedger</a>
  <a href="/legal/cgu">Conditions générales d'utilisation</a>
  <a href="/legal/cgv">Conditions générales de vente</a>
  <a href="/legal/confidentialite">Politique de confidentialité</a>
</nav>
"""

CGU_HTML = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger — Conditions générales d'utilisation</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{LEGAL_STYLE}</style>
</head>
<body>
{LEGAL_NAV}

<h1>Conditions générales d'utilisation</h1>
<p class="muted">Dernière mise à jour : 16 octobre 2026</p>

<h2>1. Objet</h2>
<p>Les présentes conditions générales d'utilisation (« CGU ») ont pour objet de définir les
modalités et conditions d'accès et d'utilisation du service ChangeLedger (le « Service »), un
outil de veille automatisée des conditions fournisseurs (conditions générales de vente, grilles
tarifaires, contrats accessibles en ligne), accessible notamment à l'adresse
<code>changeledger.io</code> et ses sous-domaines. Toute création de compte implique l'acceptation
pleine et entière des présentes CGU.</p>

<h2>2. Mentions légales</h2>
<p>Le Service est édité par <strong>ITEC FRANCE</strong>, société par actions simplifiée (SAS) au
capital social de 1 000 €, immatriculée au Registre du Commerce et des Sociétés de Paris sous le
numéro 921 573 051, dont le siège social est situé 3 Rue Jacob, 75006 Paris, France, représentée
par son Président, M. Patrice Le Lann (ci-après l'« Éditeur »).</p>
<p>La marque « ChangeLedger » est la propriété de M. Patrice Le Lann, qui en a concédé l'usage et
l'exploitation à ITEC FRANCE dans le cadre d'un contrat de licence.</p>
<p>Le Service est hébergé par Railway Corporation, 548 Market St, Suite 68956, San Francisco,
Californie 94104, États-Unis (<a href="https://railway.com">railway.com</a>).</p>
<p>Contact : <a href="mailto:patrice.lelann@gmail.com">patrice.lelann@gmail.com</a></p>

<h2>3. Définitions</h2>
<ul>
<li><strong>Compte</strong> : espace personnel créé par un Utilisateur pour accéder au Service.</li>
<li><strong>Source</strong> : une page web (conditions générales, grille tarifaire, contrat en
ligne...) qu'un Utilisateur ajoute au Service pour qu'elle soit surveillée.</li>
<li><strong>Changement</strong> : une modification détectée entre deux relevés successifs d'une
Source, classée par catégorie et niveau de sévérité et accompagnée d'un résumé généré
automatiquement.</li>
</ul>

<h2>4. Accès au Service et création de compte</h2>
<p>Le Service est réservé aux personnes agissant dans le cadre de leur activité professionnelle
(voir article 1 des <a href="/legal/cgv">CGV</a>). La création d'un compte nécessite une adresse
email valide et un mot de passe. L'Utilisateur est seul responsable de la confidentialité de ses
identifiants et de toute activité réalisée depuis son compte.</p>

<h2>5. Description et limites du Service</h2>
<p>Le Service permet d'ajouter des Sources à surveiller, de déclencher des vérifications manuelles
ou automatiques, et de consulter l'historique des Changements détectés. La classification (catégorie,
sévérité) et le résumé de chaque Changement sont générés automatiquement par un modèle d'intelligence
artificielle (API Anthropic Claude) à partir du contenu textuel de la Source.</p>
<p><strong>Ces résumés et classifications sont fournis à titre informatif uniquement et ne
constituent en aucun cas un avis ou un conseil juridique.</strong> Ils peuvent contenir des erreurs,
approximations ou omissions. Il appartient à l'Utilisateur de vérifier par lui-même, le cas échéant
avec l'assistance d'un conseil juridique, la portée réelle de tout changement détecté avant d'en
tirer une conséquence quelconque pour son activité.</p>
<p>Le Service ne couvre, à ce jour, que des pages web au format texte/HTML ; les documents PDF ou
contrats signés importés ne sont pas pris en charge.</p>

<h2>6. Obligations de l'Utilisateur</h2>
<p>L'Utilisateur s'engage à : utiliser le Service conformément à sa destination ; ne pas tenter de
contourner les limites de son palier d'abonnement ; ne pas utiliser le Service à des fins illicites
ou pour surveiller des contenus auxquels il n'a pas légitimement accès ; ne pas perturber le
fonctionnement du Service (tentatives d'intrusion, surcharge délibérée, etc.).</p>

<h2>7. Disponibilité du Service</h2>
<p>L'Éditeur s'efforce d'assurer une disponibilité raisonnable du Service mais ne garantit pas un
accès ininterrompu. Des interruptions peuvent survenir pour maintenance, mise à jour, ou en raison
de causes échappant à son contrôle (panne de l'hébergeur, d'un fournisseur tiers, etc.).</p>

<h2>8. Propriété intellectuelle</h2>
<p>Le Service, son code, sa structure, ses marques et logos sont protégés par le droit de la
propriété intellectuelle et demeurent la propriété exclusive de l'Éditeur ou de ses concédants.
Aucune disposition des présentes CGU ne saurait être interprétée comme une cession de droits de
propriété intellectuelle au profit de l'Utilisateur.</p>

<h2>9. Données personnelles</h2>
<p>Le traitement des données personnelles des Utilisateurs est décrit dans la
<a href="/legal/confidentialite">politique de confidentialité</a>, qui fait partie intégrante des
présentes CGU.</p>

<h2>10. Responsabilité</h2>
<p>L'Éditeur met en œuvre des moyens raisonnables pour assurer l'exactitude des informations
fournies par le Service, sans garantir l'absence totale d'erreur, notamment s'agissant des contenus
générés automatiquement (voir article 5). La responsabilité de l'Éditeur ne saurait être engagée en
cas de dommage résultant d'une décision prise par l'Utilisateur sur la seule foi d'un résumé ou
d'une classification automatique, sans vérification complémentaire.</p>

<h2>11. Suspension et résiliation du compte</h2>
<p>L'Éditeur se réserve le droit de suspendre ou résilier, après notification lorsque les
circonstances le permettent, le compte d'un Utilisateur en cas de manquement aux présentes CGU.
L'Utilisateur peut à tout moment cesser d'utiliser le Service ; la résiliation de son abonnement
payant est régie par les <a href="/legal/cgv">CGV</a>.</p>

<h2>12. Modification des CGU</h2>
<p>L'Éditeur peut modifier les présentes CGU à tout moment, notamment pour les adapter à l'évolution
du Service ou de la réglementation applicable. Les Utilisateurs seront informés de toute modification
substantielle par email ou via le Service.</p>

<h2>13. Droit applicable et juridiction</h2>
<p>Les présentes CGU sont soumises au droit français. Tout litige relatif à leur interprétation ou
leur exécution relève, à défaut de résolution amiable, de la compétence des tribunaux du ressort du
siège social de l'Éditeur.</p>

<h2>14. Contact</h2>
<p>Pour toute question relative aux présentes CGU :
<a href="mailto:patrice.lelann@gmail.com">patrice.lelann@gmail.com</a></p>

</body>
</html>
"""

CGV_HTML = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger — Conditions générales de vente</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{LEGAL_STYLE}</style>
</head>
<body>
{LEGAL_NAV}

<h1>Conditions générales de vente</h1>
<p class="muted">Dernière mise à jour : 16 octobre 2026</p>

<h2>1. Champ d'application</h2>
<p>Les présentes conditions générales de vente (« CGV ») s'appliquent à tout abonnement souscrit
au service ChangeLedger (le « Service »), édité par ITEC FRANCE (voir mentions légales dans les
<a href="/legal/cgu">CGU</a>).</p>
<p><strong>Le Service est exclusivement réservé aux personnes agissant pour les besoins de leur
activité professionnelle</strong> (entreprises, indépendants, associations...), à l'exclusion de
toute souscription à titre personnel par un consommateur au sens du Code de la consommation. En
souscrivant un abonnement, le client déclare et garantit agir à ce titre professionnel. Les
dispositions du Code de la consommation, et notamment le droit de rétractation, ne sont donc pas
applicables aux présentes CGV.</p>

<h2>2. Description des offres</h2>
<table>
<tr><th>Palier</th><th>Sources surveillées</th><th>Souscription</th></tr>
<tr><td>Essentiel</td><td>5</td><td>En ligne (Stripe Checkout)</td></tr>
<tr><td>Pro</td><td>25</td><td>En ligne (Stripe Checkout)</td></tr>
<tr><td>Entreprise</td><td>Illimité</td><td>Sur devis, après contact commercial</td></tr>
</table>
<p>Le détail et les tarifs en vigueur de chaque palier sont affichés sur le compte client du
Service au moment de la souscription ; ce sont ces tarifs, et non un montant reproduit dans les
présentes CGV, qui font foi.</p>

<h2>3. Tarifs et facturation</h2>
<p>Les tarifs sont exprimés en euros. Le client choisit, pour les paliers Essentiel et Pro, une
facturation <strong>mensuelle ou annuelle</strong>, au tarif correspondant affiché lors de la
souscription. Le palier Entreprise fait l'objet d'un devis spécifique.</p>
<p>Sauf mention contraire, les tarifs affichés s'entendent hors taxes ; la TVA applicable est
ajoutée conformément à la réglementation en vigueur.</p>

<h2>4. Souscription et paiement</h2>
<p>La souscription à un abonnement Essentiel ou Pro s'effectue en ligne via Stripe Checkout,
solution de paiement opérée par Stripe. ITEC FRANCE ne collecte ni ne stocke aucune donnée de
carte bancaire ; ces données sont traitées directement par Stripe.</p>
<p>Une période d'essai de 14 jours est accordée à toute nouvelle souscription Essentiel ou Pro.
La carte bancaire est enregistrée dès la souscription ; sauf résiliation par le client avant la
fin de la période d'essai (depuis le portail de gestion d'abonnement accessible dans son compte),
le premier prélèvement, correspondant au tarif et à la périodicité choisis, intervient
automatiquement à l'issue de ces 14 jours.</p>
<p>Le paiement est ensuite prélevé automatiquement selon la périodicité choisie (mensuelle ou
annuelle), par reconduction tacite, jusqu'à résiliation par le client.</p>

<h2>5. Durée, reconduction et résiliation</h2>
<p>L'abonnement est souscrit pour la période choisie (mois ou année) et se renouvelle
automatiquement à son terme pour une période de même durée, sauf résiliation. Le client peut
résilier à tout moment depuis le portail de gestion d'abonnement accessible dans son compte ; la
résiliation prend effet à l'issue de la période en cours, déjà payée, sans remboursement au
prorata de la période entamée.</p>

<h2>6. Défaut de paiement</h2>
<p>En cas d'échec de paiement (carte expirée, provision insuffisante, etc.), Stripe peut effectuer
plusieurs tentatives de prélèvement selon son fonctionnement standard. En l'absence de régularisation,
l'abonnement peut être suspendu ou résilié et le compte ramené au palier gratuit (fonctionnalités
limitées), sans préjudice des sommes déjà dues.</p>

<h2>7. Palier Entreprise</h2>
<p>Le palier Entreprise n'est pas souscriptible en self-service : il est activé manuellement par
l'Éditeur après contact commercial et accord sur les conditions tarifaires spécifiques, le cas
échéant formalisées par un devis ou un contrat séparé qui prévaut sur les présentes CGV en cas de
contradiction.</p>

<h2>8. Garanties et responsabilité</h2>
<p>Voir l'article 10 des <a href="/legal/cgu">CGU</a>, qui s'applique également aux présentes CGV.
La responsabilité de l'Éditeur, lorsqu'elle est engagée, est en tout état de cause limitée au
montant des sommes effectivement versées par le client au titre des douze derniers mois
d'abonnement.</p>

<h2>9. Droit applicable et juridiction</h2>
<p>Les présentes CGV sont soumises au droit français. Tout litige relève, à défaut de résolution
amiable, de la compétence du Tribunal de commerce de Paris, sauf disposition d'ordre public
contraire.</p>

<h2>10. Contact</h2>
<p>Pour toute question relative à la facturation ou aux présentes CGV :
<a href="mailto:patrice.lelann@gmail.com">patrice.lelann@gmail.com</a></p>

</body>
</html>
"""

PRIVACY_HTML = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger — Politique de confidentialité</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{LEGAL_STYLE}</style>
</head>
<body>
{LEGAL_NAV}

<h1>Politique de confidentialité</h1>
<p class="muted">Dernière mise à jour : 16 octobre 2026</p>

<h2>1. Responsable du traitement</h2>
<p>Le responsable du traitement des données personnelles collectées via le service ChangeLedger
est ITEC FRANCE, SAS au capital de 1 000 €, RCS Paris 921 573 051, 3 Rue Jacob, 75006 Paris,
France. Pour toute question relative à vos données personnelles :
<a href="mailto:patrice.lelann@gmail.com">patrice.lelann@gmail.com</a>.</p>

<h2>2. Données collectées</h2>
<ul>
<li><strong>Données de compte</strong> : adresse email, mot de passe (stocké sous forme hachée,
jamais en clair).</li>
<li><strong>Données d'usage</strong> : les Sources ajoutées (URL, nom du fournisseur, libellé), le
contenu textuel relevé sur ces Sources et son historique, les Changements détectés (catégorie,
sévérité, résumé, différence de texte).</li>
<li><strong>Données de facturation</strong> : gérées directement par Stripe (voir section 5) ;
ITEC FRANCE ne conserve pas vos coordonnées bancaires.</li>
<li><strong>Webhook optionnel</strong> : l'URL de webhook que vous configurez, le cas échéant, pour
recevoir une copie des alertes.</li>
<li><strong>Données techniques</strong> : adresse IP (utilisée notamment pour la limitation du
nombre de tentatives de connexion/inscription, à des fins de sécurité).</li>
</ul>

<h2>3. Finalités du traitement</h2>
<ul>
<li>Fournir et faire fonctionner le Service (authentification, surveillance des Sources, détection
et classification des Changements) ;</li>
<li>Vous envoyer les alertes par email ou webhook que vous avez configurées ;</li>
<li>Gérer la facturation de votre abonnement ;</li>
<li>Assurer la sécurité du Service (limitation de débit, prévention des abus) ;</li>
<li>Répondre à vos demandes de support.</li>
</ul>

<h2>4. Base légale</h2>
<p>Ces traitements reposent sur l'exécution du contrat qui vous lie à ITEC FRANCE (CGU/CGV) et, pour
la sécurité du Service, sur l'intérêt légitime de l'Éditeur à protéger le Service contre les abus.</p>

<h2>5. Destinataires des données et sous-traitants</h2>
<p>Vos données sont traitées par ITEC FRANCE et peuvent être transmises aux prestataires suivants,
strictement pour les besoins du Service :</p>
<ul>
<li><strong>Anthropic</strong> (API Claude) : le contenu textuel et les différences détectées sur vos
Sources sont transmis à Anthropic pour générer automatiquement la classification et le résumé de
chaque Changement. Voir <a href="https://www.anthropic.com/legal/privacy">la politique de
confidentialité d'Anthropic</a>.</li>
<li><strong>Stripe</strong> : traitement des paiements et de la facturation. Voir
<a href="https://stripe.com/fr/privacy">la politique de confidentialité de Stripe</a>.</li>
<li><strong>Resend</strong> : envoi des emails transactionnels (alertes de changement,
réinitialisation de mot de passe). Voir <a href="https://resend.com/legal/privacy-policy">la
politique de confidentialité de Resend</a>.</li>
<li><strong>Railway</strong> : hébergement de l'application et de la base de données. Voir
<a href="https://railway.com/legal/privacy">la politique de confidentialité de Railway</a>.</li>
</ul>
<p>Ces prestataires n'utilisent vos données que pour exécuter les services qui leur sont confiés,
et non à leurs propres fins commerciales.</p>

<h2>6. Transferts hors Union européenne</h2>
<p>Certains des prestataires mentionnés ci-dessus (Anthropic, Stripe, Resend, Railway) sont établis
aux États-Unis et peuvent y traiter tout ou partie des données. Ces transferts s'appuient sur les
garanties prévues par ces prestataires (clauses contractuelles types de la Commission européenne
ou mécanisme équivalent), conformément à l'article 46 du RGPD.</p>

<h2>7. Durée de conservation</h2>
<p>Vos données de compte et d'usage sont conservées pendant toute la durée de votre relation avec
ChangeLedger, puis supprimées ou anonymisées dans un délai raisonnable après la clôture de votre
compte, sous réserve des durées de conservation imposées par la loi (notamment en matière
comptable et fiscale pour les données de facturation).</p>

<h2>8. Sécurité</h2>
<p>Les mots de passe sont stockés sous forme hachée (bcrypt). Les communications avec le Service
sont chiffrées (HTTPS). L'accès aux fonctions d'administration est protégé par un secret dédié. Des
mesures de limitation de débit protègent les points d'entrée sensibles (connexion, inscription,
réinitialisation de mot de passe) contre les tentatives automatisées abusives.</p>

<h2>9. Vos droits</h2>
<p>Conformément au RGPD, vous disposez d'un droit d'accès, de rectification, d'effacement, de
limitation, de portabilité et d'opposition sur vos données personnelles. Vous pouvez exercer ces
droits en écrivant à <a href="mailto:patrice.lelann@gmail.com">patrice.lelann@gmail.com</a>. Vous
disposez également du droit d'introduire une réclamation auprès de la Commission Nationale de
l'Informatique et des Libertés (CNIL, <a href="https://www.cnil.fr">www.cnil.fr</a>).</p>

<h2>10. Cookies et stockage local</h2>
<p>Le Service n'utilise pas de cookies de suivi publicitaire. Votre navigateur conserve, dans son
stockage local (« localStorage »), le jeton de connexion qui vous permet de rester identifié entre
deux visites. Cette donnée reste sur votre appareil et n'est transmise qu'au Service lui-même.</p>

<h2>11. Modification de la politique de confidentialité</h2>
<p>Cette politique peut être mise à jour pour refléter l'évolution du Service ou de la
réglementation. Toute modification substantielle vous sera notifiée par email ou via le Service.</p>

</body>
</html>
"""
