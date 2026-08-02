const state = {
  view: "dashboard",
  companies: [],
  selectedCompanies: new Set(),
  savedFilters: [],
  lists: [],
  currentListId: null,
  templates: [],
  selectedTemplateId: null,
  lastRenderedTemplate: null,
  sequences: [],
  icpRules: [],
  priorityQueue: [],
  replies: [],
  handoffs: [],
  meetings: [],
  commandCenter: null,
  leadTimeline: null,
  okrs: null,
  agentGovernance: null,
  playbooks: null,
  playbookExecutionPlans: [],
  notifications: null,
  workspaceContext: null,
  workspaceComparison: null,
  saasAccount: null,
  officialCheckpoints: [],
  officialPostgresPlan: null,
  postgresStagingSummary: null,
  postgresStagingCompanies: [],
  scoringConfig: null,
  companyScoringConfig: null,
  scoreConfigVersions: [],
  scoreConfigDiff: null,
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
    command: "Centro de Comando",
    companies: "Pesquisa de empresas",
    postgres: "Receita DB",
    lists: "Listas",
    import: "Importacao",
    enrichment: "Enriquecimento",
    experiments: "Experimentos",
    templates: "Templates",
    sequences: "Sequencias",
    icp: "ICP SDR",
    replies: "Respostas",
    hygiene: "Higiene de emails",
    audit: "Auditoria",
  };
  $("#pageTitle").textContent = titles[view] || "Radar CNPJ";
  loadViewData(view).catch((err) => showStatus(err.message, "warn"));
}

async function loadViewData(view = state.view) {
  if (view === "dashboard") await loadDashboard();
  if (view === "command") {
    await Promise.all([
      loadCommandCenter(),
      loadNotifications(),
      loadWorkspaceComparison(),
      loadSaasAccount(),
      loadOkrs(),
      loadPlaybooks(),
      loadPlaybookExecutionPlans(),
      loadAgentGovernance(),
    ]);
  }
  if (view === "companies") {
    await loadLists();
    await loadSavedFilters();
    await loadCompanies();
  }
  if (view === "postgres") await loadPostgresStaging();
  if (view === "lists") await loadLists(true);
  if (view === "import") {
    await loadOfficialCatalog();
    await Promise.all([loadOfficialCheckpoints(), loadPostgresPlan()]);
  }
  if (view === "experiments") {
    await loadLists();
    await loadExperiments();
  }
  if (view === "templates") await loadTemplates();
  if (view === "sequences") await loadSequenceWorkspace();
  if (view === "icp") await loadIcpWorkspace();
  if (view === "replies") await loadReplyWorkspace();
  if (view === "hygiene") await Promise.all([loadScoringConfig(), loadCompanyScoringConfig(), loadScoreConfigVersions()]);
  if (view === "audit") await loadAudit();
}

function metric(label, value, tone = "") {
  return `<article class="metric ${tone}"><span>${label}</span><strong>${fmt(value)}</strong></article>`;
}

function brl(cents) {
  return `R$ ${(Number(cents || 0) / 100).toFixed(2).replace(".", ",")}`;
}

