"""Page d'accueil marketing de ChangeLedger, servie sur le domaine racine
(changeledger.io / www.changeledger.io) — distincte de l'application elle-même,
servie sur app.changeledger.io (voir le routage par domaine dans main.py).

Autonome (HTML/CSS/JS inline), dans le même esprit que app_ui.py, admin_ui.py et
legal_pages.py : aucune dépendance de build, servi directement par l'API. Reprend
l'identité visuelle définie pour l'app (couleurs, typographie, favicon).
"""
from .config import CONTACT_EMAIL

LANDING_HTML = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger — Veille automatisée des conditions fournisseurs</title>
<meta name="description" content="ChangeLedger surveille les CGV, grilles tarifaires et contrats de vos fournisseurs, détecte chaque changement et vous en résume l'impact en langage clair. Essai gratuit de 14 jours.">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    color-scheme: light dark;
    --cl-accent: #4B3FF2;
    --cl-accent-dark: #3A30C2;
    --cl-accent-tint: #EFECFE;
    --cl-ink: #12131A;
    --cl-muted: #5B5E6B;
    --cl-surface: #F6F7FB;
    --cl-border: rgba(17,19,26,0.1);
    --cl-urgent: #E64548;
    --cl-ok: #1F9D63;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; padding: 0; line-height: 1.6; color: var(--cl-ink); background: #ffffff;
  }}
  a {{ color: var(--cl-accent); text-decoration: none; }}
  h1, h2, h3, .brand {{ font-family: 'Space Grotesk', system-ui, sans-serif; }}
  .accent {{ color: var(--cl-accent); }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 1.5rem; }}
  section {{ padding: 4.5rem 0; }}

  header.site {{
    border-bottom: 1px solid var(--cl-border); position: sticky; top: 0; background: rgba(255,255,255,0.92);
    backdrop-filter: blur(6px); z-index: 10;
  }}
  header.site .wrap {{ display: flex; align-items: center; justify-content: space-between; height: 68px; gap: 1rem; }}
  header.site .brand {{ font-weight: 700; font-size: 1.2rem; }}
  header.site nav {{ display: flex; align-items: center; gap: 1.75rem; font-size: 0.92rem; font-weight: 600; }}
  header.site nav a:not(.btn) {{ color: var(--cl-ink); }}
  header.site nav a:not(.btn):hover {{ color: var(--cl-accent); }}
  .nav-login {{ color: var(--cl-muted) !important; font-weight: 600; }}

  .btn {{
    display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem;
    padding: 0.7rem 1.3rem; border-radius: 8px; font-weight: 600; font-size: 0.95rem;
    border: none; cursor: pointer; white-space: nowrap;
  }}
  .btn-primary {{ background: var(--cl-accent); color: #fff; }}
  .btn-primary:hover {{ background: var(--cl-accent-dark); }}
  .btn-secondary {{ background: #fff; color: var(--cl-ink); border: 1px solid var(--cl-border); }}
  .btn-secondary:hover {{ background: var(--cl-surface); }}

  .hero {{ padding: 4.5rem 0 3rem; }}
  .hero .wrap {{ display: flex; gap: 3rem; align-items: center; flex-wrap: wrap; }}
  .hero-copy {{ flex: 1 1 440px; min-width: 0; }}
  .hero h1 {{ font-size: clamp(2rem, 4.2vw, 2.9rem); line-height: 1.12; margin: 0 0 1.1rem; font-weight: 700; }}
  .hero p.lead {{ font-size: 1.1rem; color: var(--cl-muted); margin: 0 0 1.6rem; max-width: 520px; }}
  .hero .cta-row {{ display: flex; gap: 0.9rem; align-items: center; flex-wrap: wrap; }}
  .hero .reassure {{ margin-top: 0.8rem; font-size: 0.85rem; color: var(--cl-muted); }}

  .demo-card {{ flex: 1 1 360px; min-width: 300px; max-width: 420px; }}
  .demo-label {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--cl-muted); margin-bottom: 0.6rem; }}
  .alert-card {{
    background: #fff; border: 1px solid var(--cl-border); border-radius: 12px; padding: 1.4rem;
    box-shadow: 0 12px 32px rgba(17,19,26,0.08);
  }}
  .alert-badge {{
    display: inline-block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
    color: #fff; background: var(--cl-urgent); padding: 0.25rem 0.6rem; border-radius: 999px; margin-bottom: 0.7rem;
  }}
  .alert-card h4 {{ margin: 0 0 0.3rem; font-size: 1rem; font-family: inherit; font-weight: 700; }}
  .alert-card p {{ margin: 0; font-size: 0.88rem; color: var(--cl-muted); }}
  .alert-card .summary {{ margin-top: 0.7rem; font-size: 0.9rem; color: var(--cl-ink); }}

  .features {{ background: var(--cl-surface); }}
  h2 {{ font-size: 1.8rem; margin: 0 0 0.5rem; font-weight: 700; }}
  .section-lead {{ color: var(--cl-muted); font-size: 1.02rem; max-width: 560px; margin: 0 0 2.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); gap: 1.5rem; }}
  .feature-card {{ background: #fff; border: 1px solid var(--cl-border); border-radius: 12px; padding: 1.5rem; }}
  .feature-card h3 {{ font-size: 1.02rem; margin: 0 0 0.5rem; font-weight: 500; }}
  .feature-card p {{ margin: 0; font-size: 0.9rem; color: var(--cl-muted); }}

  .audience .grid {{ grid-template-columns: repeat(auto-fit, minmax(min(260px, 100%), 1fr)); }}
  .audience-card h3 {{ font-size: 1.02rem; margin: 0 0 0.5rem; font-weight: 500; }}
  .audience-card p {{ margin: 0; font-size: 0.9rem; color: var(--cl-muted); }}

  .steps {{ counter-reset: step; }}
  .steps .grid {{ grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); }}
  .step-card {{ position: relative; padding-top: 2.6rem; }}
  .step-card::before {{
    counter-increment: step; content: counter(step); position: absolute; top: 0; left: 0;
    width: 2.1rem; height: 2.1rem; border-radius: 50%; background: var(--cl-accent-tint); color: var(--cl-accent);
    font-family: 'Space Grotesk', system-ui, sans-serif; font-weight: 700; display: flex; align-items: center; justify-content: center;
  }}
  .step-card h3 {{ font-size: 1.02rem; margin: 0 0 0.4rem; font-weight: 500; }}
  .step-card p {{ margin: 0; font-size: 0.9rem; color: var(--cl-muted); }}

  .pricing {{ background: var(--cl-surface); }}
  .cycle-toggle {{ display: inline-flex; background: #fff; border: 1px solid var(--cl-border); border-radius: 8px; padding: 4px; margin-bottom: 2.2rem; }}
  .cycle-toggle button {{
    border: none; background: none; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; font-size: 0.88rem;
    cursor: pointer; color: var(--cl-muted); font-family: inherit;
  }}
  .cycle-toggle button.active {{ background: var(--cl-accent); color: #fff; }}
  .plans {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(270px, 100%), 1fr)); gap: 1.5rem; }}
  .plan-card {{ background: #fff; border: 1px solid var(--cl-border); border-radius: 14px; padding: 1.8rem; display: flex; flex-direction: column; gap: 1rem; }}
  .plan-card.highlight {{ border: 2px solid var(--cl-accent); position: relative; }}
  .plan-badge {{
    position: absolute; top: -0.7rem; left: 1.5rem; background: var(--cl-accent); color: #fff; font-size: 0.72rem;
    font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 999px; letter-spacing: 0.02em;
  }}
  .plan-name {{ font-size: 1.1rem; font-weight: 700; font-family: 'Space Grotesk', system-ui, sans-serif; }}
  .plan-price {{ font-size: 2rem; font-weight: 700; font-family: 'Space Grotesk', system-ui, sans-serif; }}
  .plan-price span {{ font-size: 0.95rem; font-weight: 500; color: var(--cl-muted); font-family: 'Plus Jakarta Sans', sans-serif; }}
  .plan-sub {{ font-size: 0.85rem; color: var(--cl-muted); margin-top: -0.6rem; }}
  .plan-features {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.55rem; font-size: 0.9rem; }}
  .plan-features li {{ padding-left: 1.3rem; position: relative; }}
  .plan-features li::before {{ content: "✓"; position: absolute; left: 0; color: var(--cl-accent); font-weight: 700; }}

  .cta-band {{ text-align: center; }}
  .cta-band h2 {{ font-size: 1.9rem; }}
  .cta-band .section-lead {{ margin-left: auto; margin-right: auto; }}
  .cta-band .cta-row {{ justify-content: center; }}

  footer.site {{ border-top: 1px solid var(--cl-border); padding: 2.5rem 0; }}
  footer.site .wrap {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1.5rem; align-items: flex-start; }}
  footer.site .brand {{ font-weight: 700; font-size: 1.05rem; margin-bottom: 0.4rem; }}
  footer.site .tagline {{ font-size: 0.85rem; color: var(--cl-muted); max-width: 260px; }}
  footer.site .links {{ display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.88rem; }}
  footer.site .links a {{ color: var(--cl-muted); }}
  footer.site .links a:hover {{ color: var(--cl-accent); }}
  footer.site .copyright {{ width: 100%; margin-top: 1.8rem; padding-top: 1.3rem; border-top: 1px solid var(--cl-border); font-size: 0.8rem; color: var(--cl-muted); }}

  @media (max-width: 640px) {{
    header.site nav {{ gap: 1rem; }}
    header.site nav .nav-link-desktop {{ display: none; }}
    section {{ padding: 3rem 0; }}
  }}
</style>
</head>
<body>

<header class="site">
  <div class="wrap">
    <div class="brand">Change<span class="accent">Ledger</span></div>
    <nav>
      <a class="nav-link-desktop" href="#fonctionnalites">Fonctionnalités</a>
      <a class="nav-link-desktop" href="#tarifs">Tarifs</a>
      <a class="nav-login" href="https://app.changeledger.io/app">Se connecter</a>
      <a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement</a>
    </nav>
  </div>
</header>

<section class="hero">
  <div class="wrap">
    <div class="hero-copy">
      <h1>Vos fournisseurs changent leurs conditions. Vous ne devriez pas être le dernier au courant.</h1>
      <p class="lead">ChangeLedger surveille en continu les CGV, grilles tarifaires et contrats de vos
      fournisseurs, détecte chaque changement et vous en résume l'impact en langage clair — avant que
      ça ne vous coûte cher.</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement — 14 jours</a>
        <a class="btn btn-secondary" href="#tarifs">Voir les tarifs</a>
      </div>
      <p class="reassure">Carte bancaire enregistrée à l'inscription, aucun prélèvement avant la fin de
      l'essai, résiliable à tout moment depuis votre compte.</p>
    </div>
    <div class="demo-card">
      <div class="demo-label">Exemple d'alerte reçue par email</div>
      <div class="alert-card">
        <span class="alert-badge">Urgent</span>
        <h4>Alpha Logistique</h4>
        <p>CGV — changement détecté aujourd'hui</p>
        <p class="summary">Hausse de 8% des frais de surestarie, applicable dès le mois prochain.</p>
      </div>
    </div>
  </div>
</section>

<section class="features" id="fonctionnalites">
  <div class="wrap">
    <h2>Pourquoi ChangeLedger</h2>
    <p class="section-lead">Quatre raisons pour lesquelles les entreprises qui travaillent avec de
    nombreux fournisseurs arrêtent de relire leurs CGV à la main.</p>
    <div class="grid">
      <div class="feature-card">
        <h3>Fini la relecture manuelle</h3>
        <p>Vous n'avez plus à repasser derrière chaque fournisseur pour vérifier si ses conditions ont
        bougé : ChangeLedger le fait pour vous, en continu.</p>
      </div>
      <div class="feature-card">
        <h3>Soyez alerté avant que ça coûte cher</h3>
        <p>Hausse tarifaire, délai de paiement raccourci, clause de responsabilité modifiée : vous êtes
        informé dès la publication du changement, pas des mois après.</p>
      </div>
      <div class="feature-card">
        <h3>Résumé clair, pas de jargon juridique</h3>
        <p>Chaque changement est classé par catégorie et sévérité, puis résumé en langage clair par
        l'IA — vous savez en une phrase si ça mérite votre attention.</p>
      </div>
      <div class="feature-card">
        <h3>14 jours pour juger sur pièces</h3>
        <p>Testez ChangeLedger sur vos vraies sources pendant 14 jours. Résiliable à tout moment depuis
        votre espace, en un clic.</p>
      </div>
    </div>
  </div>
</section>

<section class="audience">
  <div class="wrap">
    <h2>Pour qui</h2>
    <p class="section-lead">ChangeLedger est pensé pour celles et ceux qui doivent suivre les conditions
    de plusieurs fournisseurs sans pouvoir y consacrer une veille à temps plein.</p>
    <div class="grid">
      <div class="audience-card">
        <h3>PME &amp; artisans multi-fournisseurs</h3>
        <p>Vous travaillez avec de nombreux fournisseurs et n'avez ni le temps ni l'équipe pour relire
        leurs CGV à chaque renouvellement.</p>
      </div>
      <div class="audience-card">
        <h3>Services achats &amp; approvisionnement</h3>
        <p>Vous devez sécuriser vos conditions d'achat sans transformer ça en veille à temps plein pour
        votre équipe.</p>
      </div>
      <div class="audience-card">
        <h3>Juridique &amp; conformité</h3>
        <p>Vous devez pouvoir démontrer que les évolutions contractuelles de vos fournisseurs sont
        suivies et tracées dans le temps.</p>
      </div>
      <div class="audience-card">
        <h3>Plateformes &amp; secteurs à forte dépendance tierce</h3>
        <p>Hubs qui connectent les acteurs d'une industrie, grande distribution, e-commerce,
        marketplaces, trading, fintech et cryptomonnaies, éditeurs SaaS : dans ces environnements
        concurrentiels et réglementés, un changement de conditions chez un partenaire peut impacter
        directement votre activité — vous ne pouvez pas vous permettre de le découvrir en retard.</p>
      </div>
    </div>
  </div>
</section>

<section class="steps features">
  <div class="wrap">
    <h2>Comment ça marche</h2>
    <p class="section-lead">Trois étapes, aucune intégration technique requise.</p>
    <div class="grid">
      <div class="step-card">
        <h3>Choisissez un palier</h3>
        <p>Essentiel ou Pro, essai de 14 jours inclus — résiliable à tout moment.</p>
      </div>
      <div class="step-card">
        <h3>Ajoutez vos sources</h3>
        <p>CGV, grille tarifaire, contrat accessible en ligne : collez simplement l'URL à surveiller.</p>
      </div>
      <div class="step-card">
        <h3>Recevez vos alertes</h3>
        <p>Par email, et si vous le souhaitez sur Slack ou un webhook, dès qu'un changement est détecté.</p>
      </div>
    </div>
  </div>
</section>

<section class="pricing" id="tarifs">
  <div class="wrap">
    <h2>Tarifs</h2>
    <p class="section-lead">Deux paliers en libre-service, un palier sur mesure pour les besoins plus
    importants. Essai de 14 jours inclus sur Essentiel et Pro.</p>

    <div class="cycle-toggle">
      <button type="button" class="active" onclick="setCycle('monthly')" id="cycleMonthlyBtn">Mensuel</button>
      <button type="button" onclick="setCycle('annual')" id="cycleAnnualBtn">Annuel</button>
    </div>

    <div class="plans">
      <div class="plan-card">
        <div class="plan-name">Essentiel</div>
        <div class="plan-price"><span class="price-monthly">29&nbsp;€<span>/mois</span></span><span class="price-annual" style="display:none">290&nbsp;€<span>/an</span></span></div>
        <div class="plan-sub">Jusqu'à 5 sources surveillées</div>
        <ul class="plan-features">
          <li>Classification et résumé des changements par IA</li>
          <li>Alertes par email</li>
          <li>Webhook (Slack, Zapier, maison)</li>
          <li>Historique des changements</li>
        </ul>
        <a class="btn btn-secondary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement</a>
      </div>

      <div class="plan-card highlight">
        <span class="plan-badge">Le plus choisi</span>
        <div class="plan-name">Pro</div>
        <div class="plan-price"><span class="price-monthly">59&nbsp;€<span>/mois</span></span><span class="price-annual" style="display:none">590&nbsp;€<span>/an</span></span></div>
        <div class="plan-sub">Jusqu'à 25 sources surveillées</div>
        <ul class="plan-features">
          <li>Classification et résumé des changements par IA</li>
          <li>Alertes par email</li>
          <li>Webhook (Slack, Zapier, maison)</li>
          <li>Historique des changements</li>
        </ul>
        <a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement</a>
      </div>

      <div class="plan-card">
        <div class="plan-name">Entreprise</div>
        <div class="plan-price" style="font-size:1.3rem">Sur mesure</div>
        <div class="plan-sub">Sources illimitées, activation après contact commercial</div>
        <ul class="plan-features">
          <li>Tout Pro, sans limite de sources</li>
          <li>Accompagnement à la mise en place</li>
        </ul>
        <a class="btn btn-secondary" href="mailto:{CONTACT_EMAIL}">Nous contacter</a>
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="wrap">
    <h2>Prêt à ne plus être pris au dépourvu par vos fournisseurs ?</h2>
    <p class="section-lead">14 jours d'essai gratuit, sans engagement.</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="https://app.changeledger.io/app?signup=1">Essayer gratuitement</a>
    </div>
  </div>
</section>

<footer class="site">
  <div class="wrap">
    <div>
      <div class="brand">Change<span class="accent">Ledger</span></div>
      <p class="tagline">Veille automatisée des conditions fournisseurs.</p>
    </div>
    <div class="links">
      <a href="/legal/cgu">CGU</a>
      <a href="/legal/cgv">CGV</a>
      <a href="/legal/confidentialite">Politique de confidentialité</a>
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
    </div>
    <p class="copyright">© 2026 ITEC FRANCE — ChangeLedger est une marque exploitée sous licence.</p>
  </div>
</footer>

<script>
function setCycle(cycle) {{
  const monthly = cycle === "monthly";
  document.getElementById("cycleMonthlyBtn").classList.toggle("active", monthly);
  document.getElementById("cycleAnnualBtn").classList.toggle("active", !monthly);
  document.querySelectorAll(".price-monthly").forEach(el => el.style.display = monthly ? "" : "none");
  document.querySelectorAll(".price-annual").forEach(el => el.style.display = monthly ? "none" : "");
}}
</script>

</body>
</html>
"""
