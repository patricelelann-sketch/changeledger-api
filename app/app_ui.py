"""Frontend minimal de ChangeLedger : inscription/connexion, gestion des sources
et de l'historique des changements, compte (palier, facturation, webhook).

Autonome, comme admin_ui.py : une seule page HTML, CSS et JS inline, aucune
dépendance de build. Le token JWT est stocké dans localStorage (persistant,
cohérent avec la durée de vie de 7 jours du token côté API) ; le secret admin
de admin_ui.py reste lui en sessionStorage, par choix distinct (surface plus
sensible, durée de vie volontairement plus courte).
"""

APP_UI_HTML = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; padding: 0; line-height: 1.5; color: #111827; background: #f9fafb;
  }
  .hidden { display: none !important; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* --- Barre du haut (visible une fois connecté) --- */
  #topbar {
    display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1.25rem;
    background: white; border-bottom: 1px solid #e5e7eb;
  }
  #topbar .brand { font-weight: 700; font-size: 1.1rem; margin-right: auto; }
  #topbar nav { display: flex; gap: 0.4rem; }
  .tab {
    background: none; border: none; padding: 0.4rem 0.8rem; border-radius: 6px;
    cursor: pointer; font-size: 0.9rem; color: #4b5563;
  }
  .tab.active { background: #111827; color: white; }

  main { max-width: 760px; margin: 0 auto; padding: 1.5rem 1rem 4rem; }

  .card {
    background: white; border: 1px solid #e5e7eb; border-radius: 10px;
    padding: 1.25rem 1.5rem; margin-bottom: 1.25rem;
  }
  .card.narrow { max-width: 420px; margin: 3rem auto; }

  h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
  h2 { font-size: 1.1rem; margin: 0 0 0.9rem; }
  .muted { color: #6b7280; font-size: 0.9rem; }

  input, select, button, textarea {
    font-size: 0.95rem; padding: 0.5rem 0.7rem; border-radius: 6px;
    border: 1px solid #d1d5db; font-family: inherit;
  }
  input, select, textarea { width: 100%; margin-bottom: 0.6rem; background: white; color: inherit; }
  button {
    background: #111827; color: white; border: none; cursor: pointer; white-space: nowrap;
  }
  button:hover { background: #374151; }
  button:disabled { background: #9ca3af; cursor: not-allowed; }
  button.secondary { background: white; color: #111827; border: 1px solid #d1d5db; }
  button.secondary:hover { background: #f3f4f6; }
  button.danger { background: white; color: #b91c1c; border: 1px solid #fecaca; }
  button.danger:hover { background: #fef2f2; }

  .row { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: flex-start; }
  .row > * { margin-bottom: 0; }
  .links { font-size: 0.9rem; margin-top: 0.8rem; }
  .legal-footer { max-width: 760px; margin: 2rem auto 1rem; padding: 0 1rem; text-align: center; font-size: 0.8rem; color: #6b7280; }
  .legal-footer a { color: #6b7280; }
  .consent-note { font-size: 0.8rem; color: #6b7280; margin-top: 0.6rem; }
  .consent-note a { color: inherit; }

  .msg { margin: 0.6rem 0; font-size: 0.9rem; min-height: 1.2em; }
  .msg.error { color: #b91c1c; }
  .msg.success { color: #15803d; }

  table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
  th, td { text-align: left; padding: 0.5rem 0.5rem; border-bottom: 1px solid #e5e7eb; font-size: 0.88rem; vertical-align: top; }
  th { color: #6b7280; font-weight: 600; }
  td.actions { white-space: nowrap; }
  td.actions button { margin-right: 0.3rem; margin-bottom: 0.3rem; font-size: 0.82rem; padding: 0.3rem 0.5rem; }

  .badge {
    display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600;
  }
  .badge.urgent { background: #fef2f2; color: #b91c1c; }
  .badge.attention { background: #fffbeb; color: #92400e; }
  .badge.info { background: #eff6ff; color: #1e40af; }

  .change-item { padding: 0.75rem 0; border-bottom: 1px solid #f3f4f6; }
  .change-item:last-child { border-bottom: none; }
  .change-head { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .change-source { font-weight: 600; font-size: 0.9rem; }
  .change-date { color: #9ca3af; font-size: 0.82rem; margin-left: auto; }
  .change-summary { margin: 0.35rem 0 0.2rem; font-size: 0.92rem; }
  pre.diff {
    background: #0b1020; color: #e5e7eb; padding: 0.75rem; border-radius: 6px;
    overflow-x: auto; font-size: 0.78rem; max-height: 280px;
  }

  .plan-usage { font-size: 0.9rem; margin-bottom: 0.9rem; }
  .plan-usage.limit-reached { color: #b91c1c; }
</style>
</head>
<body>

<header id="topbar" class="hidden">
  <div class="brand">ChangeLedger</div>
  <nav>
    <button class="tab active" data-tab="sources" onclick="showTab('sources')">Sources</button>
    <button class="tab" data-tab="account" onclick="showTab('account')">Compte</button>
  </nav>
  <button class="secondary" onclick="logout()">Déconnexion</button>
</header>

<!-- ======================= Authentification ======================= -->
<main id="authView">
  <div class="card narrow">
    <h1>ChangeLedger</h1>
    <p class="muted">Veille des conditions fournisseurs (CGV, tarifs, contrats).</p>

    <div id="loginForm">
      <h2>Connexion</h2>
      <input id="loginEmail" type="email" placeholder="Email" autocomplete="username">
      <input id="loginPassword" type="password" placeholder="Mot de passe" autocomplete="current-password">
      <button onclick="login()" style="width:100%">Se connecter</button>
      <p class="links">
        <a href="#" onclick="showAuthSubview('signup'); return false;">Créer un compte</a>
        ·
        <a href="#" onclick="showAuthSubview('forgot'); return false;">Mot de passe oublié ?</a>
      </p>
      <div class="msg" id="loginMsg"></div>
    </div>

    <div id="signupForm" class="hidden">
      <h2>Créer un compte</h2>
      <p class="muted">Réservé aux professionnels (entreprises, indépendants, associations).</p>
      <input id="signupEmail" type="email" placeholder="Email" autocomplete="username">
      <input id="signupPassword" type="password" placeholder="Mot de passe (8 caractères min.)" autocomplete="new-password">
      <button onclick="signup()" style="width:100%">Créer mon compte</button>
      <p class="consent-note">En créant un compte, tu acceptes les
        <a href="/legal/cgu" target="_blank">CGU</a>, les
        <a href="/legal/cgv" target="_blank">CGV</a> et la
        <a href="/legal/confidentialite" target="_blank">politique de confidentialité</a>.</p>
      <p class="links"><a href="#" onclick="showAuthSubview('login'); return false;">J'ai déjà un compte</a></p>
      <div class="msg" id="signupMsg"></div>
    </div>

    <div id="forgotForm" class="hidden">
      <h2>Mot de passe oublié</h2>
      <p class="muted">Un lien de réinitialisation sera envoyé par email si le compte existe.</p>
      <input id="forgotEmail" type="email" placeholder="Email" autocomplete="username">
      <button onclick="forgotPassword()" style="width:100%">Envoyer le lien</button>
      <p class="links"><a href="#" onclick="showAuthSubview('login'); return false;">Retour à la connexion</a></p>
      <div class="msg" id="forgotMsg"></div>
    </div>

    <div id="resetForm" class="hidden">
      <h2>Réinitialiser le mot de passe</h2>
      <input id="resetPassword" type="password" placeholder="Nouveau mot de passe (8 caractères min.)" autocomplete="new-password">
      <button onclick="resetPassword()" style="width:100%">Réinitialiser</button>
      <p class="links"><a href="#" onclick="showAuthSubview('login'); return false;">Retour à la connexion</a></p>
      <div class="msg" id="resetMsg"></div>
    </div>
  </div>
</main>

<!-- ======================= Application (connecté) ======================= -->
<main id="appView" class="hidden">

  <section id="sourcesTab">
    <div class="card">
      <h2>Ajouter une source à surveiller</h2>
      <div class="row">
        <input id="newSupplier" placeholder="Fournisseur (ex. Acme SAS)" style="flex:1; min-width: 160px">
        <input id="newLabel" placeholder="Libellé (ex. CGV) — optionnel" style="flex:1; min-width: 160px">
      </div>
      <input id="newUrl" placeholder="https://exemple.com/cgv">
      <button id="addSourceBtn" onclick="addSource()">Ajouter la source</button>
      <div class="msg" id="addSourceMsg"></div>
    </div>

    <div class="card">
      <h2>Sources surveillées</h2>
      <div class="plan-usage" id="planUsage"></div>
      <table>
        <thead>
          <tr><th>Fournisseur</th><th>Libellé</th><th>URL</th><th>Ajoutée le</th><th>Actions</th></tr>
        </thead>
        <tbody id="sourcesBody"></tbody>
      </table>
      <p class="muted" id="noSources" style="display:none">Aucune source surveillée pour le moment.</p>
    </div>

    <div class="card">
      <h2>Changements détectés</h2>
      <div class="row" style="margin-bottom:0.6rem">
        <select id="changeFilter" onchange="loadChanges()" style="max-width: 280px">
          <option value="">Toutes les sources</option>
        </select>
        <button class="secondary" onclick="loadChanges()">Rafraîchir</button>
      </div>
      <div id="changesList"></div>
      <p class="muted" id="noChanges" style="display:none">Aucun changement détecté pour le moment.</p>
    </div>
  </section>

  <section id="accountTab" class="hidden">
    <div class="card">
      <h2>Mon compte</h2>
      <p><strong id="accountEmail"></strong></p>
      <p class="muted">Palier actuel : <strong id="accountPlan"></strong> — Abonnement : <span id="accountStatus"></span></p>
      <p class="muted" id="trialNote" style="display:none">Essai en cours — surveillance active sur tes sources, tu seras alerté dès qu'un changement est détecté. La carte enregistrée sera débitée automatiquement à la fin de l'essai, sauf annulation.</p>
      <div class="row" id="billingActions"></div>
      <div class="msg" id="billingMsg"></div>
    </div>

    <div class="card">
      <h2>Alertes webhook</h2>
      <p class="muted">En complément de l'email, reçois chaque alerte de changement sur une URL de ton choix
      (compatible avec un webhook entrant Slack, Zapier, ou un endpoint maison). Laisse vide pour désactiver.</p>
      <input id="webhookUrl" placeholder="https://hooks.slack.com/services/...">
      <div class="row">
        <button onclick="saveWebhook()">Enregistrer</button>
        <button class="secondary" onclick="clearWebhook()">Désactiver</button>
      </div>
      <div class="msg" id="webhookMsg"></div>
    </div>

    <div class="card">
      <h2>Mot de passe</h2>
      <p class="muted">Aucun changement de mot de passe directement ici : un lien de réinitialisation
      te sera envoyé par email, comme pour un mot de passe oublié.</p>
      <button class="secondary" onclick="sendSelfPasswordReset()">Envoyer un lien de réinitialisation</button>
      <div class="msg" id="passwordMsg"></div>
    </div>
  </section>

</main>

<footer class="legal-footer">
  ChangeLedger — <a href="/legal/cgu" target="_blank">CGU</a> ·
  <a href="/legal/cgv" target="_blank">CGV</a> ·
  <a href="/legal/confidentialite" target="_blank">Politique de confidentialité</a>
</footer>

<script>
const TOKEN_KEY = "changeledger_token";
const PLAN_LABELS = { none: "Aucun", essentiel: "Essentiel", pro: "Pro", entreprise: "Entreprise" };
const PLAN_LIMITS = { none: 0, essentiel: 5, pro: 25, entreprise: null };
const CATEGORY_LABELS = { tarif: "Tarif", resiliation: "Résiliation", paiement: "Paiement", responsabilite: "Responsabilité", autre: "Autre" };
const SEVERITY_LABELS = { urgent: "Urgent", attention: "À vérifier", info: "Info" };
const STATUS_LABELS = { trialing: "Essai en cours", active: "Actif", past_due: "Paiement en retard", canceled: "Annulé" };

let currentUser = null;
let sources = [];

function getToken() { return localStorage.getItem(TOKEN_KEY) || ""; }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function extractErrorMessage(body) {
  if (!body) return "Erreur inattendue.";
  const d = body.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) return d.map((e) => e.msg).join(" ");
  return "Erreur inattendue.";
}

function setMsg(id, text, kind) {
  const el = document.getElementById(id);
  el.textContent = text || "";
  el.className = "msg " + (kind || "");
}

// --- Appel API générique : ajoute le token, gère l'expiration/invalidité (401) ---
async function apiFetch(path, options) {
  options = options || {};
  const headers = Object.assign({}, options.headers || {});
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(path, Object.assign({}, options, { headers }));
  if (res.status === 401 && token) {
    clearToken();
    showAuthView();
    setMsg("loginMsg", "Ta session a expiré, reconnecte-toi.", "error");
  }
  return res;
}

// --- Vues : authentification vs application ---

function showAuthView() {
  document.getElementById("topbar").classList.add("hidden");
  document.getElementById("appView").classList.add("hidden");
  document.getElementById("authView").classList.remove("hidden");
}

function showAuthSubview(name) {
  ["login", "signup", "forgot", "reset"].forEach((n) => {
    document.getElementById(n + "Form").classList.toggle("hidden", n !== name);
  });
}

function showApp() {
  document.getElementById("authView").classList.add("hidden");
  document.getElementById("topbar").classList.remove("hidden");
  document.getElementById("appView").classList.remove("hidden");
}

function showTab(name) {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });
  document.getElementById("sourcesTab").classList.toggle("hidden", name !== "sources");
  document.getElementById("accountTab").classList.toggle("hidden", name !== "account");
}

function logout() {
  clearToken();
  currentUser = null;
  sources = [];
  showAuthView();
  showAuthSubview("login");
}

// --- Authentification ---

async function doLogin(email, password) {
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(extractErrorMessage(body));
  setToken(body.access_token);
}

async function login() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  setMsg("loginMsg", "Connexion...", "");
  try {
    await doLogin(email, password);
    setMsg("loginMsg", "", "");
    await afterLogin();
  } catch (err) {
    setMsg("loginMsg", err.message, "error");
  }
}

async function signup() {
  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;
  setMsg("signupMsg", "Création du compte...", "");
  try {
    const res = await fetch("/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    await doLogin(email, password);
    setMsg("signupMsg", "", "");
    await afterLogin();
  } catch (err) {
    setMsg("signupMsg", err.message, "error");
  }
}

async function forgotPassword() {
  const email = document.getElementById("forgotEmail").value.trim();
  setMsg("forgotMsg", "Envoi en cours...", "");
  try {
    const res = await fetch("/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    setMsg("forgotMsg", body.message || "Si un compte existe, un email a été envoyé.", "success");
  } catch (err) {
    setMsg("forgotMsg", err.message, "error");
  }
}

let resetTokenValue = "";

async function resetPassword() {
  const new_password = document.getElementById("resetPassword").value;
  setMsg("resetMsg", "Réinitialisation...", "");
  try {
    const res = await fetch("/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: resetTokenValue, new_password }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    setMsg("resetMsg", "Mot de passe réinitialisé. Tu peux te connecter.", "success");
    setTimeout(() => showAuthSubview("login"), 1500);
  } catch (err) {
    setMsg("resetMsg", err.message, "error");
  }
}

// --- Après connexion : charger les données et afficher l'application ---

async function afterLogin() {
  const res = await apiFetch("/auth/me");
  if (!res.ok) return;
  currentUser = await res.json();
  showApp();
  showTab("sources");
  await Promise.all([loadSources(), loadChanges()]);
  renderAccount();
  applyPendingCheckoutMessage();
}

// --- Sources ---

async function loadSources() {
  const res = await apiFetch("/sources");
  if (!res.ok) return;
  sources = await res.json();
  renderSources();
  renderChangeFilter();
}

function renderSources() {
  const body = document.getElementById("sourcesBody");
  body.innerHTML = "";
  document.getElementById("noSources").style.display = sources.length ? "none" : "block";
  for (const s of sources) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(s.supplier_name)}</td>
      <td>${escapeHtml(s.label || "—")}</td>
      <td><a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.url)}</a></td>
      <td>${escapeHtml((s.created_at || "").slice(0, 10))}</td>
      <td class="actions">
        <button class="secondary" data-check="${escapeHtml(s.id)}">Vérifier</button>
        <button class="danger" data-delete="${escapeHtml(s.id)}">Supprimer</button>
      </td>
    `;
    body.appendChild(tr);
  }
  body.querySelectorAll("button[data-check]").forEach((btn) => {
    btn.addEventListener("click", () => checkSource(btn.getAttribute("data-check")));
  });
  body.querySelectorAll("button[data-delete]").forEach((btn) => {
    btn.addEventListener("click", () => deleteSource(btn.getAttribute("data-delete")));
  });

  const plan = currentUser ? currentUser.plan : "none";
  const limit = PLAN_LIMITS[plan];
  const usageEl = document.getElementById("planUsage");
  const addBtn = document.getElementById("addSourceBtn");
  if (limit === null || limit === undefined) {
    usageEl.textContent = "Palier " + (PLAN_LABELS[plan] || plan) + " — sources illimitées.";
    usageEl.className = "plan-usage";
    addBtn.disabled = false;
  } else {
    const reached = sources.length >= limit;
    usageEl.textContent =
      "Palier " + (PLAN_LABELS[plan] || plan) + " — " + sources.length + " / " + limit + " sources utilisées" +
      (reached ? " (limite atteinte, passe à un palier supérieur dans l'onglet Compte)." : ".");
    usageEl.className = "plan-usage" + (reached ? " limit-reached" : "");
    addBtn.disabled = reached;
  }
}

async function addSource() {
  const supplier_name = document.getElementById("newSupplier").value.trim();
  const label = document.getElementById("newLabel").value.trim();
  const url = document.getElementById("newUrl").value.trim();
  setMsg("addSourceMsg", "Ajout en cours...", "");
  try {
    const res = await apiFetch("/sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ supplier_name, label: label || null, url }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    document.getElementById("newSupplier").value = "";
    document.getElementById("newLabel").value = "";
    document.getElementById("newUrl").value = "";
    setMsg("addSourceMsg", "Source ajoutée.", "success");
    await loadSources();
  } catch (err) {
    setMsg("addSourceMsg", err.message, "error");
  }
}

async function checkSource(id) {
  setMsg("addSourceMsg", "Vérification en cours...", "");
  try {
    const res = await apiFetch("/sources/" + id + "/check", { method: "POST" });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    setMsg("addSourceMsg", body.message || "Vérification terminée.", "success");
    await loadChanges();
  } catch (err) {
    setMsg("addSourceMsg", err.message, "error");
  }
}

async function deleteSource(id) {
  if (!confirm("Supprimer cette source et tout son historique de changements ?")) return;
  try {
    const res = await apiFetch("/sources/" + id, { method: "DELETE" });
    if (!res.ok && res.status !== 204) {
      const body = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(body));
    }
    await loadSources();
    await loadChanges();
  } catch (err) {
    setMsg("addSourceMsg", err.message, "error");
  }
}

// --- Changements ---

function renderChangeFilter() {
  const select = document.getElementById("changeFilter");
  const current = select.value;
  select.innerHTML = '<option value="">Toutes les sources</option>';
  for (const s of sources) {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.supplier_name + (s.label ? " (" + s.label + ")" : "");
    select.appendChild(opt);
  }
  select.value = current || "";
}

async function loadChanges() {
  const sourceId = document.getElementById("changeFilter").value;
  const qs = sourceId ? "?source_id=" + encodeURIComponent(sourceId) : "";
  const res = await apiFetch("/changes" + qs);
  if (!res.ok) return;
  const changes = await res.json();
  renderChanges(changes);
}

function renderChanges(changes) {
  const list = document.getElementById("changesList");
  list.innerHTML = "";
  document.getElementById("noChanges").style.display = changes.length ? "none" : "block";
  const sourceById = {};
  for (const s of sources) sourceById[s.id] = s;

  for (const c of changes) {
    const source = sourceById[c.source_id];
    const div = document.createElement("div");
    div.className = "change-item";
    const diffId = "diff-" + c.id;
    div.innerHTML = `
      <div class="change-head">
        <span class="badge ${escapeHtml(c.severity)}">${escapeHtml(SEVERITY_LABELS[c.severity] || c.severity)}</span>
        <span class="change-source">${escapeHtml(source ? source.supplier_name : c.source_id)}</span>
        <span class="muted">${escapeHtml(CATEGORY_LABELS[c.category] || c.category)}</span>
        <span class="change-date">${escapeHtml((c.detected_at || "").slice(0, 16).replace("T", " "))}</span>
      </div>
      <div class="change-summary">${escapeHtml(c.summary || "Résumé indisponible.")}</div>
      <button class="secondary" data-toggle-diff="${diffId}">Voir le diff</button>
      <pre class="diff hidden" id="${diffId}">${escapeHtml(c.diff_text)}</pre>
    `;
    list.appendChild(div);
  }
  list.querySelectorAll("button[data-toggle-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById(btn.getAttribute("data-toggle-diff")).classList.toggle("hidden");
    });
  });
}

// --- Compte / facturation / webhook ---

function renderAccount() {
  if (!currentUser) return;
  document.getElementById("accountEmail").textContent = currentUser.email;
  document.getElementById("accountPlan").textContent = PLAN_LABELS[currentUser.plan] || currentUser.plan;
  document.getElementById("accountStatus").textContent =
    STATUS_LABELS[currentUser.subscription_status] || currentUser.subscription_status || "—";
  document.getElementById("trialNote").style.display =
    currentUser.subscription_status === "trialing" ? "block" : "none";
  document.getElementById("webhookUrl").value = currentUser.webhook_url || "";

  const actions = document.getElementById("billingActions");
  actions.innerHTML = "";
  if (currentUser.plan === "entreprise") {
    actions.innerHTML = '<p class="muted">Palier Entreprise activé par notre équipe — contacte-nous pour toute question.</p>';
  } else if (currentUser.plan === "essentiel" || currentUser.plan === "pro") {
    const btn = document.createElement("button");
    btn.textContent = "Gérer mon abonnement";
    btn.onclick = openPortal;
    actions.appendChild(btn);
  } else {
    const cycleWrap = document.createElement("div");
    cycleWrap.style.marginBottom = "0.6rem";
    cycleWrap.innerHTML =
      '<label style="margin-right:1rem"><input type="radio" name="billingCycle" value="monthly" checked> Mensuel</label>' +
      '<label><input type="radio" name="billingCycle" value="annual"> Annuel</label>';
    const getCycle = () =>
      (cycleWrap.querySelector('input[name="billingCycle"]:checked') || {}).value || "monthly";
    const essentielBtn = document.createElement("button");
    essentielBtn.textContent = "Passer au palier Essentiel";
    essentielBtn.onclick = () => startCheckout("essentiel", getCycle());
    const proBtn = document.createElement("button");
    proBtn.textContent = "Passer au palier Pro";
    proBtn.className = "secondary";
    proBtn.onclick = () => startCheckout("pro", getCycle());
    actions.appendChild(cycleWrap);
    actions.appendChild(essentielBtn);
    actions.appendChild(proBtn);
  }
}

async function startCheckout(plan, cycle) {
  setMsg("billingMsg", "Redirection vers le paiement...", "");
  try {
    const res = await apiFetch("/billing/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan, cycle }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    window.location.href = body.checkout_url;
  } catch (err) {
    setMsg("billingMsg", err.message, "error");
  }
}

async function openPortal() {
  setMsg("billingMsg", "Redirection vers le portail d'abonnement...", "");
  try {
    const res = await apiFetch("/billing/portal");
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    window.location.href = body.portal_url;
  } catch (err) {
    setMsg("billingMsg", err.message, "error");
  }
}

async function saveWebhookUrl(value) {
  setMsg("webhookMsg", "Enregistrement...", "");
  try {
    const res = await apiFetch("/auth/webhook", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ webhook_url: value || null }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(extractErrorMessage(body));
    currentUser = body;
    setMsg("webhookMsg", value ? "Webhook enregistré." : "Webhook désactivé.", "success");
  } catch (err) {
    setMsg("webhookMsg", err.message, "error");
  }
}

function saveWebhook() {
  saveWebhookUrl(document.getElementById("webhookUrl").value.trim());
}

function clearWebhook() {
  document.getElementById("webhookUrl").value = "";
  saveWebhookUrl("");
}

async function sendSelfPasswordReset() {
  setMsg("passwordMsg", "Envoi en cours...", "");
  try {
    const res = await fetch("/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: currentUser.email }),
    });
    const body = await res.json().catch(() => ({}));
    setMsg("passwordMsg", body.message || "Email envoyé si le compte existe.", "success");
  } catch (err) {
    setMsg("passwordMsg", err.message, "error");
  }
}

async function applyPendingCheckoutMessage() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("checkout")) return;
  const ok = params.get("checkout") === "success";
  showTab("account");
  history.replaceState(null, "", window.location.pathname);
  if (!ok) {
    setMsg("billingMsg", "Paiement annulé.", "error");
    return;
  }
  // Le palier n'est mis à jour qu'à la réception du webhook Stripe (checkout.session.completed),
  // asynchrone par rapport à la redirection du navigateur : on réinterroge /auth/me quelques
  // fois plutôt que d'affirmer à tort que c'est déjà fait.
  setMsg("billingMsg", "Paiement effectué. Mise à jour du palier en cours...", "");
  for (let attempt = 0; attempt < 5; attempt++) {
    await new Promise((r) => setTimeout(r, 1500));
    const res = await apiFetch("/auth/me");
    if (!res.ok) continue;
    const updated = await res.json();
    currentUser = updated;
    renderAccount();
    if (updated.plan !== "none") {
      setMsg("billingMsg", "Paiement effectué, palier mis à jour.", "success");
      return;
    }
  }
  setMsg(
    "billingMsg",
    "Paiement effectué, mais le palier n'est pas encore à jour — réessaie de rafraîchir la page dans quelques instants.",
    "error"
  );
}

// --- Démarrage ---

(function init() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (token) {
    resetTokenValue = token;
    showAuthView();
    showAuthSubview("reset");
    history.replaceState(null, "", window.location.pathname);
    return;
  }
  if (getToken()) {
    afterLogin().catch(() => {
      showAuthView();
      showAuthSubview("login");
    });
  } else {
    showAuthView();
    showAuthSubview("login");
  }
})();
</script>

</body>
</html>
"""