async function loadDashboard() {
  const data = await api("/api/dashboard");
  if (data.active_workspace) renderWorkspaceContext({ ...(state.workspaceContext || {}), active_workspace: data.active_workspace });
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

function workspaceName(workspace) {
  return workspace?.profile?.display_name || workspace?.name || "-";
}

async function loadWorkspaceContext() {
  const data = await api("/api/workspace-context");
  state.workspaceContext = data;
  renderWorkspaceContext(data);
  return data;
}

function renderWorkspaceContext(data) {
  const select = $("#workspaceContextSelect");
  const label = $("#activeWorkspaceLabel");
  if (!select || !label) return;
  const active = data?.active_workspace || {};
  const workspaces = data?.workspaces || state.workspaceContext?.workspaces || [];
  label.textContent = workspaceName(active);
  select.innerHTML = workspaces.length
    ? workspaces
        .map((workspace) => `<option value="${escapeHtml(workspace.id)}">${escapeHtml(workspaceName(workspace))}</option>`)
        .join("")
    : `<option value="">Nenhum workspace</option>`;
  if (active.id) select.value = String(active.id);
}

async function setWorkspaceContextFromForm() {
  const orgId = Number($("#workspaceContextSelect").value || 0);
  if (!orgId) return showStatus("Selecione um workspace.", "warn");
  const data = await api("/api/workspace-context", {
    method: "POST",
    body: JSON.stringify({ org_id: orgId }),
  });
  state.workspaceContext = data;
  state.currentListId = null;
  state.selectedCompanies.clear();
  renderWorkspaceContext(data);
  showStatus(`Workspace ativo: ${workspaceName(data.active_workspace)}.`);
  await loadViewData(state.view);
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

async function loadCommandCenter() {
  const data = await api("/api/command-center");
  state.commandCenter = data;
  renderCommandMetrics(data.metrics || {});
  renderCommandInbox(data.inbox?.items || []);
  renderCommandKanban(data.kanban?.columns || []);
  renderCommandActivity(data.activity?.items || []);
}

function renderCommandMetrics(metrics) {
  $("#commandMetrics").innerHTML = [
    metric("Aprovacoes", metrics.pending_approvals || 0, metrics.pending_approvals ? "amber" : ""),
    metric("Handoffs", metrics.pending_handoffs || 0, metrics.pending_handoffs ? "amber" : ""),
    metric("Reunioes abertas", metrics.open_meetings || 0, metrics.open_meetings ? "green" : ""),
    metric("Leads ativos", metrics.active_leads || 0),
    metric("Acoes logadas", metrics.recent_actions || 0),
  ].join("");
}

async function loadOkrs() {
  const data = await api("/api/okrs");
  state.okrs = data;
  renderOkrs(data);
}

function renderOkrs(data) {
  const container = $("#okrPanel");
  if (!container) return;
  const objectives = data?.objectives || [];
  const kpis = data?.kpis || [];
  const objectiveMarkup = objectives.length
    ? objectives
        .map(
          (objective) => `
            <section class="okr-objective">
              <div class="okr-title">
                <div>
                  <h3>${escapeHtml(objective.title || "-")}</h3>
                  <p class="muted">${escapeHtml(objective.description || [objective.period_start, objective.period_end].filter(Boolean).join(" ate ") || "-")}</p>
                </div>
                ${badge(objective.status || "-", objective.status === "active" ? "green" : "purple")}
              </div>
              <div class="okr-kr-list">
                ${(objective.key_results || [])
                  .map((kr) => {
                    const progress = Math.max(0, Math.min(100, Number(kr.progress || 0)));
                    const formula = kr.kpi?.formula || "";
                    return `
                      <article class="okr-kr">
                        <div class="okr-kr-head">
                          <strong>${escapeHtml(kr.title || "-")}</strong>
                          ${badge(`${progress}%`, progress >= 100 ? "green" : progress >= 50 ? "amber" : "purple")}
                        </div>
                        <div class="bar-track"><div class="bar-fill" style="width:${progress}%"></div></div>
                        <div class="stat-line compact-line">
                          ${badge(`${fmt(kr.current_value)} / ${fmt(kr.target_value)}`)}
                          ${badge(kr.kpi_key || "-", "purple")}
                        </div>
                        <small>${escapeHtml(formula || "-")}</small>
                      </article>
                    `;
                  })
                  .join("")}
              </div>
            </section>
          `,
        )
        .join("")
    : `<div class="empty-state">Nenhum OKR configurado.</div>`;
  const kpiMarkup = kpis.length
    ? table(
        ["KPI", "Valor", "Formula", "Origem"],
        kpis.map((kpi) => [
          escapeHtml(kpi.name || kpi.kpi_key),
          badge(kpi.current_value ?? 0, kpi.direction === "decrease" && kpi.current_value ? "amber" : "green"),
          `<span class="truncate" title="${escapeHtml(kpi.formula || "")}">${escapeHtml(kpi.formula || "-")}</span>`,
          escapeHtml((kpi.source_tables || []).join(", ") || "-"),
        ]),
      )
    : `<div class="empty-state">Catalogo de KPIs vazio.</div>`;
  container.innerHTML = `
    <div>${objectiveMarkup}</div>
    <div class="table-wrap">${kpiMarkup}</div>
  `;
}

async function loadNotifications() {
  const data = await api("/api/notifications");
  state.notifications = data;
  renderNotifications(data);
}

function notificationSeverityTone(severity) {
  if (severity === "critical") return "red";
  if (severity === "high") return "amber";
  if (severity === "success") return "green";
  if (severity === "medium") return "purple";
  return "";
}

function notificationStatusTone(status) {
  if (status === "pending") return "amber";
  if (status === "sent") return "purple";
  if (status === "read") return "green";
  if (status === "dismissed") return "";
  return "";
}

function renderNotifications(data) {
  const summary = data?.summary || {};
  const items = data?.items || [];
  $("#notificationSummary").innerHTML = [
    metric("Pendentes", summary.pending || 0, summary.pending ? "amber" : ""),
    metric("Lidas", summary.read || 0),
    metric("Dispensadas", summary.dismissed || 0),
    metric("Total", summary.total || 0),
    metric("Criticas", (summary.pending_by_severity || {}).critical || 0, (summary.pending_by_severity || {}).critical ? "red" : ""),
  ].join("");

  $("#notificationsTable").innerHTML = items.length
    ? table(
        ["Tipo", "Severidade", "Status", "Titulo", "Origem", "Criada", ""],
        items.map((item) => [
          escapeHtml(item.notification_type),
          badge(item.severity, notificationSeverityTone(item.severity)),
          badge(item.status, notificationStatusTone(item.status)),
          `<span class="truncate" title="${escapeHtml(item.body || "")}">${escapeHtml(item.title || "-")}</span>`,
          escapeHtml(`${item.source_type} #${item.source_id}`),
          escapeHtml(item.created_at || "-"),
          item.status === "dismissed"
            ? ""
            : `<button class="row-action" data-notification-read="${escapeHtml(item.id)}">Lida</button><button class="row-action" data-notification-dismiss="${escapeHtml(item.id)}">Dispensar</button>`,
        ]),
      )
    : `<div class="empty-state">Nenhuma notificacao gerada.</div>`;
  $$("[data-notification-read]").forEach((button) => {
    button.addEventListener("click", () => updateNotificationStatus(button.dataset.notificationRead, "mark-read"));
  });
  $$("[data-notification-dismiss]").forEach((button) => {
    button.addEventListener("click", () => updateNotificationStatus(button.dataset.notificationDismiss, "dismiss"));
  });
}

async function generateNotificationsFromSignals() {
  const result = await api("/api/notifications/generate", { method: "POST", body: "{}" });
  showStatus(`${result.created || 0} notificacoes novas geradas.`);
  await loadNotifications();
}

async function updateNotificationStatus(notificationId, action) {
  await api(`/api/notifications/${notificationId}/${action}`, { method: "POST", body: "{}" });
  showStatus(action === "dismiss" ? "Notificacao dispensada." : "Notificacao marcada como lida.");
  await loadNotifications();
}

async function loadWorkspaceComparison() {
  const data = await api("/api/workspaces/comparison");
  state.workspaceComparison = data;
  renderWorkspaceComparison(data);
}

async function loadSaasAccount() {
  const data = await api("/api/saas/account");
  state.saasAccount = data;
  renderSaasAccount(data);
}

function renderWorkspaceComparison(data) {
  const workspaces = data?.workspaces || [];
  const snapshots = data?.snapshots || [];
  const totals = workspaces.reduce(
    (acc, item) => {
      const metrics = item.metrics || {};
      acc.leads += Number(metrics.active_leads || 0);
      acc.handoffs += Number(metrics.pending_handoffs || 0);
      acc.notifications += Number(metrics.pending_notifications || 0);
      acc.cost += Number(metrics.agent_cost || 0);
      return acc;
    },
    { leads: 0, handoffs: 0, notifications: 0, cost: 0 },
  );
  $("#workspaceComparisonSummary").innerHTML = [
    metric("Workspaces", workspaces.length),
    metric("Leads ativos", totals.leads),
    metric("Handoffs", totals.handoffs, totals.handoffs ? "amber" : ""),
    metric("Notificacoes", totals.notifications, totals.notifications ? "amber" : ""),
    metric("Custo IA", totals.cost.toFixed(4)),
  ].join("");

  $("#workspaceSnapshotSelect").innerHTML = workspaces
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.profile?.display_name || item.name)}</option>`)
    .join("");

  $("#workspaceComparisonTable").innerHTML = workspaces.length
    ? table(
        ["Workspace", "Vertical", "Empresas", "Leads", "Respostas", "Handoffs", "Reunioes", "Notificacoes", "IA", "Playbook"],
        workspaces.map((item) => {
          const metrics = item.metrics || {};
          return [
            escapeHtml(item.profile?.display_name || item.name),
            escapeHtml(item.profile?.vertical || "-"),
            badge(metrics.companies || 0, "purple"),
            badge(metrics.active_leads || 0, "green"),
            escapeHtml(metrics.replies || 0),
            badge(metrics.pending_handoffs || 0, metrics.pending_handoffs ? "amber" : ""),
            escapeHtml(`${metrics.open_meetings || 0}/${metrics.completed_meetings || 0}`),
            badge(metrics.pending_notifications || 0, metrics.pending_notifications ? "amber" : ""),
            escapeHtml(`${metrics.agent_calls || 0} / ${Number(metrics.agent_cost || 0).toFixed(4)}`),
            escapeHtml(metrics.active_playbook ? `${metrics.active_playbook} v${metrics.active_playbook_version}` : "-"),
          ];
        }),
      )
    : `<div class="empty-state">Nenhum workspace cadastrado.</div>`;

  $("#workspaceSnapshotsTable").innerHTML = snapshots.length
    ? table(
        ["Data", "Workspace", "Leads", "Handoffs", "Custo IA"],
        snapshots.map((item) => [
          escapeHtml(item.created_at || "-"),
          escapeHtml(item.display_name || item.workspace_name || "-"),
          escapeHtml(item.metrics?.active_leads || 0),
          escapeHtml(item.metrics?.pending_handoffs || 0),
          escapeHtml(Number(item.metrics?.agent_cost || 0).toFixed(4)),
        ]),
      )
    : `<div class="empty-state">Nenhum snapshot executivo.</div>`;
}

function renderSaasAccount(data) {
  const wallet = data?.wallet || {};
  const plans = data?.plans || [];
  const subscription = data?.subscription || null;
  const keys = data?.api_keys || [];
  const transactions = data?.transactions || [];
  const usageEvents = data?.usage_events || [];
  const activeKeys = keys.filter((key) => key.status === "active").length;
  const blockedUsage = usageEvents.filter((event) => event.status !== "ok").length;
  const activePlan = subscription?.plan || plans.find((plan) => plan.code === wallet.plan_name);
  $("#saasSummary").innerHTML = [
    metric("Saldo", wallet.balance || 0, Number(wallet.balance || 0) > 0 ? "green" : ""),
    metric("Plano", activePlan?.code || wallet.plan_name || "sem plano"),
    metric("Chaves ativas", activeKeys, activeKeys ? "green" : ""),
    metric("Creditos do plano", activePlan?.included_credits ?? 0),
    metric("Uso API", usageEvents.length),
    metric("Bloqueios", blockedUsage, blockedUsage ? "amber" : ""),
  ].join("");

  renderSaasPlans(plans, subscription);
  renderSaasPublicApiDocs();

  $("#saasApiKeysTable").innerHTML = keys.length
    ? table(
        ["Nome", "Status", "Mascara", "Escopos", "Criada", "Revogada", "Ultimo uso", ""],
        keys.map((key) => [
          escapeHtml(key.name || "-"),
          badge(key.status, key.status === "active" ? "green" : "purple"),
          escapeHtml(key.masked_token || "-"),
          escapeHtml((key.scopes || []).join(", ") || "-"),
          escapeHtml(key.created_at || "-"),
          escapeHtml(key.revoked_at || "-"),
          escapeHtml(key.last_used_at || "-"),
          key.status === "active"
            ? `<button class="row-action" data-revoke-saas-key="${escapeHtml(key.id)}">Revogar</button>`
            : badge("revogada", "purple"),
        ]),
      )
    : `<div class="empty-state">Nenhuma chave de API neste workspace.</div>`;

  $("#saasTransactionsTable").innerHTML = transactions.length
    ? table(
        ["Data", "Valor", "Saldo", "Motivo", "Referencia"],
        transactions.map((transaction) => {
          const amount = Number(transaction.amount || 0);
          return [
            escapeHtml(transaction.created_at || "-"),
            badge(amount > 0 ? `+${amount}` : amount, amount > 0 ? "green" : "amber"),
            escapeHtml(transaction.balance_after ?? "-"),
            escapeHtml(transaction.reason || "-"),
            escapeHtml([transaction.reference_type, transaction.reference_id].filter(Boolean).join(" #") || "-"),
          ];
        }),
      )
    : `<div class="empty-state">Nenhum lancamento de credito.</div>`;

  $("#saasUsageTable").innerHTML = usageEvents.length
    ? table(
        ["Data", "Status", "HTTP", "Endpoint", "Custo", "Chave", "Mensagem"],
        usageEvents.map((event) => [
          escapeHtml(event.created_at || "-"),
          badge(event.status, event.status === "ok" ? "green" : "amber"),
          escapeHtml(event.response_code || "-"),
          escapeHtml(event.endpoint || "-"),
          escapeHtml(event.cost ?? 0),
          escapeHtml(event.api_key_mask || event.api_key_name || "-"),
          escapeHtml(event.message || "-"),
        ]),
      )
    : `<div class="empty-state">Nenhuma chamada de API registrada.</div>`;

  $$("[data-revoke-saas-key]").forEach((button) => {
    button.addEventListener("click", () => revokeSaasApiKey(button.dataset.revokeSaasKey));
  });
}

function renderSaasPlans(plans, subscription) {
  $("#saasPlanSelect").innerHTML = plans
    .map((plan) => `<option value="${escapeHtml(plan.code)}">${escapeHtml(plan.name)} - ${escapeHtml(brl(plan.monthly_price_brl_cents))}</option>`)
    .join("");
  if (subscription?.plan?.code) $("#saasPlanSelect").value = subscription.plan.code;
  $("#saasSubscriptionSummary").innerHTML = subscription
    ? table(
        ["Plano", "Status", "Periodo", "Inicio", "Renova", "Creditos", "API/min"],
        [
          [
            escapeHtml(subscription.plan?.name || "-"),
            badge(subscription.status || "-", subscription.status === "active" ? "green" : "purple"),
            escapeHtml(subscription.billing_period || "-"),
            escapeHtml(subscription.started_at || "-"),
            escapeHtml(subscription.renews_at || "-"),
            badge(subscription.plan?.included_credits || 0, "green"),
            badge(subscription.plan?.api_rate_limit_per_minute || 0, "purple"),
          ],
        ],
      )
    : `<div class="empty-state">Nenhum plano aplicado neste workspace.</div>`;

  $("#saasPlansTable").innerHTML = plans.length
    ? table(
        ["Plano", "Preco", "Creditos", "API/min", "Chaves", "Recursos", "Credito extra"],
        plans.map((plan) => [
          `<strong>${escapeHtml(plan.name)}</strong><br /><span class="muted">${escapeHtml(plan.code)}</span>`,
          escapeHtml(brl(plan.monthly_price_brl_cents)),
          badge(plan.included_credits, plan.included_credits ? "green" : ""),
          badge(plan.api_rate_limit_per_minute || 0, plan.allow_public_api ? "purple" : ""),
          escapeHtml(plan.max_api_keys || 0),
          [
            plan.allow_public_api ? "API" : "",
            plan.allow_exports ? "Export" : "",
            plan.allow_enrichment ? "Enrich" : "",
            plan.allow_agent ? "Agente" : "",
            plan.allow_campaigns ? "Campanhas" : "",
          ]
            .filter(Boolean)
            .map((item) => badge(item, "green"))
            .join(" "),
          escapeHtml(brl(plan.overage_credit_price_brl_cents)),
        ]),
      )
    : `<div class="empty-state">Nenhum plano SaaS cadastrado.</div>`;
}

function renderSaasPublicApiDocs() {
  const origin = window.location.origin || "http://127.0.0.1:8000";
  const openapiUrl = `${origin}/api/public/openapi.json`;
  const searchUrl = `${origin}/api/public/companies?state=SP&has_email=1&limit=10`;
  $("#saasPublicApiDocs").innerHTML = table(
    ["Item", "Contrato atual"],
    [
      ["OpenAPI", `<a href="${escapeHtml(openapiUrl)}" target="_blank" rel="noreferrer">${escapeHtml(openapiUrl)}</a>`],
      ["Endpoint", `<code>${escapeHtml(searchUrl)}</code>`],
      ["Autenticacao", `<code>X-API-Key: &lt;token&gt;</code> ou <code>Authorization: Bearer &lt;token&gt;</code>`],
      ["Escopo", badge("companies:read", "green")],
      ["Custo", badge("1 credito por chamada bem-sucedida", "amber")],
      ["Rate limit", badge("60/min por chave", "purple")],
    ],
  );
}

function renderCreatedSaasToken(token) {
  $("#saasCreatedToken").innerHTML = token
    ? previewHtml(token)
    : `<div class="empty-state">Nenhum token criado nesta sessao.</div>`;
}

async function createSaasApiKeyFromForm() {
  const result = await api("/api/saas/api-keys", {
    method: "POST",
    body: JSON.stringify({
      name: $("#saasApiKeyName").value.trim(),
      scopes: commaValues("#saasApiKeyScopes"),
    }),
  });
  renderCreatedSaasToken(result.token);
  $("#saasApiKeyName").value = "";
  showStatus("Chave de API criada.");
  await loadSaasAccount();
}

async function revokeSaasApiKey(keyId) {
  await api(`/api/saas/api-keys/${keyId}/revoke`, {
    method: "POST",
    body: JSON.stringify({ reason: "Revogada pelo Command Center" }),
  });
  renderCreatedSaasToken(null);
  showStatus("Chave de API revogada.");
  await loadSaasAccount();
}

async function adjustSaasCreditsFromForm() {
  const amount = Number($("#saasCreditAmount").value || 0);
  if (!amount) return showStatus("Informe um valor de creditos diferente de zero.", "warn");
  await api("/api/saas/credits/adjust", {
    method: "POST",
    body: JSON.stringify({
      amount,
      reason: $("#saasCreditReason").value.trim(),
    }),
  });
  $("#saasCreditAmount").value = "";
  $("#saasCreditReason").value = "";
  showStatus("Ajuste de creditos registrado.");
  await loadSaasAccount();
}

async function applySaasPlanFromForm() {
  const planCode = $("#saasPlanSelect").value;
  if (!planCode) return showStatus("Selecione um plano.", "warn");
  const result = await api("/api/saas/plan-subscription", {
    method: "POST",
    body: JSON.stringify({
      plan_code: planCode,
      billing_period: $("#saasPlanBillingPeriod").value,
      note: $("#saasPlanNote").value.trim(),
      source: "command_center",
    }),
  });
  $("#saasPlanNote").value = "";
  showStatus(`Plano ${result.plan?.name || planCode} aplicado ao workspace.`);
  await loadSaasAccount();
}

function renderWorkspaceOnboardingResult(result) {
  const container = $("#workspaceOnboardingResult");
  if (!container) return;
  if (!result) {
    container.innerHTML = `<div class="empty-state">Nenhum onboarding executado nesta sessao.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Workspace", "Playbook", "ICP", "Template", "Sequencia", "OKR", "Run"],
    [
      [
        escapeHtml(result.profile?.display_name || result.workspace?.name || "-"),
        escapeHtml(result.playbook?.name || "-"),
        escapeHtml(result.icp_rule?.name || "-"),
        escapeHtml(result.template?.name || "-"),
        escapeHtml(result.sequence?.name || "-"),
        escapeHtml(result.objective?.title || "-"),
        badge(result.onboarding_run?.id || "-"),
      ],
    ],
  );
}

