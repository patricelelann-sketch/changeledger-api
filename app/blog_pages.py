"""Section blog minimale de ChangeLedger, servie sur le domaine marketing
(changeledger.io) à /blog et /blog/{slug}.

Autonome (HTML/CSS inline), dans le même esprit que landing_page.py et
legal_pages.py : aucune dépendance de build, servi directement par l'API,
même identité visuelle (couleurs, typographie Space Grotesk / Plus Jakarta
Sans). Chaque article est une entrée du dict BLOG_POSTS (clé = slug) ; penser
à ajouter l'entrée correspondante à SITEMAP_ENTRIES dans main.py.
"""
from .config import CONTACT_EMAIL

BLOG_STYLE = """
  :root {
    color-scheme: light dark;
    --cl-accent: #4B3FF2;
    --cl-accent-tint: #EFECFE;
    --cl-ink: #12131A;
    --cl-muted: #5B5E6B;
    --cl-border: rgba(17,19,26,0.1);
  }
  * { box-sizing: border-box; }
  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; padding: 0; line-height: 1.65; color: var(--cl-ink); background: #ffffff;
  }
  a { color: var(--cl-accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 0 1.25rem; }
  header.site { border-bottom: 1px solid var(--cl-border); }
  header.site .wrap { display: flex; align-items: center; justify-content: space-between; height: 68px; }
  header.site .brand { font-weight: 700; font-size: 1.2rem; font-family: 'Space Grotesk', system-ui, sans-serif; }
  header.site .brand .accent { color: var(--cl-accent); }
  header.site nav { display: flex; align-items: center; gap: 1.5rem; font-size: 0.92rem; font-weight: 600; }
  header.site nav a:not(.btn) { color: var(--cl-ink); }
  header.site nav a:not(.btn):hover { color: var(--cl-accent); }
  .btn { padding: 0.55rem 1.1rem; border-radius: 8px; font-weight: 700; }
  .btn-primary { background: var(--cl-accent); color: #fff !important; }
  .btn-primary:hover { text-decoration: none; opacity: 0.92; }
  main { padding: 2.5rem 0 4rem; }
  h1, h2, h3 { font-family: 'Space Grotesk', system-ui, sans-serif; font-weight: 500; }
  .eyebrow { color: var(--cl-accent); font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .index-title { font-size: 2rem; font-weight: 700; margin: 0.4rem 0 0.5rem; }
  .index-lead { color: var(--cl-muted); font-size: 1.05rem; margin-bottom: 2.5rem; }
  .post-card { display: block; padding: 1.5rem 0; border-bottom: 1px solid var(--cl-border); }
  .post-card:hover { text-decoration: none; }
  .post-card h2 { font-size: 1.25rem; margin: 0.2rem 0 0.4rem; color: var(--cl-ink); }
  .post-card:hover h2 { color: var(--cl-accent); }
  .post-card p { color: var(--cl-muted); font-size: 0.95rem; margin: 0; }
  .post-meta { color: var(--cl-muted); font-size: 0.85rem; }
  article h1 { font-size: 1.85rem; font-weight: 700; margin: 0.6rem 0 0.4rem; }
  article .post-meta { margin-bottom: 2rem; }
  article h2 { font-size: 1.25rem; margin-top: 2.2rem; }
  article p, article li { font-size: 1rem; color: var(--cl-ink); }
  article ul, article ol { padding-left: 1.3rem; }
  .callout { background: var(--cl-accent-tint); border-radius: 12px; padding: 1.25rem 1.5rem; margin: 2rem 0; }
  .callout p { margin: 0 0 0.75rem; }
  .callout p:last-child { margin-bottom: 0; }
  nav.back-link { margin-bottom: 1.5rem; font-size: 0.9rem; }
  footer.site { border-top: 1px solid var(--cl-border); padding: 2.5rem 0; }
  footer.site .wrap { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1rem; }
  footer.site .links { display: flex; flex-wrap: wrap; gap: 1.25rem; font-size: 0.88rem; }
  footer.site .copyright { width: 100%; color: var(--cl-muted); font-size: 0.82rem; margin-top: 1rem; }
"""

BLOG_HEAD_EXTRA = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">"""

BLOG_HEADER = """<header class="site">
  <div class="wrap">
    <a class="brand" href="/" style="color:inherit">Change<span class="accent">Ledger</span></a>
    <nav>
      <a href="/blog">Blog</a>
      <a href="/#tarifs">Tarifs</a>
      <a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement</a>
    </nav>
  </div>
</header>"""

