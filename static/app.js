const state = {
  view: "dashboard",
  companies: [],
  selectedCompanies: new Set(),
  lists: [],
  currentListId: null,
  templates: [],
  selectedTemplateId: null,
  lastRenderedTemplate: null,
  sequences: [],
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
    enrichment: "Enriquecimento",
    experiments: "Experimentos",
    templates: "Templates",
    sequences: "Sequencias",
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
  if (view === "experiments") loadExperiments();
  if (view === "templates") loadTemplates();
  if (view === "sequences") loadSequenceWorkspace();
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
    <div class="toolbar-actions detail-actions">
      <button class="button primary" data-enrich-company="${company.id}">Enriquecer</button>
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
  const enrichButton = $("#companyDetail [data-enrich-company]");
  if (enrichButton) {
    enrichButton.addEventListener("click", () => prefillEnrichment(company));
  }
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
  const markup = state.lists.length
    ? state.lists.map((list) => `<option value="${list.id}">${escapeHtml(list.name)} (${list.company_count || 0})</option>`).join("")
    : `<option value="">Crie uma lista</option>`;
  if (select) select.innerHTML = markup;
  const experimentSelect = $("#experimentList");
  if (experimentSelect) experimentSelect.innerHTML = markup;
  const sequenceSelect = $("#sequenceList");
  if (sequenceSelect) sequenceSelect.innerHTML = markup;
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

function prefillEnrichment(company) {
  const suggestedUrl = (company.source_url || "").startsWith("http") ? company.source_url : "";
  $("#enrichCompanyId").value = company.id;
  $("#enrichUrl").value = suggestedUrl;
  $("#enrichSourceUrl").value = suggestedUrl;
  $("#enrichHtml").value = "";
  setView("enrichment");
}

function inlineBadges(values, tone = "") {
  const items = values || [];
  if (!items.length) return "-";
  return items.map((item) => badge(item, tone)).join(" ");
}

function renderEnrichmentResult(item) {
  if (!item) {
    $("#enrichmentResult").innerHTML = `<div class="empty-state">Nenhum enriquecimento salvo para esta empresa.</div>`;
    return;
  }
  $("#enrichmentResult").innerHTML = table(
    ["Campo", "Valor"],
    [
      ["Empresa", escapeHtml(item.trade_name || item.legal_name || item.company_name || item.company_id)],
      ["CNPJ", escapeHtml(fmt(item.cnpj))],
      ["Origem", escapeHtml(fmt(item.source_url))],
      ["Tipo", badge(item.source_type || "manual")],
      ["Dominio", escapeHtml(fmt(item.detected_domain))],
      ["Score digital", badge(item.digital_maturity_score, scoreTone(item.digital_maturity_score || 0))],
      ["Confianca", badge(item.confidence, item.confidence === "high" ? "green" : item.confidence === "medium" ? "amber" : "red")],
      ["Emails", inlineBadges(item.emails, "green")],
      ["Telefones", escapeHtml((item.phones || []).join("; ") || "-")],
      ["Redes sociais", escapeHtml((item.social_links || []).join("; ") || "-")],
      ["Tecnologias", inlineBadges(item.technologies, "purple")],
      ["Motivos", escapeHtml((item.reasons || []).join("; ") || "-")],
      ["Job", escapeHtml(item.job ? `${item.job.status}: ${item.job.message}` : "-")],
    ],
  );
}

async function enrichCompanyFromForm() {
  const companyId = Number($("#enrichCompanyId").value || 0);
  const url = $("#enrichUrl").value.trim();
  const sourceUrl = $("#enrichSourceUrl").value.trim() || url;
  const html = $("#enrichHtml").value.trim();
  const ttlDays = Number($("#enrichTtl").value || 30);
  if (!companyId) return showStatus("Informe o ID da empresa.", "warn");
  if (!url && !html) return showStatus("Informe uma URL ou cole um HTML de teste.", "warn");
  showStatus(html ? "Processando HTML informado..." : "Coletando URL com robots.txt e cache...");
  const result = await api("/api/enrichment/company", {
    method: "POST",
    body: JSON.stringify({ company_id: companyId, url, source_url: sourceUrl, html, ttl_days: ttlDays }),
  });
  renderEnrichmentResult(result);
  showStatus("Enriquecimento salvo com auditoria.");
}

async function loadEnrichmentFromForm() {
  const companyId = Number($("#enrichCompanyId").value || 0);
  if (!companyId) return showStatus("Informe o ID da empresa.", "warn");
  const result = await api(`/api/enrichment/company/${companyId}`);
  renderEnrichmentResult(result);
}

async function loadExperiments() {
  await loadLists();
  await Promise.all([loadExperimentLeads(), loadCampaigns()]);
}

function experimentStatusTone(status) {
  if (["eligible", "in_campaign", "converted", "simulated_sent", "delivered", "clicked"].includes(status)) return "green";
  if (["new", "draft", "running", "replied", "responded"].includes(status)) return "amber";
  return "red";
}

async function createLeadsFromExperimentList() {
  const listId = $("#experimentList").value;
  if (!listId) return showStatus("Selecione uma lista.", "warn");
  const result = await api("/api/experiments/leads/from-list", {
    method: "POST",
    body: JSON.stringify({ list_id: Number(listId), source: "lista qualificada" }),
  });
  $("#experimentLeadSummary").textContent = `${result.total} processados / ${result.eligible} elegiveis / ${result.blocked} bloqueados`;
  showStatus("Leads criados com guardrails de higiene e supressao.");
  await loadExperimentLeads();
}

async function loadExperimentLeads() {
  const data = await api("/api/experiments/leads?limit=200");
  renderExperimentLeads(data.items || []);
}

function renderExperimentLeads(items) {
  const container = $("#experimentLeadsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhum lead criado ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Empresa", "Lista", "Email", "Status", "Score", "Bloqueio"],
    items.map((lead) => [
      lead.id,
      escapeHtml(lead.trade_name || lead.legal_name || lead.cnpj || "-"),
      escapeHtml(fmt(lead.list_name)),
      escapeHtml(fmt(lead.email)),
      badge(lead.status, experimentStatusTone(lead.status)),
      badge(lead.score, scoreTone(lead.score || 0)),
      escapeHtml(fmt(lead.block_reason)),
    ]),
  );
}