async function runWorkspaceOnboardingFromForm() {
  const name = $("#onboardingWorkspaceName").value.trim();
  if (!name) return showStatus("Informe o nome da empresa.", "warn");
  const sourcePlaybookId = Number($("#onboardingSourcePlaybook").value || 0);
  const payload = {
    workspace: {
      name,
      vertical: $("#onboardingVertical").value.trim(),
      sending_domain: $("#onboardingSendingDomain").value.trim(),
      sender_name: $("#onboardingSender").value.trim(),
      default_tone: $("#onboardingTone").value.trim(),
      brand_color: $("#onboardingBrandColor").value.trim() || undefined,
    },
    icp: {
      criteria: {
        states: commaValues("#onboardingStates"),
        cnaes: commaValues("#onboardingCnaes"),
        min_email_score: Number($("#onboardingMinEmailScore").value || 30),
      },
    },
    okr: {
      key_results: [
        {
          title: "Receber respostas qualificadas",
          kpi_key: "replies_received",
          target_value: Number($("#onboardingTarget").value || 10),
        },
      ],
    },
  };
  if (sourcePlaybookId) {
    payload.playbook = {
      source_playbook_id: sourcePlaybookId,
      name: `${name} - playbook inicial`,
    };
  }
  const result = await api("/api/workspaces/onboarding", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.workspaceContext = result.workspace_context;
  renderWorkspaceContext(result.workspace_context);
  renderWorkspaceOnboardingResult(result);
  showStatus(`Onboarding de ${result.profile?.display_name || name} concluido.`);
  await loadViewData("command");
  renderWorkspaceOnboardingResult(result);
}

async function createWorkspaceFromForm() {
  await api("/api/workspaces", {
    method: "POST",
    body: JSON.stringify({
      name: $("#workspaceName").value.trim(),
      vertical: $("#workspaceVertical").value.trim(),
      default_tone: $("#workspaceTone").value.trim(),
      sender_name: $("#workspaceSender").value.trim(),
    }),
  });
  showStatus("Workspace criado para comparacao executiva.");
  await loadWorkspaceContext();
  await loadWorkspaceComparison();
  if (state.view === "command") await loadPlaybooks();
}

async function createWorkspaceSnapshotFromForm() {
  const workspaceId = Number($("#workspaceSnapshotSelect").value || 0);
  if (!workspaceId) return showStatus("Selecione um workspace.", "warn");
  await api(`/api/workspaces/${workspaceId}/snapshot`, { method: "POST", body: "{}" });
  showStatus("Snapshot executivo criado.");
  await loadWorkspaceComparison();
}

async function loadPlaybooks() {
  const data = await api("/api/playbooks");
  state.playbooks = data;
  renderPlaybooks(data);
}

async function loadPlaybookExecutionPlans() {
  const data = await api("/api/playbook-execution-plans");
  state.playbookExecutionPlans = data.items || [];
  renderPlaybookExecutionPlans(state.playbookExecutionPlans);
}

function playbookOptionLabel(playbook) {
  const active = playbook.active_version;
  return `${playbook.name} ${active ? `(v${active.version_number})` : ""}`;
}

function selectedPlaybook() {
  const id = Number($("#playbookSelect").value || 0);
  return (state.playbooks?.playbooks || []).find((item) => item.id === id) || null;
}

function syncPlaybookVersionForm(playbook) {
  const active = playbook?.active_version;
  $("#playbookVersionContent").value = active ? JSON.stringify(active.content || {}, null, 2) : "{}";
  if ($("#playbookCloneName")) {
    $("#playbookCloneName").placeholder = playbook ? `${playbook.name} (copia)` : "Nome opcional no destino";
  }
}

function renderSelectedPlaybookVersions(playbook) {
  const versions = playbook?.versions || [];
  $("#playbookVersionsTable").innerHTML = versions.length
    ? table(
        ["Versao", "Status", "Descricao", "Criada", ""],
        versions.map((version) => [
          `v${version.version_number}`,
          badge(version.status, version.status === "active" ? "green" : "purple"),
          escapeHtml(version.description || "-"),
          escapeHtml(version.created_at || "-"),
          `<button class="row-action" data-playbook-apply="${escapeHtml(playbook.id)}" data-playbook-version="${escapeHtml(version.id)}">Aplicar</button>`,
        ]),
      )
    : `<div class="empty-state">Nenhuma versao registrada.</div>`;
  $$("[data-playbook-apply]").forEach((button) => {
    button.addEventListener("click", () => applyPlaybookFromForm(button.dataset.playbookApply, button.dataset.playbookVersion));
  });
}

function renderPlaybooks(data) {
  const playbooks = data?.playbooks || [];
  const active = data?.active_application;
  const profile = data?.company_profile || {};
  const versionCount = playbooks.reduce((total, item) => total + (item.versions || []).length, 0);
  $("#playbookSummary").innerHTML = [
    metric("Workspace", profile.display_name || "-"),
    metric("Playbook ativo", active ? active.playbook_name : "-"),
    metric("Versao ativa", active ? `v${active.version_number}` : "-"),
    metric("Biblioteca", playbooks.length),
    metric("Versoes", versionCount),
  ].join("");

  const previousSelection = Number($("#playbookSelect").value || 0);
  $("#playbookSelect").innerHTML = playbooks
    .map((playbook) => `<option value="${escapeHtml(playbook.id)}">${escapeHtml(playbookOptionLabel(playbook))}</option>`)
    .join("");
  const selectedId = playbooks.some((item) => item.id === previousSelection)
    ? previousSelection
    : active?.playbook_id || playbooks[0]?.id || "";
  $("#playbookSelect").value = selectedId;
  const selected = selectedPlaybook();
  syncPlaybookVersionForm(selected);
  renderSelectedPlaybookVersions(selected);
  renderPlaybookCloneTargets(profile.org_id);
  renderOnboardingPlaybookOptions(playbooks);

  $("#playbooksTable").innerHTML = playbooks.length
    ? table(
        ["Nome", "Status", "Versao ativa", "Origem", "Atualizado", ""],
        playbooks.map((playbook) => [
          escapeHtml(playbook.name),
          badge(playbook.status, playbook.status === "active" ? "green" : "purple"),
          playbook.active_version ? `v${playbook.active_version.version_number}` : "-",
          escapeHtml(playbook.source || "-"),
          escapeHtml(playbook.updated_at || "-"),
          `<button class="row-action" data-playbook-select="${escapeHtml(playbook.id)}">Selecionar</button>`,
        ]),
      )
    : `<div class="empty-state">Nenhum playbook registrado.</div>`;
  $$("[data-playbook-select]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#playbookSelect").value = button.dataset.playbookSelect;
      const playbook = selectedPlaybook();
      syncPlaybookVersionForm(playbook);
      renderSelectedPlaybookVersions(playbook);
    });
  });
}

function renderOnboardingPlaybookOptions(playbooks) {
  const select = $("#onboardingSourcePlaybook");
  if (!select) return;
  select.innerHTML = [
    `<option value="">Default do novo workspace</option>`,
    ...playbooks.map((playbook) => `<option value="${escapeHtml(playbook.id)}">${escapeHtml(playbookOptionLabel(playbook))}</option>`),
  ].join("");
}

function renderPlaybookCloneTargets(activeOrgId) {
  const select = $("#playbookCloneTarget");
  if (!select) return;
  const activeId = Number(activeOrgId || state.workspaceContext?.active_workspace?.id || 0);
  const options = (state.workspaceContext?.workspaces || []).filter((workspace) => Number(workspace.id) !== activeId);
  select.innerHTML = options.length
    ? options
        .map((workspace) => `<option value="${escapeHtml(workspace.id)}">${escapeHtml(workspaceName(workspace))}</option>`)
        .join("")
    : `<option value="">Nenhum destino disponivel</option>`;
}

function parseJsonField(selector, message) {
  try {
    return JSON.parse($(selector).value || "{}");
  } catch (err) {
    showStatus(message, "warn");
    return null;
  }
}

async function createPlaybookFromForm() {
  const content = parseJsonField("#playbookContent", "Conteudo JSON do playbook invalido.");
  if (!content) return;
  await api("/api/playbooks", {
    method: "POST",
    body: JSON.stringify({
      name: $("#playbookName").value.trim(),
      description: $("#playbookDescription").value.trim(),
      content,
    }),
  });
  showStatus("Playbook criado com versao 1 ativa.");
  await loadPlaybooks();
}

async function createPlaybookVersionFromForm() {
  const playbook = selectedPlaybook();
  if (!playbook) return showStatus("Selecione um playbook.", "warn");
  const content = parseJsonField("#playbookVersionContent", "Conteudo JSON da nova versao invalido.");
  if (!content) return;
  await api(`/api/playbooks/${playbook.id}/versions`, {
    method: "POST",
    body: JSON.stringify({
      description: $("#playbookVersionDescription").value.trim(),
      content,
    }),
  });
  showStatus("Nova versao de playbook criada.");
  await loadPlaybooks();
}

async function applyPlaybookFromForm(playbookId = null, versionId = null) {
  const playbook = playbookId ? (state.playbooks?.playbooks || []).find((item) => item.id === Number(playbookId)) : selectedPlaybook();
  if (!playbook) return showStatus("Selecione um playbook.", "warn");
  const activeVersionId = versionId || playbook.active_version?.id;
  await api(`/api/playbooks/${playbook.id}/apply`, {
    method: "POST",
    body: JSON.stringify({
      version_id: Number(activeVersionId || 0) || undefined,
      note: $("#playbookApplyNote").value.trim(),
    }),
  });
  showStatus("Playbook aplicado ao workspace.");
  await loadPlaybooks();
}

async function createPlaybookExecutionPlanFromForm() {
  const playbook = selectedPlaybook();
  if (!playbook) return showStatus("Selecione um playbook.", "warn");
  const result = await api(`/api/playbooks/${playbook.id}/execution-plans`, {
    method: "POST",
    body: JSON.stringify({
      version_id: playbook.active_version?.id,
      apply_note: $("#playbookApplyNote").value.trim() || undefined,
    }),
  });
  showStatus(`Plano ${result.id} criado para revisao.`);
  await loadPlaybookExecutionPlans();
}

async function applyPlaybookExecutionPlan(planId) {
  await api(`/api/playbook-execution-plans/${planId}/apply`, {
    method: "POST",
    body: JSON.stringify({ note: $("#playbookApplyNote").value.trim() }),
  });
  showStatus(`Plano ${planId} aplicado.`);
  await Promise.all([loadPlaybookExecutionPlans(), loadPlaybooks(), loadOkrs(), loadCommandCenter()]);
}

function planCreatesSummary(plan) {
  return (plan.diff?.creates || []).map((entry) => `${entry.type}: ${entry.name}`).join("\n");
}

function planGuardsSummary(plan) {
  return (plan.diff?.guards || []).join("\n");
}

function planArtifactsSummary(plan) {
  const artifacts = plan.created_artifacts || {};
  const entries = Object.entries(artifacts);
  if (!entries.length) return "-";
  return entries.map(([key, value]) => `${key}: ${value}`).join("\n");
}

function renderPlaybookExecutionPlans(items) {
  const target = $("#playbookExecutionPlansTable");
  if (!target) return;
  target.innerHTML = items.length
    ? table(
        ["ID", "Status", "Playbook", "Versao", "Cria", "Trilhos", "Criado", "Aplicado", ""],
        items.map((plan) => [
          escapeHtml(plan.id),
          badge(plan.status, plan.status === "applied" ? "green" : "purple"),
          escapeHtml(plan.playbook_name || "-"),
          plan.version_number ? `v${escapeHtml(plan.version_number)}` : "-",
          previewHtml(planCreatesSummary(plan)),
          previewHtml(plan.status === "applied" ? planArtifactsSummary(plan) : planGuardsSummary(plan)),
          escapeHtml(plan.created_at || "-"),
          escapeHtml(plan.applied_at || "-"),
          plan.status === "draft"
            ? `<button class="row-action" data-apply-playbook-plan="${escapeHtml(plan.id)}">Aplicar</button>`
            : badge("aplicado", "green"),
        ]),
      )
    : `<div class="empty-state">Nenhum plano de execucao criado neste workspace.</div>`;
  $$("[data-apply-playbook-plan]").forEach((button) => {
    button.addEventListener("click", () => applyPlaybookExecutionPlan(button.dataset.applyPlaybookPlan));
  });
}

async function clonePlaybookFromForm() {
  const playbook = selectedPlaybook();
  if (!playbook) return showStatus("Selecione um playbook.", "warn");
  const targetOrgId = Number($("#playbookCloneTarget").value || 0);
  if (!targetOrgId) return showStatus("Selecione um workspace de destino.", "warn");
  const clone = await api(`/api/playbooks/${playbook.id}/clone`, {
    method: "POST",
    body: JSON.stringify({
      target_org_id: targetOrgId,
      name: $("#playbookCloneName").value.trim() || undefined,
      description: $("#playbookCloneDescription").value.trim() || undefined,
    }),
  });
  $("#playbookCloneName").value = "";
  $("#playbookCloneDescription").value = "";
  showStatus(`Playbook clonado para o workspace ${targetOrgId} como ${clone.name}.`);
  await Promise.all([loadPlaybooks(), loadWorkspaceComparison()]);
}

async function loadAgentGovernance() {
  const data = await api("/api/agent-governance");
  state.agentGovernance = data;
  renderAgentGovernance(data);
}