BLOG_FOOTER = f"""<footer class="site">
  <div class="wrap">
    <div>
      <div class="brand" style="font-family:'Space Grotesk',system-ui,sans-serif;font-weight:700">Change<span class="accent">Ledger</span></div>
    </div>
    <div class="links">
      <a href="/legal/cgu">CGU</a>
      <a href="/legal/cgv">CGV</a>
      <a href="/legal/confidentialite">Politique de confidentialité</a>
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
    </div>
    <p class="copyright">© 2026 ITEC FRANCE — ChangeLedger est une marque exploitée sous licence.</p>
  </div>
</footer>"""

CTA_CALLOUT = """<div class="callout">
  <p><strong>ChangeLedger surveille vos fournisseurs à votre place.</strong> Ajoutez l'URL de leurs
  CGV, grille tarifaire ou contrat en ligne : vous êtes alerté par email dès qu'un changement est
  détecté, avec un résumé clair de son impact — avant que ça ne vous coûte cher.</p>
  <p><a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement — 14 jours</a></p>
</div>"""


# Chaque article : slug -> (titre, description SEO, date de publication affichée,
# date ISO pour le sitemap, contenu HTML du corps de l'article, sans <h1>/meta).
BLOG_POSTS: dict[str, dict] = {
    "hausse-tarif-fournisseur-sans-preavis": {
        "title": "Hausse de tarif fournisseur sans préavis : comment réagir et s'organiser pour que ça n'arrive plus",
        "description": (
            "Un fournisseur augmente ses tarifs sans vous prévenir ? Voici les réflexes immédiats "
            "pour réagir, et comment mettre en place une veille pour ne plus être pris au dépourvu."
        ),
        "date_display": "24 octobre 2026",
        "date_iso": "2026-10-24",
        "body": """
<p>Vous recevez une facture, ou vous relisez par hasard une grille tarifaire, et vous découvrez
qu'un de vos fournisseurs a augmenté ses prix — sans email, sans courrier, sans que personne ne
vous l'ait signalé. C'est l'un des scénarios les plus fréquents (et les plus coûteux) pour les
entreprises qui travaillent avec de nombreux fournisseurs : la hausse n'est pas cachée, elle est
simplement publiée quelque part que personne ne surveille.</p>

<h2>Pourquoi ça passe inaperçu</h2>
<p>La plupart des fournisseurs ont le droit de modifier leurs conditions générales de vente (CGV)
ou leur grille tarifaire de manière unilatérale, dès lors que le préavis contractuel prévu est
respecté. Ce préavis est souvent très court, parfois limité à la publication d'une nouvelle version
sur leur site — sans notification active. Tant que vous ne relisez pas régulièrement le document,
le changement s'applique sans que vous l'ayez vu venir.</p>

<h2>Les premiers réflexes quand vous découvrez une hausse</h2>
<ul>
<li><strong>Retrouvez le document applicable à la date du changement.</strong> CGV, grille
tarifaire, contrat-cadre : le texte qui fait foi n'est pas toujours celui que vous avez sous la
main. Si possible, comparez l'ancienne et la nouvelle version pour isoler précisément ce qui a
changé.</li>
<li><strong>Vérifiez la clause de révision tarifaire et le préavis contractuel.</strong> Certains
contrats imposent un délai minimum (30, 60, 90 jours) avant toute application d'une hausse, ou une
notification individuelle du client. Si ce délai n'a pas été respecté, vous avez un levier de
négociation, voire un motif de contestation.</li>
<li><strong>Chiffrez l'impact réel sur votre activité</strong>, pas seulement le pourcentage
annoncé : volume commandé, fréquence, poids de ce fournisseur dans vos achats.</li>
<li><strong>Vérifiez les conditions de sortie</strong> (préavis de résiliation, durée d'engagement
restante) avant toute décision — une hausse de tarif peut parfois justifier une résiliation
anticipée si elle dépasse un seuil prévu au contrat.</li>
</ul>

<h2>Comment réagir une fois la situation clarifiée</h2>
<p>Trois options s'offrent généralement à vous, souvent combinables : négocier directement avec
votre interlocuteur habituel en mettant en avant l'ancienneté de la relation et les volumes
engagés ; mettre en concurrence pour objectiver si la hausse reste alignée avec le marché ; ou
accepter la hausse en l'intégrant à votre propre tarification si le fournisseur reste difficilement
substituable. Dans tous les cas, agir vite — avant la date d'application effective — vous laisse
plus de marge de manœuvre qu'une contestation a posteriori.</p>

<h2>Le vrai sujet : ne plus découvrir les hausses après coup</h2>
<p>Réagir correctement une fois la hausse découverte ne résout qu'une partie du problème. La
vraie question est : combien de hausses, de clauses modifiées ou de délais de paiement raccourcis
passent aujourd'hui inaperçus chez vos autres fournisseurs ? Relire manuellement les CGV de chaque
fournisseur à intervalle régulier n'est réaliste que pour une poignée de contrats stratégiques —
au-delà, c'est une charge que peu d'entreprises peuvent se permettre en continu.</p>

%s

<h2>En résumé</h2>
<p>Une hausse tarifaire non annoncée n'est presque jamais illégale : elle est simplement publiée là
où vous ne regardez pas. Le réflexe le plus rentable n'est donc pas seulement de bien réagir une
fois la hausse découverte, mais de mettre en place une veille qui vous alerte au moment où le
changement est publié — pas des semaines ou des mois plus tard, sur une facture.</p>
""" % CTA_CALLOUT,
    },
}