async function createCampaignFromForm() {
  const payload = {
    name: $("#campaignName").value.trim(),
    niche: $("#campaignNiche").value.trim(),
    subject: $("#campaignSubject").value.trim(),
    body: $("#campaignBody").value.trim(),
    cta_url: $("#campaignCta").value.trim(),
    daily_limit: Number($("#campaignDailyLimit").value || 50),
    interval_seconds: Number($("#campaignInterval").value || 300),
  };
  if (!payload.name || !payload.subject || !payload.body) {
    return showStatus("Informe nome, assunto e corpo da campanha.", "warn");
  }
  await api("/api/experiments/campaigns", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("#campaignName").value = "";
  $("#campaignSubject").value = "";
  $("#campaignBody").value = "";
  showStatus("Campanha simulada criada.");
  await loadCampaigns();
}

async function loadCampaigns() {
  const data = await api("/api/experiments/campaigns");
  renderCampaigns(data.items || []);
}

function renderCampaigns(items) {
  const container = $("#campaignsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma campanha criada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Campanha", "Status", "Modo", "Envios", "Cliques", "Respostas", "Conversoes", "Bloqueios", ""],
    items.map((campaign) => {
      const funnel = campaign.funnel || {};
      return [
        campaign.id,
        `<span class="truncate" title="${escapeHtml(campaign.name)}">${escapeHtml(campaign.name)}</span>`,
        badge(campaign.status, experimentStatusTone(campaign.status)),
        badge(campaign.mode, campaign.mode === "simulated" ? "purple" : "red"),
        badge(funnel.sent || 0, "green"),
        badge(funnel.clicked || 0, "amber"),
        badge(funnel.replied || 0, "amber"),
        badge(funnel.converted || 0, "green"),
        badge(funnel.blocked || 0, funnel.blocked ? "red" : ""),
        `<button class="row-action" data-simulate-campaign="${campaign.id}">Simular</button>`,
      ];
    }),
  );
  $$("[data-simulate-campaign]").forEach((button) => {
    button.addEventListener("click", () => simulateCampaign(button.dataset.simulateCampaign));
  });
}

async function simulateCampaign(campaignId) {
  const listId = $("#experimentList").value;
  if (!listId) return showStatus("Selecione uma lista para simular.", "warn");
  const result = await api(`/api/experiments/campaigns/${campaignId}/simulate`, {
    method: "POST",
    body: JSON.stringify({ list_id: Number(listId), limit: 50 }),
  });
  const simulation = result.simulation || {};
  showStatus(`${simulation.sent || 0} envios simulados / ${simulation.blocked || 0} bloqueados.`);
  await Promise.all([loadCampaigns(), loadExperimentLeads()]);
}

