const state = {
  view: "dashboard",
  companies: [],
  selectedCompanies: new Set(),
  lists: [],
  currentListId: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function fmt(value) {
  if (value === null || value === undefined || value === "") return "-";
  return value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.error || message;
    } catch (err) {
      // keep status text
    }
    throw new Error(message);
  }
  return response.json();
}

function showStatus(message, tone = "info") {
  const status = $("#status");
  status.textContent = message;
  status.className = `status ${tone}`;
  window.clearTimeout(showStatus.timer);
  showStatus.timer = window.setTimeout(() => status.classList.add("hidden"), 4500);
}

function setView(view) {
  state.view = view;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === view));
  $$(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === view));
  const titles = {
    dashboard: "Dashboard",
    companies: "Pesquisa de empresas",
    lists: "Listas",
    import: "Importacao",
    hygiene: "Higiene de emails",
    audit: "Auditoria",
  };
  $("#pageTitle").textContent = titles[view] || "Radar CNPJ";
  if (view === "dashboard") loadDashboard();
  if (view === "companies") {
    loadLists();
    loadCompanies();
  }
  if (view === "lists") loadLists(true);
  if (view === "import") loadOfficialCatalog();
  if (view === "audit") loadAudit();
}

function metric(label, value, tone = "") {
  return `<article class="metric ${tone}"><span>${label}</span><strong>${fmt(value)}</strong></article>`;
}

async function loadDashboard() {
  const data = await api("/api/dashboard");
  const totals = data.totals || {};
  $("#metrics").innerHTML = [
    metric("Empresas", totals.companies || 0),
    metric("Ativas", totals.active || 0),
    metric("Com email", totals.with_email || 0),
    metric("Com telefone", totals.with_phone || 0),
    metric("Score medio", totals.avg_score || 0),
  ].join("");
  renderBars("#topStates", data.top_states || [], "state");
  renderBars("#topCnaes", data.top_cnaes || [], "code", "description");
  renderImports(data.imports || []);
}

function renderBars(selector, items, key, subtitleKey) {
  const max = Math.max(1, ...items.map((item) => item.total || 0));
  if (!items.length) {
    $(selector).innerHTML = `<div class="empty-state">Sem dados ainda. Carregue a amostra ou importe um CSV.</div>`;
    return;
  }
  $(selector).innerHTML = items
    .map((item) => {
      const label = subtitleKey ? `${fmt(item[key])} - ${fmt(item[subtitleKey])}` : fmt(item[key]);
      const width = Math.max(4, Math.round(((item.total || 0) / max) * 100));
      return `<div class="bar-row"><span class="truncate" title="${escapeHtml(label)}">${escapeHtml(label)}</span><div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div><strong>${item.total}</strong></div>`;
    })
    .join("");
}

function renderImports(items) {
  if (!items.length) {
    $("#imports").innerHTML = `<div class="empty-state">Nenhuma importacao registrada.</div>`;
    return;
  }
  $("#imports").innerHTML = table(
    ["Fonte", "Status", "Importadas", "Erros", "Mensagem"],
    items.map((item) => [
      item.source_name,
      badge(item.status, item.status === "completed" ? "green" : item.status === "failed" ? "red" : "amber"),
      item.imported_rows,
      item.error_rows,
      item.message,
    ]),
  );
}