def _post_html(slug: str, post: dict) -> str:
    canonical = f"https://changeledger.io/blog/{slug}"
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{post['title']} — Blog ChangeLedger</title>
<meta name="description" content="{post['description']}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ChangeLedger">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{post['title']}">
<meta property="og:description" content="{post['description']}">
<meta property="og:image" content="https://changeledger.io/og-image.png">
<meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{post['title']}">
<meta name="twitter:description" content="{post['description']}">
<meta name="twitter:image" content="https://changeledger.io/og-image.png">
{BLOG_HEAD_EXTRA}
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{post['title']}",
  "description": "{post['description']}",
  "datePublished": "{post['date_iso']}",
  "author": {{"@type": "Organization", "name": "ChangeLedger"}},
  "publisher": {{"@type": "Organization", "name": "ChangeLedger"}}
}}
</script>
<style>{BLOG_STYLE}</style>
</head>
<body>
{BLOG_HEADER}
<main class="wrap">
  <article>
    <nav class="back-link"><a href="/blog">&larr; Tous les articles</a></nav>
    <p class="eyebrow">Veille fournisseurs</p>
    <h1>{post['title']}</h1>
    <p class="post-meta">Publié le {post['date_display']}</p>
    {post['body']}
  </article>
</main>
{BLOG_FOOTER}
</body>
</html>"""


def _index_html() -> str:
    cards = "\n".join(
        f"""<a class="post-card" href="/blog/{slug}">
      <p class="post-meta">{post['date_display']}</p>
      <h2>{post['title']}</h2>
      <p>{post['description']}</p>
    </a>"""
        for slug, post in sorted(
            BLOG_POSTS.items(), key=lambda kv: kv[1]["date_iso"], reverse=True
        )
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog ChangeLedger — Veille des conditions fournisseurs</title>
<meta name="description" content="Conseils pratiques sur la veille des CGV, tarifs et contrats fournisseurs : comment réagir aux changements, et comment les anticiper.">
<link rel="canonical" href="https://changeledger.io/blog">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ChangeLedger">
<meta property="og:url" content="https://changeledger.io/blog">
<meta property="og:title" content="Blog ChangeLedger — Veille des conditions fournisseurs">
<meta property="og:description" content="Conseils pratiques sur la veille des CGV, tarifs et contrats fournisseurs : comment réagir aux changements, et comment les anticiper.">
<meta property="og:image" content="https://changeledger.io/og-image.png">
<meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://changeledger.io/og-image.png">
{BLOG_HEAD_EXTRA}
<style>{BLOG_STYLE}</style>
</head>
<body>
{BLOG_HEADER}
<main class="wrap">
  <p class="eyebrow">Blog</p>
  <h1 class="index-title">Veille des conditions fournisseurs</h1>
  <p class="index-lead">Conseils pratiques pour réagir aux changements de CGV, de tarifs et de
  contrats fournisseurs — et pour arrêter de les découvrir après coup.</p>
  {cards}
</main>
{BLOG_FOOTER}
</body>
</html>"""


BLOG_INDEX_HTML = _index_html()
BLOG_POST_HTML = {slug: _post_html(slug, post) for slug, post in BLOG_POSTS.items()}