function configOptionLabel(config) {
  return `v${config.version_number} - ${config.name} (${config.status})`;
}

function renderAgentGovernance(data) {
  const active = data?.active_config || {};
  const versions = data?.versions || [];
  const simulations = data?.simulations || [];
  const costs = data?.costs || [];
  const costSummary = data?.cost_summary || {};
  $("#agentGovernanceSummary").innerHTML = [
    metric("Versao ativa", active.version_number ? `v${active.version_number}` : "-"),
    metric("Status", active.status || "-"),
    metric("Modelo", active.model_name || "-"),
    metric("Chamadas IA", costSummary.total_calls || 0),
    metric("Custo estimado", Number(costSummary.estimated_cost || 0).toFixed(4)),
  ].join("");

  $("#agentSimulationConfig").innerHTML = versions
    .map((config) => `<option value="${escapeHtml(config.id)}">${escapeHtml(configOptionLabel(config))}</option>`)
    .join("");

  $("#agentVersionsTable").innerHTML = versions.length
    ? table(
        ["Versao", "Nome", "Status", "Modelo", "Criada", ""],
        versions.map((config) => [
          `v${config.version_number}`,
          escapeHtml(config.name),
          badge(config.status, config.status === "active" ? "green" : config.status === "staging" ? "amber" : "purple"),
          escapeHtml(config.model_name),
          escapeHtml(config.created_at || "-"),
          config.status === "active"
            ? ""
            : `<button class="row-action" data-agent-activate="${escapeHtml(config.id)}">Ativar</button>`,
        ]),
      )
    : `<div class="empty-state">Nenhuma versao registrada.</div>`;
  $$("[data-agent-activate]").forEach((button) => {
    button.addEventListener("click", () => activateAgentConfig(button.dataset.agentActivate));
  });

  $("#agentSimulationsTable").innerHTML = simulations.length
    ? table(
        ["Data", "Config", "Lead", "Cenario", "Decisao"],
        simulations.map((item) => [
          escapeHtml(item.created_at || "-"),
          escapeHtml(`v${item.version_number} - ${item.config_name}`),
          escapeHtml(item.lead_email || item.lead_id || "-"),
          escapeHtml(item.scenario || "-"),
          badge(item.result?.decision || item.status, item.result?.decision === "eligible_for_autonomy" ? "green" : "amber"),
        ]),
      )
    : `<div class="empty-state">Nenhuma simulacao registrada.</div>`;

  $("#agentCostsTable").innerHTML = costs.length
    ? table(
        ["Data", "Operacao", "Modelo", "Tokens", "Custo", "Lead"],
        costs.map((item) => [
          escapeHtml(item.created_at || "-"),
          escapeHtml(item.operation || "-"),
          escapeHtml(item.model_name || "-"),
          badge(item.total_tokens || 0, "purple"),
          escapeHtml(Number(item.estimated_cost || 0).toFixed(6)),
          escapeHtml(item.lead_email || item.lead_id || "-"),
        ]),
      )
    : `<div class="empty-state">Nenhum custo registrado.</div>`;
}

async function createAgentConfigFromForm() {
  let rules;
  try {
    rules = JSON.parse($("#agentConfigRules").value || "{}");
  } catch (err) {
    return showStatus("Rules JSON invalido.", "warn");
  }
  await api("/api/agent-governance/configs", {
    method: "POST",
    body: JSON.stringify({
      name: $("#agentConfigName").value.trim(),
      model_name: $("#agentConfigModel").value.trim(),
      prompt_text: $("#agentConfigPrompt").value.trim(),
      rules,
    }),
  });
  showStatus("Versao staging criada.");
  await loadAgentGovernance();
}

async function activateAgentConfig(configId) {
  await api(`/api/agent-governance/configs/${configId}/activate`, {
    method: "POST",
    body: "{}",
  });
  showStatus(`Configuracao ${configId} ativada.`);
  await loadAgentGovernance();
}

async function createAgentSimulationFromForm() {
  const payload = {
    config_version_id: Number($("#agentSimulationConfig").value || 0),
    lead_id: Number($("#agentSimulationLeadId").value || 0) || undefined,
    scenario: $("#agentSimulationScenario").value.trim() || "first_contact",
  };
  await api("/api/agent-governance/simulations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  showStatus("Simulacao local registrada.");
  await loadAgentGovernance();
}

async function recordAgentCostFromForm() {
  const payload = {
    config_version_id: Number($("#agentSimulationConfig").value || 0),
    lead_id: Number($("#agentSimulationLeadId").value || 0) || undefined,
    operation: $("#agentCostOperation").value.trim(),
    prompt_tokens: Number($("#agentPromptTokens").value || 0),
    completion_tokens: Number($("#agentCompletionTokens").value || 0),
    estimated_cost: Number($("#agentEstimatedCost").value || 0),
  };
  await api("/api/agent-governance/costs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  showStatus("Custo estimado registrado.");
  await loadAgentGovernance();
}

function commandTypeTone(type) {
  if (type === "meeting") return "green";
  if (type === "handoff") return "amber";
  if (type === "approval") return "purple";
  return "";
}

function priorityTone(priority) {
  if (priority === "urgent") return "red";
  if (priority === "high") return "amber";
  if (priority === "medium") return "purple";
  return "";
}

function renderCommandInbox(items) {
  const container = $("#commandInbox");
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma pendencia humana agora.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Tipo", "ID", "Prioridade", "Empresa", "Email", "Status", "Origem", "Motivo", ""],
    items.map((item) => {
      const actions = (item.actions || [])
        .map(
          (action) =>
            `<button class="row-action" data-command-action="${escapeHtml(action.decision)}" data-command-source-type="${escapeHtml(item.source_type)}" data-command-source-id="${escapeHtml(item.source_id)}">${escapeHtml(action.label)}</button>`,
        )
        .join(" ");
      return [
        badge(item.source_type, commandTypeTone(item.source_type)),
        item.source_id,
        badge(item.priority, priorityTone(item.priority)),
        escapeHtml(item.company_name || "-"),
        escapeHtml(item.email || "-"),
        badge(item.status, experimentStatusTone(item.status)),
        escapeHtml(item.origin_label || "-"),
        previewHtml(item.reason || item.title || "-"),
        actions,
      ];
    }),
  );
  $$("[data-command-action]").forEach((button) => {
    button.addEventListener("click", () =>
      runCommandAction(button.dataset.commandSourceType, button.dataset.commandSourceId, button.dataset.commandAction),
    );
  });
}

function renderCommandKanban(columns) {
  const container = $("#commandKanban");
  if (!columns.length) {
    container.innerHTML = `<div class="empty-state">Nenhum lead no pipeline.</div>`;
    return;
  }
  container.innerHTML = columns
    .map((column) => {
      const cards = column.items || [];
      const markup = cards.length
        ? cards
            .map(
              (card) => `
                <article class="kanban-card">
                  <div class="kanban-card-head">
                    <strong title="${escapeHtml(card.company_name)}">${escapeHtml(card.company_name || "-")}</strong>
                    ${badge(card.score || 0, scoreTone(card.score || 0))}
                  </div>
                  <span>${escapeHtml(card.email || "-")}</span>
                  <div class="stat-line compact-line">
                    ${badge(card.status, experimentStatusTone(card.status))}
                    ${card.sequence_name ? badge(card.sequence_name, "purple") : ""}
                  </div>
                  <small>${escapeHtml([card.city, card.state].filter(Boolean).join(" / ") || card.next_action_at || "-")}</small>
                  <button class="row-action" data-lead-replay="${escapeHtml(card.lead_id)}">Replay</button>
                </article>
              `,
            )
            .join("")
        : `<div class="kanban-empty">Vazio</div>`;
      return `
        <section class="kanban-column">
          <header>
            <h3>${escapeHtml(column.label)}</h3>
            <span>${cards.length}</span>
          </header>
          <div class="kanban-list">${markup}</div>
        </section>
      `;
    })
    .join("");
  $$("[data-lead-replay]").forEach((button) => {
    button.addEventListener("click", () => loadLeadTimeline(button.dataset.leadReplay));
  });
}

function renderCommandActivity(items) {
  const container = $("#commandActivity");
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma atividade registrada.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Data", "Acao", "Origem", "Lead", "Empresa", "Motivo"],
    items.map((item) => [
      escapeHtml(item.created_at),
      badge(item.action_type, "purple"),
      escapeHtml(item.origin_label || item.source || "-"),
      escapeHtml(item.lead_email || "-"),
      escapeHtml(item.company_name || "-"),
      previewHtml(item.reason || "-"),
    ]),
  );
}

function renderCommandCenterSnapshot(data) {
  state.commandCenter = data;
  renderCommandMetrics(data.metrics || {});
  renderCommandInbox(data.inbox?.items || []);
  renderCommandKanban(data.kanban?.columns || []);
  renderCommandActivity(data.activity?.items || []);
}

async function runCommandAction(sourceType, sourceId, decision) {
  const note = $("#commandActionNote").value.trim();
  const result = await api("/api/command-center/actions", {
    method: "POST",
    body: JSON.stringify({
      source_type: sourceType,
      source_id: Number(sourceId),
      decision,
      note,
    }),
  });
  if (result.command_center) {
    renderCommandCenterSnapshot(result.command_center);
  } else {
    await loadCommandCenter();
  }
  showStatus(`Decisao ${decision} aplicada em ${sourceType} #${sourceId}.`);
}

function timelineTone(kind) {
  kind = kind || "";
  if (kind.includes("approval")) return "purple";
  if (kind.includes("handoff") || kind.includes("meeting")) return "amber";
  if (kind.includes("conversion") || kind === "reply") return "green";
  if (kind.includes("event")) return "purple";
  return "";
}

function metadataBlock(metadata) {
  const text = JSON.stringify(metadata || {}, null, 2);
  if (!text || text === "{}") return "";
  return `<details class="timeline-meta"><summary>Metadados</summary><pre>${escapeHtml(text)}</pre></details>`;
}