function bytes(value) {
  const number = Number(value || 0);
  if (!number) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = number;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(size >= 10 ? 1 : 2)} ${units[unit]}`;
}

function badge(text, tone = "") {
  return `<span class="badge ${tone}">${escapeHtml(fmt(text))}</span>`;
}

function table(headers, rows) {
  return `<table><thead><tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr></thead><tbody>${rows
    .map((row) => `<tr>${row.map((cell) => `<td>${cell ?? "-"}</td>`).join("")}</tr>`)
    .join("")}</tbody></table>`;
}

function companyFilters() {
  const params = new URLSearchParams();
  const values = {
    query: $("#filterQuery").value,
    state: $("#filterState").value,
    city: $("#filterCity").value,
    cnae: $("#filterCnae").value,
    status: $("#filterStatus").value,
    size: $("#filterSize").value,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  if ($("#filterHasEmail").checked) params.set("has_email", "1");
  params.set("limit", "80");
  return params;
}

async function loadCompanies() {
  const params = companyFilters();
  const data = await api(`/api/companies?${params.toString()}`);
  state.companies = data.items || [];
  state.selectedCompanies.clear();
  $("#resultCount").textContent = `${data.total || 0} empresas encontradas`;
  renderCompanies();
}

function renderCompanies() {
  if (!state.companies.length) {
    $("#companiesTable").innerHTML = `<div class="empty-state">Nenhuma empresa com estes filtros. Tente remover cidade, CNAE ou exigir email.</div>`;
    return;
  }
  const headers = ["", "Empresa", "CNPJ", "UF", "Cidade", "CNAE", "Porte", "Email", "Score"];
  const rows = state.companies.map((company) => [
    `<input type="checkbox" data-select-company="${company.id}" />`,
    `<button class="row-action truncate" title="${escapeHtml(company.legal_name)}" data-company-id="${company.id}">${escapeHtml(company.legal_name)}</button>`,
    escapeHtml(company.cnpj),
    escapeHtml(fmt(company.state)),
    escapeHtml(fmt(company.city)),
    escapeHtml(fmt(company.main_cnae_code)),
    escapeHtml(fmt(company.size)),
    company.email ? badge("email", "green") : badge("sem email", "amber"),
    badge(company.opportunity_score, scoreTone(company.opportunity_score)),
  ]);
  $("#companiesTable").innerHTML = table(headers, rows);
  $$("[data-company-id]").forEach((button) => {
    button.addEventListener("click", () => loadCompanyDetail(button.dataset.companyId));
  });
  $$("[data-select-company]").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const id = Number(checkbox.dataset.selectCompany);
      if (checkbox.checked) state.selectedCompanies.add(id);
      else state.selectedCompanies.delete(id);
    });
  });
}

function scoreTone(score) {
  if (score >= 75) return "green";
  if (score >= 50) return "amber";
  return "red";
}

async function loadCompanyDetail(id) {
  const company = await api(`/api/companies/${id}`);
  const address = [company.street_type, company.street, company.number, company.district, company.city, company.state, company.zip_code]
    .filter(Boolean)
    .join(", ");
  $("#companyDetail").innerHTML = `
    <h2>${escapeHtml(company.legal_name)}</h2>
    <p class="muted">${escapeHtml(fmt(company.trade_name))}</p>
    <div class="stat-line">
      ${badge(company.status, (company.status || "").toLowerCase().includes("ativa") ? "green" : "amber")}
      ${badge(company.sector, "purple")}
      ${badge(`Score ${company.opportunity_score}`, scoreTone(company.opportunity_score))}
    </div>
    <div class="detail-grid">
      ${detailItem("CNPJ", company.cnpj)}
      ${detailItem("CNAE", `${fmt(company.main_cnae_code)} ${fmt(company.main_cnae_description)}`)}
      ${detailItem("Cidade/UF", `${fmt(company.city)} / ${fmt(company.state)}`)}
      ${detailItem("Porte", company.size)}
      ${detailItem("Email", company.email)}
      ${detailItem("Telefone", company.phone)}
      ${detailItem("Capital social", company.capital_social)}
      ${detailItem("Origem", company.source_name)}
    </div>
    <h3>Endereco</h3>
    <p>${escapeHtml(fmt(address))}</p>
    <h3>Socios e administradores</h3>
    ${renderPartners(company.partners || [])}
    <h3>Por que este score</h3>
    <ul>${(company.score_reasons || []).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
    <p class="muted">Base legal: ${escapeHtml(fmt(company.legal_basis))}</p>
  `;
}

function detailItem(label, value) {
  return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(fmt(value))}</strong></div>`;
}

function renderPartners(partners) {
  if (!partners.length) return `<p class="muted">Nenhum socio importado para esta empresa.</p>`;
  return `<ul>${partners
    .map((partner) => `<li><strong>${escapeHtml(partner.name)}</strong> - ${escapeHtml(fmt(partner.qualification))}</li>`)
    .join("")}</ul>`;
}

async function loadLists(renderDetail = false) {
  const data = await api("/api/lists");
  state.lists = data.items || [];
  renderListSelector();
  renderListsIndex();
  if (renderDetail && state.currentListId) {
    loadListDetail(state.currentListId);
  }
}

function renderListSelector() {
  const select = $("#targetList");
  if (!select) return;
  select.innerHTML = state.lists.length
    ? state.lists.map((list) => `<option value="${list.id}">${escapeHtml(list.name)} (${list.company_count || 0})</option>`).join("")
    : `<option value="">Crie uma lista</option>`;
}