async function recordExperimentEvent() {
  const sendId = Number($("#experimentSendId").value || 0);
  const eventType = $("#experimentEventType").value;
  if (!sendId) return showStatus("Informe o ID do envio.", "warn");
  await api("/api/experiments/events", {
    method: "POST",
    body: JSON.stringify({ send_id: sendId, event_type: eventType }),
  });
  showStatus("Evento registrado no funil.");
  await Promise.all([loadCampaigns(), loadExperimentLeads()]);
}

function clearTemplateForm() {
  state.selectedTemplateId = null;
  state.lastRenderedTemplate = null;
  $("#templateSelectedId").value = "";
  $("#templateName").value = "";
  $("#templatePurpose").value = "first_contact";
  $("#templateSubject").value = "";
  $("#templateBody").value = "";
  $("#templatePreviewResult").innerHTML = `<div class="empty-state">Selecione um template e renderize com uma empresa.</div>`;
}

async function loadTemplates() {
  const data = await api("/api/templates");
  state.templates = data.items || [];
  renderTemplatesTable(state.templates);
  renderTemplateSelects();
}

function renderTemplateSelects() {
  const markup = state.templates.length
    ? `<option value="">Selecione</option>${state.templates
        .map((template) => {
          const version = template.active_version || {};
          return `<option value="${template.id}">${escapeHtml(template.name)} v${version.version_number || "-"}</option>`;
        })
        .join("")}`
    : `<option value="">Crie um template</option>`;
  $$("[data-template-select]").forEach((select) => {
    const current = select.value;
    select.innerHTML = markup;
    if (current) select.value = current;
  });
}

function renderTemplatesTable(items) {
  const container = $("#templatesTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhum template criado ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Nome", "Finalidade", "Status", "Versao", "Variaveis", ""],
    items.map((item) => {
      const version = item.active_version || {};
      return [
        item.id,
        `<span class="truncate" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</span>`,
        badge(item.purpose),
        badge(item.status, item.status === "active" ? "green" : "amber"),
        badge(version.version_number || "-"),
        escapeHtml((version.variables || []).join(", ") || "-"),
        `<button class="row-action" data-select-template="${item.id}">Selecionar</button>`,
      ];
    }),
  );
  $$("[data-select-template]").forEach((button) => {
    button.addEventListener("click", () => selectTemplate(button.dataset.selectTemplate));
  });
}

async function selectTemplate(templateId) {
  const template = await api(`/api/templates/${templateId}`);
  const version = template.active_version || {};
  state.selectedTemplateId = template.id;
  $("#templateSelectedId").value = template.id;
  $("#templateName").value = template.name;
  $("#templatePurpose").value = template.purpose || "other";
  $("#templateSubject").value = version.subject || "";
  $("#templateBody").value = version.body || "";
  showStatus(`Template ${template.id} selecionado.`);
}

function templatePayloadFromForm() {
  return {
    name: $("#templateName").value.trim(),
    purpose: $("#templatePurpose").value,
    subject: $("#templateSubject").value.trim(),
    body: $("#templateBody").value.trim(),
  };
}