function renderLeadTimeline(data) {
  const container = $("#leadTimelineResult");
  if (!data || !data.lead) {
    container.innerHTML = `<div class="empty-state">Replay nao encontrado.</div>`;
    return;
  }
  const lead = data.lead || {};
  const company = data.company || {};
  const summary = data.summary || {};
  const title = company.trade_name || company.legal_name || lead.email || `Lead ${lead.id}`;
  const subtitle = [company.cnpj, company.city, company.state].filter(Boolean).join(" / ");
  const items = data.timeline || [];
  const timeline = items.length
    ? items
        .map(
          (item) => `
            <article class="timeline-item">
              <div class="timeline-seq">${escapeHtml(item.sequence)}</div>
              <div class="timeline-body">
                <div class="timeline-head">
                  <strong>${escapeHtml(item.title || item.kind)}</strong>
                  <span>${escapeHtml(item.occurred_at || "-")}</span>
                </div>
                <div class="stat-line compact-line">
                  ${badge(item.kind, timelineTone(item.kind || ""))}
                  ${badge(item.origin_label || "-", "")}
                  ${badge(`${item.source_table} #${item.source_id}`, "")}
                </div>
                <p>${escapeHtml(item.detail || "-")}</p>
                ${metadataBlock(item.metadata)}
              </div>
            </article>
          `,
        )
        .join("")
    : `<div class="empty-state">Nenhum evento para este lead.</div>`;
  container.innerHTML = `
    <div class="timeline-summary">
      <div>
        <h3>${escapeHtml(title)}</h3>
        <p class="muted">${escapeHtml(subtitle || lead.email || "-")}</p>
      </div>
      <div class="stat-line compact-line">
        ${badge(`lead ${lead.id}`, "purple")}
        ${badge(lead.status || "-", experimentStatusTone(lead.status || ""))}
        ${badge(`${summary.timeline_items || 0} eventos`)}
        ${badge(`${summary.actions || 0} acoes`)}
        ${badge(`${summary.approvals || 0} aprovacoes`)}
        ${badge(`${summary.handoffs || 0} handoffs`)}
        ${badge(`${summary.meetings || 0} reunioes`)}
      </div>
    </div>
    <div class="timeline-list">${timeline}</div>
  `;
}

async function loadLeadTimeline(leadId) {
  const id = Number(leadId || $("#leadTimelineId").value || 0);
  if (!id) return showStatus("Informe o lead ID para carregar o replay.", "warn");
  const data = await api(`/api/leads/${id}/timeline`);
  state.leadTimeline = data;
  $("#leadTimelineId").value = id;
  renderLeadTimeline(data);
  showStatus(`Replay do lead ${id} carregado.`);
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

function currentCompanyFilters() {
  const values = {
    query: $("#filterQuery").value.trim(),
    state: $("#filterState").value.trim().toUpperCase(),
    city: $("#filterCity").value.trim(),
    cnae: $("#filterCnae").value.trim(),
    sector: $("#filterSector").value.trim(),
    status: $("#filterStatus").value,
    size: $("#filterSize").value,
    min_score: $("#filterMinScore").value,
  };
  const filters = {};
  Object.entries(values).forEach(([key, value]) => {
    if (value) filters[key] = value;
  });
  if ($("#filterHasEmail").checked) filters.has_email = "1";
  if ($("#filterHasPhone").checked) filters.has_phone = "1";
  return filters;
}

function companyFilters() {
  const params = new URLSearchParams();
  Object.entries(currentCompanyFilters()).forEach(([key, value]) => params.set(key, value));
  params.set("limit", "80");
  return params;
}

function describeCompanyFilters(filters = {}) {
  const labels = {
    query: "Busca",
    state: "UF",
    city: "Cidade",
    cnae: "CNAE",
    sector: "Setor",
    status: "Situacao",
    size: "Porte",
    has_email: "Com email",
    has_phone: "Com telefone",
    min_score: "Score min.",
  };
  const parts = Object.entries(filters)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => {
      const label = labels[key] || key;
      if (key === "has_email" || key === "has_phone") return label;
      return `${label}: ${value}`;
    });
  if (!parts.length) return "-";
  return parts.map((part) => badge(part, "purple")).join(" ");
}

function applyCompanyFiltersToForm(filters = {}) {
  $("#filterQuery").value = filters.query || "";
  $("#filterState").value = filters.state || "";
  $("#filterCity").value = filters.city || "";
  $("#filterCnae").value = filters.cnae || "";
  $("#filterSector").value = filters.sector || "";
  $("#filterStatus").value = filters.status || "";
  $("#filterSize").value = filters.size || "";
  $("#filterMinScore").value = filters.min_score || "";
  $("#filterHasEmail").checked = Boolean(filters.has_email);
  $("#filterHasPhone").checked = Boolean(filters.has_phone);
}

async function loadSavedFilters() {
  const data = await api("/api/saved-filters");
  state.savedFilters = data.items || [];
  renderSavedFilters();
  return data;
}

function renderSavedFilters() {
  const select = $("#savedFilterSelect");
  if (select) {
    select.innerHTML = state.savedFilters.length
      ? `<option value="">Selecione um segmento</option>${state.savedFilters
          .map((filter) => `<option value="${filter.id}">${escapeHtml(filter.name)} (${filter.total_at_creation || 0})</option>`)
          .join("")}`
      : `<option value="">Nenhum segmento salvo</option>`;
  }
  const container = $("#savedFiltersTable");
  if (!container) return;
  if (!state.savedFilters.length) {
    container.innerHTML = `<div class="empty-state">Nenhum segmento salvo neste workspace.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Segmento", "Filtros", "Empresas", "Criado", ""],
    state.savedFilters.map((filter) => [
      `<strong>${escapeHtml(filter.name)}</strong>`,
      describeCompanyFilters(filter.filters || {}),
      badge(filter.total_at_creation || 0, "green"),
      escapeHtml(fmt(filter.created_at)),
      `<div class="row-actions"><button class="row-action" data-apply-saved-filter="${filter.id}">Aplicar</button><button class="row-action" data-create-icp-saved-filter="${filter.id}">Criar ICP</button></div>`,
    ]),
  );
  $$("[data-apply-saved-filter]").forEach((button) => {
    button.addEventListener("click", () => applySavedFilterById(button.dataset.applySavedFilter));
  });
  $$("[data-create-icp-saved-filter]").forEach((button) => {
    button.addEventListener("click", () => createIcpFromSavedFilterId(button.dataset.createIcpSavedFilter));
  });
}

async function createSavedFilterFromForm() {
  const name = $("#savedFilterName").value.trim();
  const filters = currentCompanyFilters();
  if (!name) return showStatus("Informe um nome para o segmento.", "warn");
  if (!Object.keys(filters).length) return showStatus("Aplique ao menos um filtro antes de salvar.", "warn");
  const saved = await api("/api/saved-filters", {
    method: "POST",
    body: JSON.stringify({ name, filters }),
  });
  $("#savedFilterName").value = "";
  showStatus(`Segmento "${saved.name}" salvo com ${saved.total_at_creation || 0} empresas.`);
  await loadSavedFilters();
}

async function applySavedFilterById(id) {
  const saved = state.savedFilters.find((item) => String(item.id) === String(id));
  if (!saved) return showStatus("Selecione um segmento salvo.", "warn");
  applyCompanyFiltersToForm(saved.filters || {});
  showStatus(`Segmento "${saved.name}" aplicado.`);
  await loadCompanies();
}

async function applySavedFilterFromSelect() {
  const id = $("#savedFilterSelect").value;
  if (!id) return showStatus("Selecione um segmento salvo.", "warn");
  await applySavedFilterById(id);
}

