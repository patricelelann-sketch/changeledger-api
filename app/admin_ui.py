"""Page HTML minimale d'administration (liste des comptes + changement de palier).

Autonome (pas de dépendance externe, pas de framework JS) : un simple formulaire pour
saisir le secret admin (X-Admin-Secret), stocké uniquement en mémoire de l'onglet
(sessionStorage), et deux appels à l'API déjà existante (/admin/users, /admin/users/plan).
Pas de protection supplémentaire sur la page elle-même : comme pour les commandes curl
équivalentes, c'est le secret qui protège les données, pas l'accès à la page.
"""

ADMIN_UI_HTML = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChangeLedger — Administration</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5;
  }
  h1 { font-size: 1.4rem; }
  .muted { color: #6b7280; font-size: 0.9rem; }
  .row { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; margin: 1rem 0; }
  input, select, button {
    font-size: 0.95rem; padding: 0.4rem 0.6rem; border-radius: 6px;
    border: 1px solid #d1d5db;
  }
  button {
    background: #111827; color: white; border: none; cursor: pointer;
  }
  button:hover { background: #374151; }
  button.secondary { background: white; color: #111827; border: 1px solid #d1d5db; }
  button.secondary:hover { background: #f3f4f6; }
  button.danger { background: white; color: #b91c1c; border: 1px solid #fca5a5; }
  button.danger:hover { background: #fef2f2; }
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  th, td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }
  th { color: #6b7280; font-weight: 600; }
  #message { margin: 0.8rem 0; font-size: 0.9rem; min-height: 1.2em; }
  #message.error { color: #b91c1c; }
  #message.success { color: #15803d; }
  .plan-form { display: flex; gap: 0.4rem; align-items: center; }
  #gate { max-width: 420px; margin-top: 3rem; }
  #app { display: none; }
</style>
</head>
<body>

<div id="gate">
  <h1>ChangeLedger — Administration</h1>
  <p class="muted">Saisis le secret admin (X-Admin-Secret) pour accéder aux comptes.</p>
  <div class="row">
    <input type="password" id="secretInput" placeholder="Secret admin" style="flex:1">
    <button onclick="saveSecret()">Entrer</button>
  </div>
  <div id="gateMessage" class="error"></div>
</div>

<div id="app">
  <h1>ChangeLedger — Administration</h1>
  <div class="row">
    <button class="secondary" onclick="loadUsers()">Rafraîchir</button>
    <button class="secondary" onclick="resetSecret()">Changer de secret</button>
  </div>
  <div id="message"></div>
  <table>
    <thead>
      <tr><th>Email</th><th>Palier</th><th>Abonnement</th><th>Créé le</th><th>Changer le palier</th></tr>
    </thead>
    <tbody id="usersBody"></tbody>
  </table>
</div>

<script>
const PLANS = ["none", "essentiel", "pro", "entreprise"];

function getSecret() {
  return sessionStorage.getItem("changeledger_admin_secret") || "";
}

function saveSecret() {
  const value = document.getElementById("secretInput").value.trim();
  if (!value) return;
  sessionStorage.setItem("changeledger_admin_secret", value);
  document.getElementById("gateMessage").textContent = "";
  showApp();
  loadUsers();
}

function resetSecret() {
  sessionStorage.removeItem("changeledger_admin_secret");
  document.getElementById("app").style.display = "none";
  document.getElementById("gate").style.display = "block";
  document.getElementById("secretInput").value = "";
}

function showApp() {
  document.getElementById("gate").style.display = "none";
  document.getElementById("app").style.display = "block";
}

function setMessage(text, kind) {
  const el = document.getElementById("message");
  el.textContent = text || "";
  el.className = kind || "";
}

async function loadUsers() {
  setMessage("Chargement...", "");
  try {
    const res = await fetch("/admin/users", {
      headers: { "X-Admin-Secret": getSecret() },
    });
    if (res.status === 401 || res.status === 403) {
      setMessage("Secret invalide ou administration désactivée.", "error");
      document.getElementById("app").style.display = "none";
      document.getElementById("gate").style.display = "block";
      document.getElementById("gateMessage").textContent = "Secret refusé, réessaie.";
      return;
    }
    if (!res.ok) {
      setMessage("Erreur inattendue (" + res.status + ").", "error");
      return;
    }
    const users = await res.json();
    renderUsers(users);
    setMessage("");
  } catch (err) {
    setMessage("Impossible de contacter l'API : " + err, "error");
  }
}

function renderUsers(users) {
  const body = document.getElementById("usersBody");
  body.innerHTML = "";
  for (const user of users) {
    const tr = document.createElement("tr");

    const planOptions = PLANS.map(
      (p) => `<option value="${p}" ${p === user.plan ? "selected" : ""}>${p}</option>`
    ).join("");

    tr.innerHTML = `
      <td>${escapeHtml(user.email)}</td>
      <td>${escapeHtml(user.plan)}</td>
      <td>${escapeHtml(user.subscription_status || "—")}</td>
      <td>${escapeHtml((user.created_at || "").slice(0, 10))}</td>
      <td>
        <span class="plan-form">
          <select data-email="${escapeHtml(user.email)}">${planOptions}</select>
          <button class="secondary" data-email="${escapeHtml(user.email)}">Enregistrer</button>
          <button class="danger" data-delete-email="${escapeHtml(user.email)}">Supprimer</button>
        </span>
      </td>
    `;
    body.appendChild(tr);
  }
  body.querySelectorAll("button[data-email]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const email = btn.getAttribute("data-email");
      const select = body.querySelector(`select[data-email="${CSS.escape(email)}"]`);
      setPlan(email, select.value);
    });
  });
  body.querySelectorAll("button[data-delete-email]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const email = btn.getAttribute("data-delete-email");
      if (confirm(`Supprimer définitivement le compte ${email} et toutes ses données (sources, changements) ? Cette action est irréversible.`)) {
        deleteUser(email);
      }
    });
  });
}

async function deleteUser(email) {
  setMessage("Suppression de " + email + "...", "");
  try {
    const res = await fetch("/admin/users", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Secret": getSecret(),
      },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setMessage("Échec : " + (body.detail || res.status), "error");
      return;
    }
    setMessage(email + " a été supprimé.", "success");
    loadUsers();
  } catch (err) {
    setMessage("Impossible de contacter l'API : " + err, "error");
  }
}

async function setPlan(email, plan) {
  setMessage("Mise à jour de " + email + "...", "");
  try {
    const res = await fetch("/admin/users/plan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Secret": getSecret(),
      },
      body: JSON.stringify({ email, plan }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setMessage("Échec : " + (body.detail || res.status), "error");
      return;
    }
    setMessage(email + " est maintenant sur le palier " + plan + ".", "success");
    loadUsers();
  } catch (err) {
    setMessage("Impossible de contacter l'API : " + err, "error");
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

if (getSecret()) {
  showApp();
  loadUsers();
}
</script>

</body>
</html>
"""