async function createTemplateFromForm() {
  const payload = templatePayloadFromForm();
  if (!payload.name || !payload.subject || !payload.body) {
    return showStatus("Informe nome, assunto e corpo do template.", "warn");
  }
  const template = await api("/api/templates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.selectedTemplateId = template.id;
  $("#templateSelectedId").value = template.id;
  showStatus("Template criado com versao 1 ativa.");
  await loadTemplates();
}

async function createTemplateVersionFromForm() {
  const templateId = Number($("#templateSelectedId").value || state.selectedTemplateId || 0);
  if (!templateId) return showStatus("Selecione um template para criar nova versao.", "warn");
  const payload = templatePayloadFromForm();
  const template = await api(`/api/templates/${templateId}/versions`, {
    method: "POST",
    body: JSON.stringify({ subject: payload.subject, body: payload.body }),
  });
  const version = template.active_version || {};
  showStatus(`Nova versao ativa: ${version.version_number}.`);
  await loadTemplates();
}

function previewHtml(value) {
  return `<pre class="preview-text">${escapeHtml(value || "-")}</pre>`;
}

async function renderTemplateFromForm() {
  const templateId = Number($("#templateSelectedId").value || state.selectedTemplateId || 0);
  if (!templateId) return showStatus("Selecione um template.", "warn");
  const payload = {
    template_id: templateId,
    company_id: Number($("#templatePreviewCompanyId").value || 0) || undefined,
    cta_url: $("#templatePreviewCta").value.trim(),
    unsubscribe_url: $("#templatePreviewUnsubscribe").value.trim(),
    privacy_url: $("#templatePreviewPrivacy").value.trim(),
  };
  const rendered = await api("/api/templates/render", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.lastRenderedTemplate = rendered;
  $("#templatePreviewResult").innerHTML = table(
    ["Campo", "Valor"],
    [
      ["Template", escapeHtml(`${rendered.name} v${rendered.version_number}`)],
      ["Assunto", escapeHtml(rendered.subject)],
      ["Corpo", previewHtml(rendered.body)],
      ["Variaveis ausentes", escapeHtml((rendered.missing_variables || []).join(", ") || "-")],
      ["Variaveis nao suportadas", escapeHtml((rendered.unsupported_variables || []).join(", ") || "-")],
    ],
  );
  showStatus("Preview renderizado com rodape de compliance.");
}

function useTemplateInCampaign() {
  const rendered = state.lastRenderedTemplate;
  if (!rendered) return showStatus("Renderize um template antes de usar na campanha.", "warn");
  $("#campaignSubject").value = rendered.subject || "";
  $("#campaignBody").value = rendered.body || "";
  $("#campaignCta").value = $("#templatePreviewCta").value.trim() || $("#campaignCta").value;
  setView("experiments");
  showStatus("Template renderizado aplicado ao formulario de campanha simulada.");
}

async function loadSequenceWorkspace() {
  await loadLists();
  await loadTemplates();
  await Promise.all([loadSequences(), loadApprovals(), loadJourneys(), loadAgentActions()]);
}

async function createSequenceFromForm() {
  const firstTemplate = Number($("#sequenceStepTemplate1").value || 0);
  if (!firstTemplate) return showStatus("Selecione o template do passo 1.", "warn");
  const steps = [{ name: "Primeiro contato", template_id: firstTemplate, wait_days: 0 }];
  const secondTemplate = Number($("#sequenceStepTemplate2").value || 0);
  if (secondTemplate) {
    steps.push({
      name: "Follow-up",
      template_id: secondTemplate,
      wait_days: Number($("#sequenceStep2Wait").value || 0),
    });
  }
  const payload = {
    name: $("#sequenceName").value.trim(),
    description: $("#sequenceDescription").value.trim(),
    steps,
  };
  if (!payload.name) return showStatus("Informe o nome da sequencia.", "warn");
  await api("/api/sequences", { method: "POST", body: JSON.stringify(payload) });
  $("#sequenceName").value = "";
  $("#sequenceDescription").value = "";
  showStatus("Sequencia criada com passos supervisionados.");
  await loadSequences();
}

async function loadSequences() {
  const data = await api("/api/sequences");
  state.sequences = data.items || [];
  renderSequences(state.sequences);
}

function renderSequences(items) {
  const container = $("#sequencesTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma sequencia criada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Sequencia", "Status", "Passos", "Jornadas", ""],
    items.map((sequence) => {
      const counts = sequence.journey_counts || {};
      const summary = Object.entries(counts).map(([key, value]) => `${key}:${value}`).join(" / ") || "-";
      return [
        sequence.id,
        `<span class="truncate" title="${escapeHtml(sequence.name)}">${escapeHtml(sequence.name)}</span>`,
        badge(sequence.status, sequence.status === "active" ? "green" : "amber"),
        escapeHtml((sequence.steps || []).map((step) => `${step.step_number}. ${step.name}`).join("; ")),
        escapeHtml(summary),
        `<button class="row-action" data-enroll-sequence="${sequence.id}">Inscrever lista</button>`,
      ];
    }),
  );
  $$("[data-enroll-sequence]").forEach((button) => {
    button.addEventListener("click", () => enrollSequence(button.dataset.enrollSequence));
  });
}

async function enrollSequence(sequenceId) {
  const listId = Number($("#sequenceList").value || 0);
  if (!listId) return showStatus("Selecione uma lista para inscrever.", "warn");
  const result = await api(`/api/sequences/${sequenceId}/enroll`, {
    method: "POST",
    body: JSON.stringify({ list_id: listId }),
  });
  showStatus(`${result.enrolled} jornadas criadas / ${result.approvals} aprovacoes pendentes.`);
  await Promise.all([loadSequences(), loadApprovals(), loadJourneys(), loadAgentActions()]);
}

async function loadApprovals() {
  const data = await api("/api/approvals");
  renderApprovals(data.items || []);
}

function renderApprovals(items) {
  const container = $("#approvalsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma aprovacao pendente.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Titulo", "Email", "Assunto", "Corpo", ""],
    items.map((approval) => {
      const context = approval.context || {};
      return [
        approval.id,
        `<span class="truncate" title="${escapeHtml(approval.title)}">${escapeHtml(approval.title)}</span>`,
        escapeHtml(fmt(context.email)),
        escapeHtml(fmt(context.subject)),
        previewHtml(context.body || "-"),
        `<button class="row-action" data-approve="${approval.id}">Aprovar</button> <button class="row-action" data-reject="${approval.id}">Rejeitar</button>`,
      ];
    }),
  );
  $$("[data-approve]").forEach((button) => {
    button.addEventListener("click", () => decideApproval(button.dataset.approve, "approve"));
  });
  $$("[data-reject]").forEach((button) => {
    button.addEventListener("click", () => decideApproval(button.dataset.reject, "reject"));
  });
}