async function createIcpFromSavedFilterId(id) {
  const saved = state.savedFilters.find((item) => String(item.id) === String(id));
  if (!saved) return showStatus("Selecione um segmento salvo.", "warn");
  const payload = {
    name: $("#savedFilterIcpName").value.trim(),
    max_leads: Number($("#savedFilterIcpMaxLeads").value || 50),
  };
  if (!payload.name) delete payload.name;
  const result = await api(`/api/saved-filters/${id}/icp`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("#savedFilterIcpName").value = "";
  showStatus(`ICP "${result.icp_rule?.name || saved.name}" criado a partir do segmento.`);
}

async function createIcpFromSavedFilterForm() {
  const id = $("#savedFilterSelect").value;
  if (!id) return showStatus("Selecione um segmento salvo.", "warn");
  await createIcpFromSavedFilterId(id);
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

function postgresStagingParams() {
  const params = new URLSearchParams();
  params.set("snapshot", $("#postgresSnapshot").value.trim() || "2026-07");
  const query = $("#postgresQuery").value.trim();
  const stateValue = $("#postgresState").value.trim();
  const city = $("#postgresCity").value.trim();
  const cnae = $("#postgresCnae").value.trim();
  if (query) params.set("query", query);
  if (stateValue) params.set("state", stateValue);
  if (city) params.set("city", city);
  if (cnae) params.set("cnae", cnae);
  if ($("#postgresHasEmail").checked) params.set("has_email", "1");
  params.set("limit", "50");
  return params;
}

async function loadPostgresStaging() {
  const snapshot = $("#postgresSnapshot").value.trim() || "2026-07";
  const summary = await api(`/api/postgres/staging/summary?snapshot=${encodeURIComponent(snapshot)}`);
  state.postgresStagingSummary = summary;
  renderPostgresStagingSummary(summary);
  await searchPostgresStaging();
}

function renderPostgresStagingSummary(summary) {
  const items = summary.items || [];
  $("#postgresStagingMetrics").innerHTML = items
    .map((item) => metric(item.family, Number(item.total || 0).toLocaleString("pt-BR")))
    .join("");
}

async function searchPostgresStaging() {
  const params = postgresStagingParams();
  const data = await api(`/api/postgres/staging/companies?${params.toString()}`);
  state.postgresStagingCompanies = data.items || [];
  $("#postgresStagingStatus").textContent = `${data.count || 0} registro(s) retornado(s) do staging ${data.snapshot || ""}.`;
  renderPostgresStagingCompanies();
}

function renderPostgresStagingCompanies() {
  const items = state.postgresStagingCompanies || [];
  if (!items.length) {
    $("#postgresStagingTable").innerHTML = `<div class="empty-state">Nenhum registro encontrado no Postgres staging para estes filtros.</div>`;
    return;
  }
  $("#postgresStagingTable").innerHTML = table(
    ["Razao social", "CNPJ", "Fantasia", "UF", "Municipio", "CNAE", "Email", "Socios", "Socio amostra"],
    items.map((item) => [
      `<span class="truncate" title="${escapeHtml(item.razao_social)}">${escapeHtml(item.razao_social)}</span>`,
      escapeHtml(fmt(item.cnpj)),
      escapeHtml(fmt(item.nome_fantasia)),
      escapeHtml(fmt(item.uf)),
      escapeHtml(fmt(item.municipio)),
      escapeHtml(fmt(item.cnae_fiscal_principal)),
      item.correio_eletronico ? escapeHtml(item.correio_eletronico) : badge("sem email", "amber"),
      escapeHtml(fmt(item.socios_count)),
      escapeHtml(fmt(item.socio_amostra)),
    ]),
  );
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
  const icpSelect = $("#icpList");
  if (icpSelect) icpSelect.innerHTML = markup;
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

async function loadOfficialCheckpoints() {
  const container = $("#officialCheckpoints");
  if (!container) return;
  const data = await api("/api/sources/official/checkpoints");
  state.officialCheckpoints = data.items || [];
  renderOfficialCheckpoints(state.officialCheckpoints);
}

function officialCheckpointTone(status) {
  if (status === "completed") return "green";
  if (status === "failed") return "red";
  if (status === "running") return "amber";
  return "blue";
}

function renderOfficialCheckpoints(items) {
  const container = $("#officialCheckpoints");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhum checkpoint de importacao oficial.</div>`;
    return;
  }
  container.innerHTML = table(
    ["Snapshot", "Chunk", "Status", "Prox. offset", "Lote", "Importadas", "Erros", "Atualizado", ""],
    items.map((item) => [
      escapeHtml(item.snapshot),
      escapeHtml(item.chunk),
      badge(item.status || "-", officialCheckpointTone(item.status)),
      escapeHtml(item.next_offset || 0),
      escapeHtml(item.limit_per_run || "-"),
      escapeHtml(item.imported_rows || 0),
      escapeHtml(item.error_rows || 0),
      escapeHtml(fmt(item.updated_at)),
      item.status === "completed"
        ? `<span class="muted">concluido</span>`
        : `<button class="row-action" data-official-resume="${escapeHtml(item.id)}">Retomar</button>`,
    ]),
  );
}

async function loadPostgresPlan() {
  const summary = $("#postgresPlanSummary");
  if (!summary) return;
  const snapshot = $("#officialSnapshot").value.trim();
  const suffix = snapshot ? `?snapshot=${encodeURIComponent(snapshot)}` : "";
  summary.textContent = "Montando plano PostgreSQL...";
  try {
    const data = await api(`/api/sources/official/postgres-plan${suffix}`);
    state.officialPostgresPlan = data;
    renderPostgresPlan(data);
  } catch (err) {
    summary.textContent = err.message;
  }
}

function renderPostgresPlan(plan) {
  const summaryNode = $("#postgresPlanSummary");
  const metricsNode = $("#postgresPlanMetrics");
  const commandsNode = $("#postgresPlanCommands");
  const copyNode = $("#postgresCopyPlan");
  const guardrailsNode = $("#postgresPlanGuardrails");
  const ddlNode = $("#postgresPlanDdl");
  if (!summaryNode || !metricsNode || !commandsNode || !copyNode || !guardrailsNode || !ddlNode) return;

  const summary = plan.summary || {};
  const commands = plan.commands || {};
  const diskCapacity = plan.disk_capacity || {};
  summaryNode.innerHTML = plan.snapshot
    ? `Snapshot <strong>${escapeHtml(plan.snapshot)}</strong> / schema <strong>${escapeHtml(plan.schema_name)}</strong>`
    : "Nenhum snapshot com arquivo oficial baixado.";
  const diskTone = diskCapacity.status === "pass" ? "green" : diskCapacity.status === "fail" ? "red" : "amber";
  metricsNode.innerHTML = [
    metric("Arquivos locais", summary.available_files || 0, (summary.available_files || 0) ? "green" : "amber"),
    metric("Conhecidos", summary.recognized_files || 0),
    metric("Indisponiveis", summary.unavailable_files || 0, (summary.unavailable_files || 0) ? "amber" : ""),
    metric("Ausentes", summary.missing_files || 0, (summary.missing_files || 0) ? "amber" : "green"),
    metric("Volume local", bytes(summary.total_available_bytes || 0)),
    metric("Disco livre", diskCapacity.free_bytes == null ? "-" : bytes(diskCapacity.free_bytes), diskTone),
    metric("Disco minimo", diskCapacity.required_bytes == null ? "-" : bytes(diskCapacity.required_bytes), diskTone),
  ].join("");
  const commandButtons = [
    ["preflight_without_docker", "Copiar preflight sem Docker"],
    ["preflight", "Copiar preflight completo"],
    ["smoke_import", "Copiar smoke import"],
    ["snapshot_import", "Copiar importação completa"],
  ].filter(([key]) => commands[key]);
  commandsNode.innerHTML = commandButtons
    .map(
      ([key, label]) =>
        `<button class="button" data-copy-postgres-command="${escapeHtml(key)}">${escapeHtml(label)}</button>`,
    )
    .join("");

  const items = plan.copy_plan || [];
  if (!items.length) {
    copyNode.innerHTML = `<div class="empty-state">Nenhum ZIP local disponivel para COPY neste snapshot.</div>`;
  } else {
    copyNode.innerHTML = table(
      ["Arquivo", "Familia", "Chunk", "Tabela", "CSV detectado", "Tamanho", ""],
      items.map((item, index) => [
        escapeHtml(item.filename),
        escapeHtml(item.family),
        escapeHtml(item.chunk ?? "-"),
        escapeHtml(item.table),
        escapeHtml(item.csv_member || "-"),
        bytes(item.size_bytes),
        `<button class="row-action" data-copy-postgres-plan="${index}">Copiar importação</button>`,
      ]),
    );
  }

  const guardrails = plan.guardrails || [];
  const diskGuardrail =
    diskCapacity.status === "fail"
      ? [
          `Capacidade insuficiente para carga completa: ${bytes(diskCapacity.free_bytes || 0)} livre de ${bytes(
            diskCapacity.required_bytes || 0,
          )} recomendados.`,
        ]
      : [];
  guardrailsNode.innerHTML = guardrails.length || diskGuardrail.length
    ? table(["Guardrail"], [...diskGuardrail, ...guardrails].map((item) => [escapeHtml(item)]))
    : "";
  ddlNode.textContent = plan.ddl_sql || "";
}

async function copyText(text, successMessage) {
  if (!text) return showStatus("Nada para copiar.", "warn");
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
  } else {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  showStatus(successMessage || "Copiado.");
}

async function syncOfficial(modeOverride) {
  const mode = modeOverride || $("#officialMode").value;
  const snapshot = $("#officialSnapshot").value.trim();
  const chunk = Number($("#officialChunk").value || 1);
  const limit = Number($("#officialLimit").value || 1000);
  const offsetRaw = $("#officialOffset").value.trim();
  const resume = $("#officialResume").checked;
  if (!snapshot) return showStatus("Descubra ou informe o snapshot oficial.", "warn");
  if (mode === "full" && !window.confirm("A base completa pode baixar varios GB. Continuar?")) return;
  showStatus("Sincronizacao oficial iniciada. Isso pode demorar conforme o tamanho dos arquivos.");
  const payload = { snapshot, chunk, limit, mode, resume };
  if (offsetRaw) payload.offset = Number(offsetRaw);
  const result = await api("/api/sources/official/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const imported = result.imported ? ` / ${result.imported.imported_rows} empresas importadas` : "";
  const checkpoint = result.checkpoint ? ` / checkpoint ${result.checkpoint.status} no offset ${result.checkpoint.next_offset}` : "";
  showStatus(`${result.downloaded.length} arquivos oficiais processados${imported}${checkpoint}.`);
  $("#officialOffset").value = "";
  await loadOfficialCheckpoints();
  await loadPostgresPlan();
  await loadDashboard();
  await loadCompanies();
}

async function resumeOfficialCheckpoint(checkpointId) {
  const checkpoint = state.officialCheckpoints.find((item) => String(item.id) === String(checkpointId));
  if (!checkpoint) return;
  $("#officialSnapshot").value = checkpoint.snapshot;
  $("#officialChunk").value = checkpoint.chunk;
  $("#officialLimit").value = checkpoint.limit_per_run || $("#officialLimit").value || 1000;
  $("#officialMode").value = "chunk";
  $("#officialResume").checked = true;
  $("#officialOffset").value = "";
  await syncOfficial("chunk");
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

async function loadIcpWorkspace() {
  await loadLists();
  await Promise.all([loadIcpRules(), loadPriorityQueue()]);
}

function commaValues(selector) {
  return $(selector).value
    .split(/,|;|\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function icpPayloadFromForm() {
  return {
    name: $("#icpName").value.trim(),
    description: $("#icpDescription").value.trim(),
    criteria: {
      states: commaValues("#icpStates"),
      cities: commaValues("#icpCities"),
      cnaes: commaValues("#icpCnaes"),
      sectors: commaValues("#icpSectors"),
      sizes: commaValues("#icpSizes"),
      min_opportunity_score: Number($("#icpMinCompanyScore").value || 0),
      min_email_score: Number($("#icpMinEmailScore").value || 30),
      require_email: $("#icpRequireEmail").checked,
      require_corporate_email: $("#icpRequireCorporate").checked,
      exclude_shared_email: $("#icpExcludeShared").checked,
      exclude_suppressed: $("#icpExcludeSuppressed").checked,
      max_leads: Number($("#icpMaxLeads").value || 50),
    },
  };
}

async function createIcpRuleFromForm() {
  const payload = icpPayloadFromForm();
  if (!payload.name) return showStatus("Informe o nome do ICP.", "warn");
  await api("/api/icp-rules", { method: "POST", body: JSON.stringify(payload) });
  $("#icpName").value = "";
  $("#icpDescription").value = "";
  showStatus("ICP estruturado criado.");
  await loadIcpRules();
}

async function loadIcpRules() {
  const data = await api("/api/icp-rules");
  state.icpRules = data.items || [];
  renderIcpRules(state.icpRules);
}

function criteriaSummary(criteria) {
  const parts = [];
  if ((criteria.states || []).length) parts.push(`UF ${criteria.states.join(",")}`);
  if ((criteria.cities || []).length) parts.push(`Cidade ${criteria.cities.join(",")}`);
  if ((criteria.cnaes || []).length) parts.push(`CNAE ${criteria.cnaes.join(",")}`);
  if ((criteria.sectors || []).length) parts.push(`Setor ${criteria.sectors.join(",")}`);
  if ((criteria.sizes || []).length) parts.push(`Porte ${criteria.sizes.join(",")}`);
  if (criteria.min_opportunity_score) parts.push(`Empresa >= ${criteria.min_opportunity_score}`);
  if (criteria.min_email_score) parts.push(`Email >= ${criteria.min_email_score}`);
  if (criteria.require_email) parts.push("com email");
  if (criteria.require_corporate_email) parts.push("corporativo");
  if (criteria.exclude_shared_email) parts.push("sem terceirizado");
  if (criteria.exclude_suppressed) parts.push("sem supressao");
  return parts.join(" / ") || "Sem filtros";
}

function renderIcpRules(items) {
  const container = $("#icpRulesTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhum ICP criado ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "ICP", "Status", "Criterios", "Max", ""],
    items.map((rule) => [
      rule.id,
      `<span class="truncate" title="${escapeHtml(rule.name)}">${escapeHtml(rule.name)}</span>`,
      badge(rule.status, rule.status === "active" ? "green" : "amber"),
      `<span class="truncate" title="${escapeHtml(criteriaSummary(rule.criteria || {}))}">${escapeHtml(criteriaSummary(rule.criteria || {}))}</span>`,
      escapeHtml(fmt((rule.criteria || {}).max_leads)),
      `<button class="row-action" data-prioritize-icp="${rule.id}">Priorizar</button>`,
    ]),
  );
  $$("[data-prioritize-icp]").forEach((button) => {
    button.addEventListener("click", () => prioritizeIcpRule(button.dataset.prioritizeIcp));
  });
}

async function prioritizeIcpRule(ruleId) {
  const listId = Number($("#icpList").value || 0);
  const payload = listId ? { list_id: listId } : {};
  const result = await api(`/api/icp-rules/${ruleId}/prioritize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const summary = result.summary || {};
  showStatus(`${summary.suggested || 0} novas sugestoes / ${summary.updated || 0} atualizadas / ${summary.blocked || 0} bloqueadas.`);
  await Promise.all([loadIcpRules(), loadPriorityQueue()]);
}

async function loadPriorityQueue() {
  const data = await api("/api/priority-queue?limit=200");
  state.priorityQueue = data.items || [];
  renderPriorityQueue(state.priorityQueue);
}

function priorityReason(reason) {
  const matched = (reason?.matched || []).map((item) => `+ ${item}`);
  const blocked = (reason?.blocked || []).map((item) => `- ${item}`);
  const scores = [
    `empresa: ${fmt(reason?.company_score)}`,
    `email: ${fmt(reason?.email_score)}`,
    `fit: ${fmt(reason?.fit_score)}`,
    `prioridade: ${fmt(reason?.priority_score)}`,
  ];
  return [...scores, ...matched, ...blocked].join("\n");
}

function renderPriorityQueue(items) {
  const container = $("#priorityQueueTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma sugestao priorizada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "ICP", "Empresa", "Email", "Cidade/UF", "CNAE", "Status", "Score", "Motivo", ""],
    items.map((item) => [
      item.id,
      escapeHtml(item.icp_name),
      `<span class="truncate" title="${escapeHtml(item.trade_name || item.legal_name)}">${escapeHtml(item.trade_name || item.legal_name)}</span>`,
      escapeHtml(item.lead_email || item.company_email || "-"),
      escapeHtml(`${fmt(item.city)} / ${fmt(item.state)}`),
      escapeHtml(fmt(item.main_cnae_code)),
      badge(item.status, item.status === "suggested" ? "amber" : item.status === "accepted" ? "green" : "red"),
      badge(item.priority_score, scoreTone(item.priority_score || 0)),
      previewHtml(priorityReason(item.reason || {})),
      item.status === "suggested"
        ? `<button class="row-action" data-priority-accept="${item.id}">Aceitar</button> <button class="row-action" data-priority-reject="${item.id}">Rejeitar</button>`
        : "",
    ]),
  );
  $$("[data-priority-accept]").forEach((button) => {
    button.addEventListener("click", () => decidePriorityItem(button.dataset.priorityAccept, "accept"));
  });
  $$("[data-priority-reject]").forEach((button) => {
    button.addEventListener("click", () => decidePriorityItem(button.dataset.priorityReject, "reject"));
  });
}

async function decidePriorityItem(itemId, decision) {
  const note = $("#priorityDecisionNote").value.trim();
  await api(`/api/priority-queue/${itemId}/${decision}`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });
  showStatus(decision === "accept" ? "Sugestao aceita para proxima acao." : "Sugestao rejeitada.");
  await Promise.all([loadPriorityQueue(), loadAgentActions()]);
}

async function loadReplyWorkspace() {
  await Promise.all([loadReplies(), loadHandoffs(), loadMeetings()]);
}

async function classifyReplyFromForm() {
  const payload = {
    send_id: Number($("#replySendId").value || 0) || undefined,
    lead_id: Number($("#replyLeadId").value || 0) || undefined,
    email: $("#replyEmail").value.trim(),
    subject: $("#replySubject").value.trim(),
    body: $("#replyBody").value.trim(),
    source: "manual_ui",
  };
  if (!payload.subject && !payload.body) return showStatus("Informe assunto ou corpo da resposta.", "warn");
  const result = await api("/api/replies/classify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const reply = result.reply || {};
  showStatus(`Resposta classificada como ${reply.classification}.`);
  await Promise.all([loadReplies(), loadHandoffs(), loadMeetings(), loadAgentActions()]);
}

async function loadReplies() {
  const data = await api("/api/replies?limit=200");
  state.replies = data.items || [];
  renderReplies(state.replies);
}

function renderReplies(items) {
  const container = $("#repliesTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma resposta classificada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Data", "Empresa", "Email", "Classe", "Confianca", "Assunto", "Motivos", "Corpo"],
    items.map((item) => [
      item.id,
      escapeHtml(item.created_at),
      escapeHtml(item.trade_name || item.legal_name || "-"),
      escapeHtml(item.email || item.lead_email || "-"),
      badge(item.classification, replyTone(item.classification)),
      badge(Math.round((Number(item.confidence) || 0) * 100), scoreTone(Math.round((Number(item.confidence) || 0) * 100))),
      escapeHtml(fmt(item.subject)),
      escapeHtml((item.reasons || []).join("; ") || "-"),
      previewHtml(item.body_text || "-"),
    ]),
  );
}

function replyTone(classification) {
  if (classification === "interest_meeting") return "green";
  if (classification === "opt_out" || classification === "not_interested") return "red";
  if (classification === "ambiguous") return "amber";
  return "purple";
}

async function loadHandoffs() {
  const data = await api("/api/handoffs?status=pending&limit=200");
  state.handoffs = data.items || [];
  renderHandoffs(state.handoffs);
}

function renderHandoffs(items) {
  const container = $("#handoffsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhum handoff pendente.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Prioridade", "Empresa", "Email", "Motivo", "Classe", "Contexto", ""],
    items.map((item) => {
      const context = item.context || {};
      return [
        item.id,
        badge(item.priority, item.priority === "urgent" ? "red" : item.priority === "high" ? "amber" : "purple"),
        escapeHtml(item.trade_name || item.legal_name || "-"),
        escapeHtml(item.lead_email || context.email || "-"),
        escapeHtml(item.reason),
        badge(context.classification || "-", replyTone(context.classification)),
        previewHtml(context.body_preview || "-"),
        `<button class="row-action" data-handoff-meeting="${item.id}" data-handoff-lead="${item.lead_id || ""}">Reuniao</button> <button class="row-action" data-handoff-resolve="${item.id}">Resolver</button> <button class="row-action" data-handoff-dismiss="${item.id}">Dispensar</button>`,
      ];
    }),
  );
  $$("[data-handoff-meeting]").forEach((button) => {
    button.addEventListener("click", () => fillMeetingFromHandoff(button.dataset.handoffMeeting, button.dataset.handoffLead));
  });
  $$("[data-handoff-resolve]").forEach((button) => {
    button.addEventListener("click", () => decideHandoff(button.dataset.handoffResolve, "resolve"));
  });
  $$("[data-handoff-dismiss]").forEach((button) => {
    button.addEventListener("click", () => decideHandoff(button.dataset.handoffDismiss, "dismiss"));
  });
}

function fillMeetingFromHandoff(handoffId, leadId) {
  $("#meetingHandoffId").value = handoffId || "";
  $("#meetingLeadId").value = leadId || "";
  $("#meetingNotes").focus();
  showStatus(`Handoff ${handoffId} pronto para registrar reuniao.`);
}

async function decideHandoff(handoffId, decision) {
  const note = $("#handoffDecisionNote").value.trim();
  await api(`/api/handoffs/${handoffId}/${decision}`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });
  showStatus(decision === "resolve" ? "Handoff resolvido." : "Handoff dispensado.");
  await Promise.all([loadHandoffs(), loadAgentActions()]);
}