function renderListsIndex() {
  const container = $("#listsIndex");
  if (!container) return;
  if (!state.lists.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma lista criada.</div>`;
    return;
  }
  container.innerHTML = state.lists
    .map(
      (list) => `
      <article class="list-card ${String(state.currentListId) === String(list.id) ? "active" : ""}" data-list-card="${list.id}">
        <strong>${escapeHtml(list.name)}</strong>
        <span class="muted">${list.company_count || 0} empresas / ${list.email_count || 0} emails / score ${fmt(list.avg_score)}</span>
      </article>`,
    )
    .join("");
  $$("[data-list-card]").forEach((card) => {
    card.addEventListener("click", () => {
      state.currentListId = Number(card.dataset.listCard);
      renderListsIndex();
      loadListDetail(state.currentListId);
    });
  });
}

async function loadListDetail(id) {
  const list = await api(`/api/lists/${id}`);
  const stats = list.stats || {};
  $("#listDetail").innerHTML = `
    <div class="panel-head">
      <h2>${escapeHtml(list.name)}</h2>
      <div class="toolbar-actions">
        <input id="exportPurpose" class="input compact" placeholder="Finalidade da exportacao" />
        <button class="button" data-export="csv">CSV</button>
        <button class="button" data-export="xlsx">XLSX</button>
        <button class="button primary" id="validateListBtn">Validar emails</button>
      </div>
    </div>
    <div class="stat-line">
      ${badge(`${stats.total || 0} empresas`)}
      ${badge(`${stats.with_email || 0} com email`, "green")}
      ${badge(`${stats.with_phone || 0} com telefone`, "amber")}
      ${badge(`score ${fmt(stats.avg_score)}`, "purple")}
    </div>
    <div class="table-wrap">${renderListCompanies(list.companies || [])}</div>
  `;
  $$("[data-export]").forEach((button) => {
    button.addEventListener("click", () => exportCurrentList(button.dataset.export));
  });
  $("#validateListBtn").addEventListener("click", validateCurrentList);
}

function renderListCompanies(companies) {
  if (!companies.length) return `<div class="empty-state">Lista vazia. Adicione empresas pela tela de pesquisa.</div>`;
  return table(
    ["Empresa", "CNPJ", "Cidade", "UF", "Email", "Score", ""],
    companies.map((company) => [
      `<span class="truncate" title="${escapeHtml(company.legal_name)}">${escapeHtml(company.legal_name)}</span>`,
      escapeHtml(company.cnpj),
      escapeHtml(fmt(company.city)),
      escapeHtml(fmt(company.state)),
      escapeHtml(fmt(company.email)),
      badge(company.opportunity_score, scoreTone(company.opportunity_score)),
      `<button class="row-action" data-remove-company="${company.id}">Remover</button>`,
    ]),
  );
}

async function createListFromForm() {
  const name = $("#listName").value.trim();
  if (!name) return showStatus("Informe o nome da lista.", "warn");
  const list = await api("/api/lists", {
    method: "POST",
    body: JSON.stringify({ name, description: $("#listDescription").value }),
  });
  state.currentListId = list.id;
  $("#listName").value = "";
  $("#listDescription").value = "";
  showStatus("Lista criada.");
  await loadLists(true);
  await loadListDetail(list.id);
}

async function addSelectedToList() {
  const listId = $("#targetList").value;
  if (!listId) return showStatus("Crie ou selecione uma lista.", "warn");
  const companyIds = Array.from(state.selectedCompanies);
  if (!companyIds.length) return showStatus("Selecione empresas na tabela.", "warn");
  const result = await api(`/api/lists/${listId}/companies`, {
    method: "POST",
    body: JSON.stringify({ company_ids: companyIds }),
  });
  showStatus(`${result.added} empresas adicionadas a lista.`);
  await loadLists();
}

async function exportCurrentList(format) {
  const purpose = $("#exportPurpose").value.trim();
  if (!purpose || purpose.length < 8) return showStatus("Informe uma finalidade clara para exportar.", "warn");
  const url = `/api/lists/${state.currentListId}/export?format=${encodeURIComponent(format)}&purpose=${encodeURIComponent(purpose)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json();
    return showStatus(body.error || "Erro ao exportar.", "warn");
  }
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `radar-cnpj-lista.${format}`;
  link.click();
  URL.revokeObjectURL(link.href);
  showStatus("Exportacao gerada e auditada.");
}

async function validateCurrentList() {
  if (!state.currentListId) return;
  const data = await api("/api/emails/validate", {
    method: "POST",
    body: JSON.stringify({ list_id: state.currentListId }),
  });
  showStatus(`${data.items.length} emails validados.`);
  renderEmailResults(data.items);
  setView("hygiene");
}

async function importFromForm() {
  const payload = {
    path: $("#importPath").value.trim(),
    source_name: $("#importSource").value.trim(),
    source_url: $("#importUrl").value.trim(),
    legal_basis: $("#importBasis").value.trim(),
    limit: Number($("#importLimit").value || 1000),
  };
  if (!payload.path) return showStatus("Informe o caminho local do arquivo ou diretorio.", "warn");
  const result = await api("/api/import", { method: "POST", body: JSON.stringify(payload) });
  showStatus(result.message || "Importacao concluida.");
  await loadDashboard();
}

async function loadOfficialCatalog() {
  const summary = $("#officialSummary");
  if (!summary) return;
  summary.textContent = "Buscando fonte oficial...";
  try {
    const data = await api("/api/sources/official");
    const latest = data.latest || {};
    if (latest.name) $("#officialSnapshot").value = latest.name;
    summary.innerHTML = latest.name
      ? `Ultima base: <strong>${escapeHtml(latest.name)}</strong> / ${bytes(latest.size_bytes)}`
      : "Nenhuma base oficial encontrada.";
    renderOfficialFiles(data.latest_files || []);
  } catch (err) {
    summary.textContent = err.message;
  }
}

function renderOfficialFiles(files) {
  const container = $("#officialFiles");
  if (!container) return;
  if (!files.length) {
    container.innerHTML = `<div class="empty-state">Nenhum arquivo oficial listado.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Arquivo", "Tamanho", "Atualizado"],
    files.map((file) => [escapeHtml(file.name), bytes(file.size_bytes), escapeHtml(fmt(file.last_modified))]),
  );
}

async function syncOfficial(modeOverride) {
  const mode = modeOverride || $("#officialMode").value;
  const snapshot = $("#officialSnapshot").value.trim();
  const chunk = Number($("#officialChunk").value || 1);
  const limit = Number($("#officialLimit").value || 1000);
  if (!snapshot) return showStatus("Descubra ou informe o snapshot oficial.", "warn");
  if (mode === "full" && !window.confirm("A base completa pode baixar varios GB. Continuar?")) return;
  showStatus("Sincronizacao oficial iniciada. Isso pode demorar conforme o tamanho dos arquivos.");
  const result = await api("/api/sources/official/sync", {
    method: "POST",
    body: JSON.stringify({ snapshot, chunk, limit, mode }),
  });
  const imported = result.imported ? ` / ${result.imported.imported_rows} empresas importadas` : "";
  showStatus(`${result.downloaded.length} arquivos oficiais processados${imported}.`);
  await loadDashboard();
  await loadCompanies();
}

async function lookupBrasilApi() {
  const cnpj = $("#brasilApiCnpj").value.trim();
  if (!cnpj) return showStatus("Informe o CNPJ.", "warn");
  showStatus("Consultando BrasilAPI...");
  const result = await api("/api/sources/brasilapi/cnpj", {
    method: "POST",
    body: JSON.stringify({ cnpj }),
  });
  const company = result.company || {};
  $("#brasilApiResult").innerHTML = table(
    ["Campo", "Valor"],
    [
      ["Empresa", escapeHtml(company.legal_name)],
      ["CNPJ", escapeHtml(company.cnpj)],
      ["Cidade/UF", escapeHtml(`${fmt(company.city)} / ${fmt(company.state)}`)],
      ["CNAE", escapeHtml(`${fmt(company.main_cnae_code)} ${fmt(company.main_cnae_description)}`)],
      ["Email", escapeHtml(fmt(company.email))],
      ["Socios", escapeHtml((company.partners || []).map((p) => p.name).join("; "))],
    ],
  );
  showStatus("CNPJ consultado e salvo na base local.");
  await loadDashboard();
  await loadCompanies();
}

async function seed() {
  const result = await api("/api/seed", { method: "POST", body: "{}" });
  showStatus(result.message || "Amostra carregada.");
  await loadDashboard();
  await loadCompanies();
}

async function validateFreeEmails() {
  const emails = $("#emailInput").value.split(/\s|,|;/).filter(Boolean);
  const data = await api("/api/emails/validate", {
    method: "POST",
    body: JSON.stringify({ emails }),
  });
  renderEmailResults(data.items);
}

async function scoreFreeEmails() {
  const emails = $("#emailInput").value.split(/\s|,|;/).filter(Boolean);
  const data = await api("/api/emails/score", {
    method: "POST",
    body: JSON.stringify({ emails }),
  });
  renderEmailResults(data.items.map((item) => ({ email: item.email, advanced: item })));
}

function renderEmailResults(items) {
  if (!items.length) {
    $("#emailResults").innerHTML = `<div class="empty-state">Nenhum email para validar.</div>`;
    return;
  }
  $("#emailResults").innerHTML = table(
    ["Email", "Higiene", "Area", "Score", "Motivos"],
    items.map((item) => [
      escapeHtml(item.email),
      badge(item.classification || item.advanced?.classification, emailTone(item.classification || item.advanced?.classification)),
      escapeHtml(fmt(item.advanced?.area)),
      badge(item.advanced?.score ?? item.score, scoreTone(item.advanced?.score ?? item.score)),
      escapeHtml(((item.advanced?.reasons || item.reasons || [])).join("; ")),
    ]),
  );
}

function emailTone(classification) {
  if (classification === "Valido") return "green";
  if (classification === "Generico" || classification === "Pessoal") return "amber";
  return "red";
}

async function addSuppression() {
  const email = $("#suppressionEmail").value.trim();
  const reason = $("#suppressionReason").value.trim() || "Solicitacao manual";
  if (!email) return showStatus("Informe o email para supressao.", "warn");
  await api("/api/suppression", { method: "POST", body: JSON.stringify({ email, reason }) });
  showStatus("Email adicionado a lista de supressao.");
  $("#suppressionEmail").value = "";
  $("#suppressionReason").value = "";
}

async function loadAudit() {
  const data = await api("/api/audit");
  const items = data.items || [];
  if (!items.length) {
    $("#auditTable").innerHTML = `<div class="empty-state">Nenhum evento auditado ainda.</div>`;
    return;
  }
  $("#auditTable").innerHTML = table(
    ["Data", "Acao", "Entidade", "ID", "Metadados"],
    items.map((item) => [
      escapeHtml(item.created_at),
      escapeHtml(item.action),
      escapeHtml(item.entity_type),
      escapeHtml(fmt(item.entity_id)),
      `<span class="truncate" title="${escapeHtml(item.metadata)}">${escapeHtml(item.metadata)}</span>`,
    ]),
  );
}

function wireEvents() {
  $$(".nav-item").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $("#searchBtn").addEventListener("click", loadCompanies);
  $("#quickSearchBtn").addEventListener("click", () => {
    $("#filterQuery").value = $("#quickSearch").value;
    setView("companies");
  });
  $("#quickSearch").addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#quickSearchBtn").click();
  });
  $("#addToListBtn").addEventListener("click", addSelectedToList);
  $("#createListBtn").addEventListener("click", createListFromForm);
  $("#importBtn").addEventListener("click", importFromForm);
  $("#discoverOfficialBtn").addEventListener("click", loadOfficialCatalog);
  $("#syncOfficialBtn").addEventListener("click", () => syncOfficial());
  $("#downloadDomainsBtn").addEventListener("click", () => syncOfficial("domains"));
  $("#brasilApiBtn").addEventListener("click", lookupBrasilApi);
  $("#seedBtn").addEventListener("click", seed);
  $("#seedBtnImport").addEventListener("click", seed);
  $("#validateEmailsBtn").addEventListener("click", validateFreeEmails);
  $("#scoreEmailsBtn").addEventListener("click", scoreFreeEmails);
  $("#suppressionBtn").addEventListener("click", addSuppression);
  $("#refreshAuditBtn").addEventListener("click", loadAudit);
  $("#listDetail").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-remove-company]");
    if (!button || !state.currentListId) return;
    await api(`/api/lists/${state.currentListId}/companies/${button.dataset.removeCompany}`, { method: "DELETE" });
    showStatus("Empresa removida da lista.");
    await loadListDetail(state.currentListId);
    await loadLists();
  });
}

async function start() {
  wireEvents();
  await loadDashboard();
  await loadLists();
  await loadCompanies();
}

start().catch((err) => showStatus(err.message, "warn"));