async function decideApproval(approvalId, decision) {
  const note = $("#approvalDecisionNote").value.trim();
  await api(`/api/approvals/${approvalId}/${decision}`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });
  showStatus(decision === "approve" ? "Passo aprovado e simulado." : "Passo rejeitado.");
  await Promise.all([loadSequences(), loadApprovals(), loadJourneys(), loadAgentActions()]);
}

async function loadJourneys() {
  const data = await api("/api/sequences/journeys");
  renderJourneys(data.items || []);
}

function renderJourneys(items) {
  const container = $("#journeysTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma jornada criada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Lead", "Sequencia", "Passo", "Status", "Proxima acao", "Bloqueio", ""],
    items.map((journey) => [
      journey.id,
      escapeHtml(journey.trade_name || journey.legal_name || journey.email || "-"),
      escapeHtml(journey.sequence_name),
      escapeHtml(`${journey.current_step_number}. ${journey.step_name || "-"}`),
      badge(journey.status, experimentStatusTone(journey.status)),
      escapeHtml(fmt(journey.next_action_at)),
      escapeHtml(fmt(journey.block_reason)),
      journey.status === "waiting" ? `<button class="row-action" data-prepare-next="${journey.id}">Preparar proximo</button>` : "",
    ]),
  );
  $$("[data-prepare-next]").forEach((button) => {
    button.addEventListener("click", () => prepareNextJourney(button.dataset.prepareNext));
  });
}

async function prepareNextJourney(journeyId) {
  await api(`/api/sequences/journeys/${journeyId}/prepare-next`, { method: "POST", body: "{}" });
  showStatus("Proximo passo preparado para aprovacao.");
  await Promise.all([loadApprovals(), loadJourneys(), loadAgentActions()]);
}

async function loadAgentActions() {
  const data = await api("/api/agent-actions");
  renderAgentActions(data.items || []);
}

function renderAgentActions(items) {
  const container = $("#agentActionsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma acao registrada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Data", "Acao", "Origem", "Lead", "Sequencia", "Motivo"],
    items.map((action) => [
      escapeHtml(action.created_at),
      badge(action.action_type, "purple"),
      badge(action.source),
      escapeHtml(fmt(action.email)),
      escapeHtml(fmt(action.sequence_name)),
      escapeHtml(action.reason),
    ]),
  );
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
  $("#enrichCompanyBtn").addEventListener("click", enrichCompanyFromForm);
  $("#loadEnrichmentBtn").addEventListener("click", loadEnrichmentFromForm);
  $("#createLeadsFromListBtn").addEventListener("click", createLeadsFromExperimentList);
  $("#refreshExperimentLeadsBtn").addEventListener("click", loadExperimentLeads);
  $("#createCampaignBtn").addEventListener("click", createCampaignFromForm);
  $("#refreshCampaignsBtn").addEventListener("click", loadCampaigns);
  $("#recordExperimentEventBtn").addEventListener("click", recordExperimentEvent);
  $("#clearTemplateFormBtn").addEventListener("click", clearTemplateForm);
  $("#refreshTemplatesBtn").addEventListener("click", loadTemplates);
  $("#createTemplateBtn").addEventListener("click", createTemplateFromForm);
  $("#createTemplateVersionBtn").addEventListener("click", createTemplateVersionFromForm);
  $("#renderTemplateBtn").addEventListener("click", renderTemplateFromForm);
  $("#useTemplateInCampaignBtn").addEventListener("click", useTemplateInCampaign);
  $("#createSequenceBtn").addEventListener("click", createSequenceFromForm);
  $("#refreshSequencesBtn").addEventListener("click", loadSequenceWorkspace);
  $("#refreshApprovalsBtn").addEventListener("click", loadApprovals);
  $("#refreshJourneysBtn").addEventListener("click", loadJourneys);
  $("#refreshAgentActionsBtn").addEventListener("click", loadAgentActions);
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