function meetingPayloadFromForm() {
  return {
    lead_id: Number($("#meetingLeadId").value || 0) || undefined,
    scheduled_at: $("#meetingScheduledAt").value.trim(),
    duration_minutes: Number($("#meetingDuration").value || 30),
    meeting_url: $("#meetingUrl").value.trim(),
    owner_name: $("#meetingOwner").value.trim(),
    notes: $("#meetingNotes").value.trim(),
  };
}

async function createMeetingFromHandoffForm() {
  const handoffId = Number($("#meetingHandoffId").value || 0);
  if (!handoffId) return showStatus("Informe o ID do handoff.", "warn");
  const meeting = await api(`/api/handoffs/${handoffId}/meeting`, {
    method: "POST",
    body: JSON.stringify(meetingPayloadFromForm()),
  });
  $("#meetingStatusId").value = meeting.id;
  showStatus(`Reuniao ${meeting.id} registrada e handoff resolvido.`);
  await Promise.all([loadHandoffs(), loadMeetings(), loadAgentActions()]);
}

async function createMeetingManualForm() {
  const payload = meetingPayloadFromForm();
  if (!payload.lead_id) return showStatus("Informe o ID do lead.", "warn");
  const meeting = await api("/api/meetings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("#meetingStatusId").value = meeting.id;
  showStatus(`Reuniao ${meeting.id} registrada.`);
  await Promise.all([loadMeetings(), loadAgentActions()]);
}

async function loadMeetings() {
  const data = await api("/api/meetings?limit=200");
  state.meetings = data.items || [];
  renderMeetings(state.meetings);
}

function meetingTone(status) {
  if (status === "completed") return "green";
  if (status === "cancelled" || status === "no_show") return "red";
  if (status === "scheduled") return "amber";
  return "purple";
}

function renderMeetings(items) {
  const container = $("#meetingsTable");
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Nenhuma reuniao registrada ainda.</div>`;
    return;
  }
  container.innerHTML = table(
    ["ID", "Status", "Quando", "Empresa", "Email", "Origem", "Link", "Nota", ""],
    items.map((item) => [
      item.id,
      badge(item.status, meetingTone(item.status)),
      escapeHtml(fmt(item.scheduled_at)),
      escapeHtml(item.trade_name || item.legal_name || "-"),
      escapeHtml(item.attendee_email || item.lead_email || "-"),
      escapeHtml(item.source || "-"),
      item.meeting_url ? `<a href="${escapeHtml(item.meeting_url)}" target="_blank" rel="noreferrer">Abrir</a>` : "-",
      previewHtml(item.outcome_note || item.notes || "-"),
      `<button class="row-action" data-meeting-fill="${item.id}" data-meeting-status="${item.status}">Status</button> <button class="row-action" data-meeting-complete="${item.id}">Concluir</button> <button class="row-action" data-meeting-cancel="${item.id}">Cancelar</button>`,
    ]),
  );
  $$("[data-meeting-fill]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#meetingStatusId").value = button.dataset.meetingFill;
      $("#meetingStatus").value = button.dataset.meetingStatus || "scheduled";
      $("#meetingStatusNote").focus();
    });
  });
  $$("[data-meeting-complete]").forEach((button) => {
    button.addEventListener("click", () => updateMeetingStatus(button.dataset.meetingComplete, "completed"));
  });
  $$("[data-meeting-cancel]").forEach((button) => {
    button.addEventListener("click", () => updateMeetingStatus(button.dataset.meetingCancel, "cancelled"));
  });
}

async function updateMeetingStatus(meetingId, status) {
  const note = $("#meetingStatusNote").value.trim();
  await api(`/api/meetings/${meetingId}/status`, {
    method: "POST",
    body: JSON.stringify({ status, note }),
  });
  showStatus(`Reuniao ${meetingId} atualizada para ${status}.`);
  await Promise.all([loadMeetings(), loadAgentActions()]);
}

async function updateMeetingStatusFromForm() {
  const meetingId = Number($("#meetingStatusId").value || 0);
  if (!meetingId) return showStatus("Informe o ID da reuniao.", "warn");
  await updateMeetingStatus(meetingId, $("#meetingStatus").value);
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

function prettyJson(value) {
  return JSON.stringify(value || {}, null, 2);
}

function parseJsonField(selector, label) {
  const raw = $(selector).value.trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (err) {
    throw new Error(`${label} precisa ser JSON valido.`);
  }
}

async function loadScoringConfig() {
  const config = await api("/api/scoring/config");
  state.scoringConfig = config;
  renderScoringConfig(config);
}

function renderScoringConfig(config) {
  if (!config) return;
  $("#scoringConfigName").value = config.name || "";
  $("#scoringPrefixRulesJson").value = prettyJson(config.email_prefix_rules || {});
  $("#scoringThresholdsJson").value = prettyJson(config.thresholds || {});
  $("#scoringConfigSummary").textContent = `${config.prefix_count || 0} prefixos / atualizado em ${fmt(config.updated_at)}`;
  const rules = Object.entries(config.email_prefix_rules || {})
    .map(([prefix, rule]) => ({ prefix, ...(rule || {}) }))
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
    .slice(0, 12);
  $("#scoringConfigTable").innerHTML = rules.length
    ? table(
        ["Prefixo", "Area", "Score", "Label"],
        rules.map((rule) => [
          badge(rule.prefix, "purple"),
          escapeHtml(rule.area || "-"),
          badge(rule.score || 0, scoreTone(Number(rule.score || 0))),
          escapeHtml(rule.label || "-"),
        ]),
      )
    : `<div class="empty-state">Nenhum prefixo configurado.</div>`;
}

async function saveScoringConfigFromForm() {
  try {
    const payload = {
      name: $("#scoringConfigName").value.trim(),
      email_prefix_rules: parseJsonField("#scoringPrefixRulesJson", "Prefixos"),
      thresholds: parseJsonField("#scoringThresholdsJson", "Thresholds"),
    };
    const config = await api("/api/scoring/config", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.scoringConfig = config;
    renderScoringConfig(config);
    await loadScoreConfigVersions();
    showStatus("Config de scoring salva.");
  } catch (err) {
    showStatus(err.message, "warn");
  }
}

async function loadCompanyScoringConfig() {
  const config = await api("/api/scoring/company-config");
  state.companyScoringConfig = config;
  renderCompanyScoringConfig(config);
}

function renderCompanyScoringConfig(config) {
  if (!config) return;
  const rules = config.rules || {};
  $("#companyScoringConfigName").value = config.name || "";
  $("#companyScoringRulesJson").value = prettyJson(rules);
  $("#companyScoringConfigSummary").textContent = `${config.sector_count || 0} setores / ${config.capital_band_count || 0} faixas / atualizado em ${fmt(config.updated_at)}`;
  const sectorRows = Object.entries(rules.sector_bonus || {})
    .map(([sector, bonus]) => ({ sector, bonus }))
    .sort((a, b) => Number(b.bonus || 0) - Number(a.bonus || 0));
  const contactRows = [
    { signal: "email", bonus: rules.contact?.email_bonus || 0 },
    { signal: "telefone", bonus: rules.contact?.phone_bonus || 0 },
    { signal: "base", bonus: rules.base_score || 0 },
  ];
  $("#companyScoringConfigTable").innerHTML = table(
    ["Sinal", "Peso"],
    [
      ...contactRows.map((row) => [escapeHtml(row.signal), badge(row.bonus, scoreTone(Number(row.bonus || 0)))]),
      ...sectorRows.slice(0, 10).map((row) => [escapeHtml(row.sector), badge(row.bonus, scoreTone(Number(row.bonus || 0)))]),
    ],
  );
}

async function saveCompanyScoringConfigFromForm() {
  try {
    const payload = {
      name: $("#companyScoringConfigName").value.trim(),
      rules: parseJsonField("#companyScoringRulesJson", "Regras de empresa"),
    };
    const config = await api("/api/scoring/company-config", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.companyScoringConfig = config;
    renderCompanyScoringConfig(config);
    await loadScoreConfigVersions();
    showStatus("Config de score de empresa salva.");
  } catch (err) {
    showStatus(err.message, "warn");
  }
}

async function rescoreCompaniesFromForm() {
  try {
    const limit = Number($("#companyRescoreLimit").value || 500);
    const result = await api("/api/scoring/company-rescore", {
      method: "POST",
      body: JSON.stringify({ limit }),
    });
    $("#companyRescoreSummary").textContent = `${result.scored || 0} empresas recalculadas com ${result.scoring_config?.name || "config ativa"}.`;
    showStatus("Score de empresas recalculado.");
    if (state.view === "companies") await loadCompanies();
  } catch (err) {
    showStatus(err.message, "warn");
  }
}

function scoreConfigTypeLabel(type) {
  if (type === "email") return "Email";
  if (type === "company") return "Empresa";
  return type || "-";
}

function scoreVersionSummary(item) {
  if (item.config_type === "email") {
    return `${item.prefix_count || 0} prefixos / ${item.threshold_count || 0} thresholds`;
  }
  if (item.config_type === "company") {
    return `${item.sector_count || 0} setores / ${item.capital_band_count || 0} faixas`;
  }
  return "-";
}

function scoreConfigChangeTone(changeType) {
  if (changeType === "added") return "green";
  if (changeType === "removed") return "red";
  if (changeType === "changed") return "amber";
  return "blue";
}

function scoreConfigChangeLabel(changeType) {
  if (changeType === "added") return "Adicionado";
  if (changeType === "removed") return "Removido";
  if (changeType === "changed") return "Alterado";
  if (changeType === "unchanged") return "Igual";
  return changeType || "-";
}

function formatDiffValue(value, exists) {
  if (!exists) return `<span class="muted">ausente</span>`;
  let text;
  if (value === null) {
    text = "null";
  } else if (typeof value === "object") {
    text = JSON.stringify(value);
  } else {
    text = String(value);
  }
  if (text.length > 180) text = `${text.slice(0, 177)}...`;
  return `<code class="json-chip">${escapeHtml(text)}</code>`;
}

async function loadScoreConfigVersions() {
  const selector = $("#scoreVersionType");
  const type = selector ? selector.value : "all";
  const suffix = type && type !== "all" ? `?type=${encodeURIComponent(type)}` : "";
  const data = await api(`/api/scoring/config-versions${suffix}`);
  state.scoreConfigVersions = data.items || [];
  state.scoreConfigDiff = null;
  renderScoreConfigVersions(state.scoreConfigVersions);
  renderScoreConfigDiff(null);
}

function renderScoreConfigVersions(items) {
  $("#scoreVersionsSummary").textContent = `${items.length || 0} versoes registradas`;
  if (!items.length) {
    $("#scoreConfigVersionsTable").innerHTML = `<div class="empty-state">Nenhuma versao registrada.</div>`;
    return;
  }
  $("#scoreConfigVersionsTable").innerHTML = table(
    ["Tipo", "Versao", "Status", "Nome", "Resumo", "Nota", "Ativada", "Acao"],
    items.map((item) => [
      badge(scoreConfigTypeLabel(item.config_type), item.config_type === "company" ? "purple" : "blue"),
      `v${escapeHtml(item.version_number || "-")}`,
      badge(item.status || "-", item.status === "active" ? "green" : "amber"),
      escapeHtml(item.name || "-"),
      escapeHtml(scoreVersionSummary(item)),
      escapeHtml(item.change_note || "-"),
      escapeHtml(fmt(item.activated_at || item.created_at)),
      `<span class="inline-actions">
        <button class="row-action" data-score-version-diff="${escapeHtml(item.id)}">Diff</button>
        ${
          item.status === "active"
            ? `<span class="muted">ativa</span>`
            : `<button class="row-action" data-score-version-rollback="${escapeHtml(item.id)}">Restaurar</button>`
        }
      </span>`,
    ]),
  );
}

function renderScoreConfigDiff(diff) {
  const panel = $("#scoreConfigDiffPanel");
  if (!panel) return;
  if (!diff) {
    panel.innerHTML = `<div class="empty-state">Selecione Diff em uma versao para revisar o impacto antes de restaurar.</div>`;
    return;
  }
  const summary = diff.summary || {};
  const version = diff.version || {};
  const active = diff.active_version || {};
  const changedRows = (diff.changes || []).filter((item) => item.change_type !== "unchanged");
  const visibleRows = changedRows.slice(0, 80);
  panel.innerHTML = `
    <div class="diff-summary">
      <div>
        <strong>${escapeHtml(scoreConfigTypeLabel(diff.config_type))}: v${escapeHtml(active.version_number || "-")} ativo -> v${escapeHtml(version.version_number || "-")}</strong>
        <div class="muted">Antes e a configuracao ativa agora; depois e o snapshot escolhido.</div>
      </div>
      <div class="inline-actions">
        ${badge(summary.changed || 0, "amber")} <span class="muted">alterados</span>
        ${badge(summary.added || 0, "green")} <span class="muted">adicionados</span>
        ${badge(summary.removed || 0, "red")} <span class="muted">removidos</span>
      </div>
    </div>
    ${
      changedRows.length
        ? table(
            ["Campo", "Tipo", "Antes", "Depois"],
            visibleRows.map((item) => [
              `<code>${escapeHtml(item.path)}</code>`,
              badge(scoreConfigChangeLabel(item.change_type), scoreConfigChangeTone(item.change_type)),
              formatDiffValue(item.before, item.before_exists),
              formatDiffValue(item.after, item.after_exists),
            ]),
          )
        : `<div class="empty-state">Nenhuma mudanca entre a versao ativa e esta versao.</div>`
    }
    ${changedRows.length > visibleRows.length ? `<div class="muted">Mostrando 80 de ${changedRows.length} campos alterados.</div>` : ""}
  `;
}

async function loadScoreConfigVersionDiff(versionId, options = {}) {
  const diff = await api(`/api/scoring/config-versions/${versionId}/diff`);
  state.scoreConfigDiff = diff;
  renderScoreConfigDiff(diff);
  if (!options.silent) {
    const count = diff.summary?.change_count || 0;
    showStatus(count ? `Diff carregado com ${count} campos alterados.` : "Diff carregado sem mudancas.");
  }
  return diff;
}

async function rollbackScoreConfigVersion(versionId) {
  const version = state.scoreConfigVersions.find((item) => String(item.id) === String(versionId));
  const label = version ? `${scoreConfigTypeLabel(version.config_type)} v${version.version_number}` : "esta versao";
  const diff =
    state.scoreConfigDiff && String(state.scoreConfigDiff.version?.id) === String(versionId)
      ? state.scoreConfigDiff
      : await loadScoreConfigVersionDiff(versionId, { silent: true });
  const count = diff.summary?.change_count || 0;
  if (!window.confirm(`Restaurar ${label}? ${count} campos mudarao.`)) return;
  const result = await api(`/api/scoring/config-versions/${versionId}/rollback`, {
    method: "POST",
    body: JSON.stringify({ change_note: `Rollback via UI para ${label}` }),
  });
  await Promise.all([loadScoringConfig(), loadCompanyScoringConfig(), loadScoreConfigVersions()]);
  if (result.config_type === "company") {
    $("#companyRescoreSummary").textContent = "Config restaurada. Recalcule empresas para atualizar o overlay.";
  }
  showStatus("Versao de scoring restaurada.");
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
  $("#setWorkspaceContextBtn").addEventListener("click", setWorkspaceContextFromForm);
  $("#workspaceContextSelect").addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#setWorkspaceContextBtn").click();
  });
  $("#saveCurrentFilterBtn").addEventListener("click", createSavedFilterFromForm);
  $("#refreshSavedFiltersBtn").addEventListener("click", loadSavedFilters);
  $("#applySavedFilterBtn").addEventListener("click", applySavedFilterFromSelect);
  $("#createIcpFromSavedFilterBtn").addEventListener("click", createIcpFromSavedFilterForm);
  $("#addToListBtn").addEventListener("click", addSelectedToList);
  $("#refreshPostgresStagingBtn").addEventListener("click", loadPostgresStaging);
  $("#searchPostgresStagingBtn").addEventListener("click", searchPostgresStaging);
  ["postgresQuery", "postgresState", "postgresCity", "postgresCnae"].forEach((id) => {
    $(`#${id}`).addEventListener("keydown", (event) => {
      if (event.key === "Enter") searchPostgresStaging();
    });
  });
  $("#createListBtn").addEventListener("click", createListFromForm);
  $("#importBtn").addEventListener("click", importFromForm);
  $("#discoverOfficialBtn").addEventListener("click", loadOfficialCatalog);
  $("#syncOfficialBtn").addEventListener("click", () => syncOfficial());
  $("#downloadDomainsBtn").addEventListener("click", () => syncOfficial("domains"));
  $("#refreshOfficialCheckpointsBtn").addEventListener("click", loadOfficialCheckpoints);
  $("#loadPostgresPlanBtn").addEventListener("click", loadPostgresPlan);
  $("#copyPostgresDdlBtn").addEventListener("click", () =>
    copyText((state.officialPostgresPlan || {}).ddl_sql || "", "DDL PostgreSQL copiado."),
  );
  $("#postgresCopyPlan").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-postgres-plan]");
    if (!button || !state.officialPostgresPlan) return;
    const item = (state.officialPostgresPlan.copy_plan || [])[Number(button.dataset.copyPostgresPlan)];
    if (!item) return;
    const fallback = [item.extract_command, item.copy_sql].filter(Boolean).join("\n\n");
    await copyText(item.import_command || fallback, "Comando de importação copiado.");
  });
  $("#postgresPlanCommands").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-postgres-command]");
    if (!button || !state.officialPostgresPlan) return;
    const command = (state.officialPostgresPlan.commands || {})[button.dataset.copyPostgresCommand];
    await copyText(command || "", "Comando PostgreSQL copiado.");
  });
  $("#officialCheckpoints").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-official-resume]");
    if (!button) return;
    await resumeOfficialCheckpoint(button.dataset.officialResume);
  });
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
  $("#refreshCommandBtn").addEventListener("click", loadCommandCenter);
  $("#generateNotificationsBtn").addEventListener("click", generateNotificationsFromSignals);
  $("#refreshNotificationsBtn").addEventListener("click", loadNotifications);
  $("#refreshWorkspaceComparisonBtn").addEventListener("click", loadWorkspaceComparison);
  $("#refreshSaasAccountBtn").addEventListener("click", loadSaasAccount);
  $("#createSaasApiKeyBtn").addEventListener("click", createSaasApiKeyFromForm);
  $("#adjustSaasCreditsBtn").addEventListener("click", adjustSaasCreditsFromForm);
  $("#applySaasPlanBtn").addEventListener("click", applySaasPlanFromForm);
  $("#runWorkspaceOnboardingBtn").addEventListener("click", runWorkspaceOnboardingFromForm);
  $("#createWorkspaceBtn").addEventListener("click", createWorkspaceFromForm);
  $("#createWorkspaceSnapshotBtn").addEventListener("click", createWorkspaceSnapshotFromForm);
  $("#refreshOkrsBtn").addEventListener("click", loadOkrs);
  $("#refreshPlaybooksBtn").addEventListener("click", loadPlaybooks);
  $("#playbookSelect").addEventListener("change", () => {
    const playbook = selectedPlaybook();
    syncPlaybookVersionForm(playbook);
    renderSelectedPlaybookVersions(playbook);
  });
  $("#createPlaybookBtn").addEventListener("click", createPlaybookFromForm);
  $("#createPlaybookVersionBtn").addEventListener("click", createPlaybookVersionFromForm);
  $("#applyPlaybookBtn").addEventListener("click", () => applyPlaybookFromForm());
  $("#createPlaybookExecutionPlanBtn").addEventListener("click", createPlaybookExecutionPlanFromForm);
  $("#clonePlaybookBtn").addEventListener("click", clonePlaybookFromForm);
  $("#refreshAgentGovernanceBtn").addEventListener("click", loadAgentGovernance);
  $("#createAgentConfigBtn").addEventListener("click", createAgentConfigFromForm);
  $("#createAgentSimulationBtn").addEventListener("click", createAgentSimulationFromForm);
  $("#recordAgentCostBtn").addEventListener("click", recordAgentCostFromForm);
  $("#loadLeadTimelineBtn").addEventListener("click", () => loadLeadTimeline());
  $("#createIcpBtn").addEventListener("click", createIcpRuleFromForm);
  $("#refreshIcpBtn").addEventListener("click", loadIcpWorkspace);
  $("#refreshPriorityBtn").addEventListener("click", loadPriorityQueue);
  $("#classifyReplyBtn").addEventListener("click", classifyReplyFromForm);
  $("#refreshRepliesBtn").addEventListener("click", loadReplyWorkspace);
  $("#refreshHandoffsBtn").addEventListener("click", loadHandoffs);
  $("#refreshMeetingsBtn").addEventListener("click", loadMeetings);
  $("#createMeetingFromHandoffBtn").addEventListener("click", createMeetingFromHandoffForm);
  $("#createMeetingManualBtn").addEventListener("click", createMeetingManualForm);
  $("#updateMeetingStatusBtn").addEventListener("click", updateMeetingStatusFromForm);
  $("#seedBtn").addEventListener("click", seed);
  $("#seedBtnImport").addEventListener("click", seed);
  $("#validateEmailsBtn").addEventListener("click", validateFreeEmails);
  $("#scoreEmailsBtn").addEventListener("click", scoreFreeEmails);
  $("#refreshScoringConfigBtn").addEventListener("click", loadScoringConfig);
  $("#saveScoringConfigBtn").addEventListener("click", saveScoringConfigFromForm);
  $("#refreshCompanyScoringConfigBtn").addEventListener("click", loadCompanyScoringConfig);
  $("#saveCompanyScoringConfigBtn").addEventListener("click", saveCompanyScoringConfigFromForm);
  $("#rescoreCompaniesBtn").addEventListener("click", rescoreCompaniesFromForm);
  $("#refreshScoreVersionsBtn").addEventListener("click", loadScoreConfigVersions);
  $("#scoreVersionType").addEventListener("change", loadScoreConfigVersions);
  $("#scoreConfigVersionsTable").addEventListener("click", async (event) => {
    const diffButton = event.target.closest("[data-score-version-diff]");
    if (diffButton) {
      await loadScoreConfigVersionDiff(diffButton.dataset.scoreVersionDiff);
      return;
    }
    const rollbackButton = event.target.closest("[data-score-version-rollback]");
    if (!rollbackButton) return;
    await rollbackScoreConfigVersion(rollbackButton.dataset.scoreVersionRollback);
  });
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
  await loadWorkspaceContext();
  await loadDashboard();
  await loadLists();
  await loadCompanies();
}

start().catch((err) => showStatus(err.message, "warn"));
