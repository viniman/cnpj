import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .database import connect, init_db
from .services import (
    add_companies_to_list,
    add_suppression,
    activate_agent_config,
    adjust_credit_wallet,
    agent_governance,
    apply_playbook,
    apply_playbook_execution_plan,
    approve_sequence_step,
    audit_events,
    create_icp_rule,
    create_agent_config,
    create_agent_simulation,
    create_api_key,
    create_list,
    create_campaign,
    create_email_template,
    create_email_template_version,
    create_leads_from_list,
    create_meeting,
    create_meeting_from_handoff,
    clone_playbook_to_workspace,
    create_playbook,
    create_playbook_execution_plan,
    create_playbook_version,
    create_sequence,
    create_workspace,
    create_workspace_snapshot,
    command_center_action,
    command_center,
    dashboard,
    decide_handoff,
    decide_priority_queue_item,
    enrich_company,
    enroll_sequence_from_list,
    export_list,
    get_campaign,
    get_company,
    get_company_enrichment,
    get_email_template,
    get_icp_rule,
    get_list,
    lead_timeline,
    get_sequence,
    import_source,
    create_okr,
    generate_notifications,
    record_agent_cost,
    list_agent_actions,
    list_approvals,
    list_campaigns,
    list_email_templates,
    list_experiment_leads,
    list_handoffs,
    list_icp_rules,
    list_journeys,
    list_lists,
    list_meetings,
    list_notifications,
    list_playbook_execution_plans,
    okr_dashboard,
    playbook_library,
    list_priority_queue,
    list_reply_classifications,
    list_sequences,
    prepare_next_journey_step,
    prioritize_icp_rule,
    remove_company_from_list,
    record_campaign_event,
    record_inbound_reply,
    reject_sequence_step,
    render_email_template,
    revoke_api_key,
    run_workspace_onboarding,
    saas_account,
    score_emails,
    search_companies,
    seed_sample,
    simulate_campaign,
    update_meeting_status,
    update_notification_status,
    validate_emails,
    set_current_workspace,
    workspace_context,
    workspace_comparison,
)
from .official_sources import catalog, download_files, import_brasilapi_cnpj, list_snapshot_files, sync_official_snapshot


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "static")


class RadarHandler(SimpleHTTPRequestHandler):
    server_version = "RadarCNPJ/0.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed)
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_post(parsed)
            return
        self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_delete(parsed)
            return
        self.send_error(404)

    def log_message(self, fmt, *args):
        return

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_commit(self, conn, payload, status=200):
        conn.commit()
        self.send_json(payload, status=status)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status=status)

    def serve_static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        safe = os.path.normpath(unquote(path).lstrip("/"))
        file_path = os.path.abspath(os.path.join(STATIC_DIR, safe))
        if not file_path.startswith(STATIC_DIR) or not os.path.isfile(file_path):
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def query_params(self, parsed):
        values = parse_qs(parsed.query)
        return dict((key, value[-1]) for key, value in values.items())

    def handle_api_get(self, parsed):
        parts = [part for part in parsed.path.split("/") if part]
        params = self.query_params(parsed)
        try:
            with connect() as conn:
                if parsed.path == "/api/health":
                    self.send_json({"ok": True, "name": "Radar CNPJ Interno"})
                elif parsed.path == "/api/dashboard":
                    self.send_json(dashboard(conn))
                elif parsed.path == "/api/command-center":
                    self.send_json(command_center(conn))
                elif parsed.path == "/api/agent-governance":
                    self.send_json(agent_governance(conn))
                elif parsed.path == "/api/playbooks":
                    self.send_json(playbook_library(conn))
                elif parsed.path == "/api/playbook-execution-plans":
                    self.send_json(list_playbook_execution_plans(conn, params))
                elif parsed.path == "/api/saas/account":
                    self.send_json(saas_account(conn, params))
                elif parsed.path == "/api/notifications":
                    self.send_json(list_notifications(conn, params))
                elif parsed.path == "/api/workspace-context":
                    self.send_json(workspace_context(conn))
                elif parsed.path == "/api/workspaces/comparison":
                    self.send_json(workspace_comparison(conn))
                elif parsed.path == "/api/okrs":
                    self.send_json(okr_dashboard(conn))
                elif parsed.path == "/api/companies":
                    self.send_json(search_companies(conn, params))
                elif len(parts) == 3 and parts[1] == "companies":
                    company = get_company(conn, int(parts[2]))
                    if not company:
                        self.send_error_json("Empresa nao encontrada", 404)
                    else:
                        self.send_json(company)
                elif len(parts) == 4 and parts[1] == "leads" and parts[3] == "timeline":
                    timeline = lead_timeline(conn, int(parts[2]))
                    if not timeline:
                        self.send_error_json("Lead nao encontrado", 404)
                    else:
                        self.send_json(timeline)
                elif len(parts) == 4 and parts[1] == "enrichment" and parts[2] == "company":
                    enrichment = get_company_enrichment(conn, int(parts[3]))
                    if not enrichment:
                        self.send_error_json("Enriquecimento nao encontrado", 404)
                    else:
                        self.send_json(enrichment)
                elif parsed.path == "/api/lists":
                    self.send_json({"items": list_lists(conn)})
                elif len(parts) == 3 and parts[1] == "lists":
                    item = get_list(conn, int(parts[2]))
                    if not item:
                        self.send_error_json("Lista nao encontrada", 404)
                    else:
                        self.send_json(item)
                elif len(parts) == 4 and parts[1] == "lists" and parts[3] == "export":
                    data, content_type = export_list(
                        conn,
                        int(parts[2]),
                        params.get("format", "csv"),
                        params.get("purpose", ""),
                    )
                    conn.commit()
                    extension = "xlsx" if params.get("format") == "xlsx" else "csv"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Disposition", 'attachment; filename="radar-cnpj-lista.%s"' % extension)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                elif parsed.path == "/api/audit":
                    self.send_json({"items": audit_events(conn, params.get("limit", 100))})
                elif parsed.path == "/api/experiments/leads":
                    self.send_json(list_experiment_leads(conn, params))
                elif parsed.path == "/api/experiments/campaigns":
                    self.send_json(list_campaigns(conn))
                elif len(parts) == 4 and parts[1] == "experiments" and parts[2] == "campaigns":
                    campaign = get_campaign(conn, int(parts[3]))
                    if not campaign:
                        self.send_error_json("Campanha nao encontrada", 404)
                    else:
                        self.send_json(campaign)
                elif parsed.path == "/api/templates":
                    self.send_json(list_email_templates(conn))
                elif len(parts) == 3 and parts[1] == "templates":
                    template = get_email_template(conn, int(parts[2]))
                    if not template:
                        self.send_error_json("Template nao encontrado", 404)
                    else:
                        self.send_json(template)
                elif parsed.path == "/api/sequences":
                    self.send_json(list_sequences(conn))
                elif parsed.path == "/api/sequences/journeys":
                    self.send_json(list_journeys(conn, params))
                elif len(parts) == 3 and parts[1] == "sequences":
                    sequence = get_sequence(conn, int(parts[2]))
                    if not sequence:
                        self.send_error_json("Sequencia nao encontrada", 404)
                    else:
                        self.send_json(sequence)
                elif parsed.path == "/api/approvals":
                    self.send_json(list_approvals(conn, params))
                elif parsed.path == "/api/agent-actions":
                    self.send_json(list_agent_actions(conn, params))
                elif parsed.path == "/api/icp-rules":
                    self.send_json(list_icp_rules(conn, params))
                elif len(parts) == 3 and parts[1] == "icp-rules":
                    rule = get_icp_rule(conn, int(parts[2]))
                    if not rule:
                        self.send_error_json("ICP nao encontrado", 404)
                    else:
                        self.send_json(rule)
                elif parsed.path == "/api/priority-queue":
                    self.send_json(list_priority_queue(conn, params))
                elif parsed.path == "/api/replies":
                    self.send_json(list_reply_classifications(conn, params))
                elif parsed.path == "/api/handoffs":
                    self.send_json(list_handoffs(conn, params))
                elif parsed.path == "/api/meetings":
                    self.send_json(list_meetings(conn, params))
                elif parsed.path == "/api/sources/official":
                    self.send_json(catalog())
                elif len(parts) == 5 and parts[1] == "sources" and parts[2] == "official" and parts[3] == "snapshots":
                    self.send_json({"items": list_snapshot_files(parts[4])})
                else:
                    self.send_error_json("Endpoint nao encontrado", 404)
        except Exception as exc:
            self.send_error_json(str(exc), 500)

    def handle_api_post(self, parsed):
        parts = [part for part in parsed.path.split("/") if part]
        try:
            data = self.read_json()
            with connect() as conn:
                if parsed.path == "/api/seed":
                    result = seed_sample(conn)
                    self.send_json_commit(conn, result)
                elif parsed.path == "/api/import":
                    result = import_source(
                        conn,
                        data.get("path", ""),
                        data.get("source_name") or "Importacao local",
                        data.get("source_url") or "",
                        data.get("legal_basis") or "Legitimo interesse B2B",
                        data.get("limit") or 1000,
                    )
                    self.send_json_commit(conn, result)
                elif parsed.path == "/api/lists":
                    name = (data.get("name") or "").strip()
                    if not name:
                        self.send_error_json("Nome da lista e obrigatorio")
                    else:
                        self.send_json_commit(conn, create_list(conn, name, data.get("description") or ""), 201)
                elif len(parts) == 4 and parts[1] == "lists" and parts[3] == "companies":
                    ids = data.get("company_ids") or []
                    self.send_json_commit(conn, add_companies_to_list(conn, int(parts[2]), ids))
                elif parsed.path == "/api/emails/validate":
                    results = validate_emails(conn, data.get("emails") or [], data.get("list_id"))
                    self.send_json_commit(conn, {"items": results})
                elif parsed.path == "/api/emails/score":
                    results = score_emails(
                        conn,
                        emails=data.get("emails") or [],
                        list_id=data.get("list_id"),
                        company_id=data.get("company_id"),
                    )
                    self.send_json_commit(conn, {"items": results})
                elif parsed.path == "/api/enrichment/company":
                    result = enrich_company(
                        conn,
                        int(data.get("company_id") or 0),
                        url=data.get("url") or "",
                        html=data.get("html") or "",
                        source_url=data.get("source_url") or "",
                        ttl_days=data.get("ttl_days") or 30,
                    )
                    self.send_json_commit(conn, result)
                elif parsed.path == "/api/experiments/leads/from-list":
                    result = create_leads_from_list(
                        conn,
                        int(data.get("list_id") or 0),
                        data.get("source") or "lista qualificada",
                    )
                    self.send_json_commit(conn, result)
                elif parsed.path == "/api/experiments/campaigns":
                    self.send_json_commit(conn, create_campaign(conn, data), 201)
                elif len(parts) == 5 and parts[1] == "experiments" and parts[2] == "campaigns" and parts[4] == "simulate":
                    self.send_json_commit(
                        conn,
                        simulate_campaign(
                            conn,
                            int(parts[3]),
                            list_id=data.get("list_id"),
                            limit=data.get("limit") or 50,
                        )
                    )
                elif parsed.path == "/api/experiments/events":
                    self.send_json_commit(conn, record_campaign_event(conn, data))
                elif parsed.path == "/api/templates":
                    self.send_json_commit(conn, create_email_template(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "templates" and parts[3] == "versions":
                    self.send_json_commit(conn, create_email_template_version(conn, int(parts[2]), data))
                elif parsed.path == "/api/templates/render":
                    self.send_json_commit(conn, render_email_template(conn, data))
                elif parsed.path == "/api/sequences":
                    self.send_json_commit(conn, create_sequence(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "sequences" and parts[3] == "enroll":
                    self.send_json_commit(conn, enroll_sequence_from_list(conn, int(parts[2]), int(data.get("list_id") or 0)))
                elif len(parts) == 5 and parts[1] == "sequences" and parts[2] == "journeys" and parts[4] == "prepare-next":
                    self.send_json_commit(conn, prepare_next_journey_step(conn, int(parts[3])))
                elif len(parts) == 4 and parts[1] == "approvals" and parts[3] == "approve":
                    self.send_json_commit(conn, approve_sequence_step(conn, int(parts[2]), data.get("note") or ""))
                elif len(parts) == 4 and parts[1] == "approvals" and parts[3] == "reject":
                    self.send_json_commit(conn, reject_sequence_step(conn, int(parts[2]), data.get("note") or ""))
                elif parsed.path == "/api/icp-rules":
                    self.send_json_commit(conn, create_icp_rule(conn, data), 201)
                elif parsed.path == "/api/okrs":
                    self.send_json_commit(conn, create_okr(conn, data), 201)
                elif parsed.path == "/api/agent-governance/configs":
                    self.send_json_commit(conn, create_agent_config(conn, data), 201)
                elif len(parts) == 5 and parts[1] == "agent-governance" and parts[2] == "configs" and parts[4] == "activate":
                    self.send_json_commit(conn, activate_agent_config(conn, int(parts[3])))
                elif parsed.path == "/api/agent-governance/simulations":
                    self.send_json_commit(conn, create_agent_simulation(conn, data), 201)
                elif parsed.path == "/api/agent-governance/costs":
                    self.send_json_commit(conn, record_agent_cost(conn, data), 201)
                elif parsed.path == "/api/playbooks":
                    self.send_json_commit(conn, create_playbook(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "playbooks" and parts[3] == "versions":
                    self.send_json_commit(conn, create_playbook_version(conn, int(parts[2]), data), 201)
                elif len(parts) == 4 and parts[1] == "playbooks" and parts[3] == "apply":
                    self.send_json_commit(conn, apply_playbook(conn, int(parts[2]), data), 201)
                elif len(parts) == 4 and parts[1] == "playbooks" and parts[3] == "clone":
                    self.send_json_commit(conn, clone_playbook_to_workspace(conn, int(parts[2]), data), 201)
                elif len(parts) == 4 and parts[1] == "playbooks" and parts[3] == "execution-plans":
                    self.send_json_commit(conn, create_playbook_execution_plan(conn, int(parts[2]), data), 201)
                elif len(parts) == 4 and parts[1] == "playbook-execution-plans" and parts[3] == "apply":
                    self.send_json_commit(conn, apply_playbook_execution_plan(conn, int(parts[2]), data), 201)
                elif parsed.path == "/api/saas/api-keys":
                    self.send_json_commit(conn, create_api_key(conn, data), 201)
                elif len(parts) == 5 and parts[1] == "saas" and parts[2] == "api-keys" and parts[4] == "revoke":
                    self.send_json_commit(conn, revoke_api_key(conn, int(parts[3]), data))
                elif parsed.path == "/api/saas/credits/adjust":
                    self.send_json_commit(conn, adjust_credit_wallet(conn, data), 201)
                elif parsed.path == "/api/notifications/generate":
                    self.send_json_commit(conn, generate_notifications(conn), 201)
                elif len(parts) == 4 and parts[1] == "notifications" and parts[3] == "mark-read":
                    self.send_json_commit(conn, update_notification_status(conn, int(parts[2]), "read"))
                elif len(parts) == 4 and parts[1] == "notifications" and parts[3] == "dismiss":
                    self.send_json_commit(conn, update_notification_status(conn, int(parts[2]), "dismissed"))
                elif parsed.path == "/api/workspace-context":
                    self.send_json_commit(conn, set_current_workspace(conn, int(data.get("org_id") or 0)))
                elif parsed.path == "/api/workspaces":
                    self.send_json_commit(conn, create_workspace(conn, data), 201)
                elif parsed.path == "/api/workspaces/onboarding":
                    self.send_json_commit(conn, run_workspace_onboarding(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "workspaces" and parts[3] == "snapshot":
                    self.send_json_commit(conn, create_workspace_snapshot(conn, int(parts[2])), 201)
                elif len(parts) == 4 and parts[1] == "icp-rules" and parts[3] == "prioritize":
                    self.send_json_commit(
                        conn,
                        prioritize_icp_rule(
                            conn,
                            int(parts[2]),
                            list_id=data.get("list_id"),
                            limit=data.get("limit"),
                        ),
                    )
                elif len(parts) == 4 and parts[1] == "priority-queue" and parts[3] == "accept":
                    self.send_json_commit(conn, decide_priority_queue_item(conn, int(parts[2]), "accept", data.get("note") or ""))
                elif len(parts) == 4 and parts[1] == "priority-queue" and parts[3] == "reject":
                    self.send_json_commit(conn, decide_priority_queue_item(conn, int(parts[2]), "reject", data.get("note") or ""))
                elif parsed.path == "/api/command-center/actions":
                    self.send_json_commit(conn, command_center_action(conn, data))
                elif parsed.path == "/api/replies/classify":
                    self.send_json_commit(conn, record_inbound_reply(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "handoffs" and parts[3] == "meeting":
                    self.send_json_commit(conn, create_meeting_from_handoff(conn, int(parts[2]), data), 201)
                elif len(parts) == 4 and parts[1] == "handoffs" and parts[3] == "resolve":
                    self.send_json_commit(conn, decide_handoff(conn, int(parts[2]), "resolve", data.get("note") or ""))
                elif len(parts) == 4 and parts[1] == "handoffs" and parts[3] == "dismiss":
                    self.send_json_commit(conn, decide_handoff(conn, int(parts[2]), "dismiss", data.get("note") or ""))
                elif parsed.path == "/api/meetings":
                    self.send_json_commit(conn, create_meeting(conn, data), 201)
                elif len(parts) == 4 and parts[1] == "meetings" and parts[3] == "status":
                    self.send_json_commit(conn, update_meeting_status(conn, int(parts[2]), data.get("status"), data.get("note") or ""))
                elif parsed.path == "/api/suppression":
                    self.send_json_commit(conn, add_suppression(conn, data.get("email"), data.get("reason") or "manual"))
                elif parsed.path == "/api/sources/official/download":
                    snapshot = data.get("snapshot")
                    filenames = data.get("filenames") or []
                    if not snapshot or not filenames:
                        self.send_error_json("Informe snapshot e filenames")
                    else:
                        self.send_json_commit(conn, {"items": download_files(conn, snapshot, filenames, data.get("force") is True)})
                elif parsed.path == "/api/sources/official/sync":
                    self.send_json_commit(
                        conn,
                        sync_official_snapshot(
                            conn,
                            snapshot=data.get("snapshot"),
                            chunk=data.get("chunk", 1),
                            limit=data.get("limit", 1000),
                            mode=data.get("mode", "domains"),
                        )
                    )
                elif parsed.path == "/api/sources/brasilapi/cnpj":
                    self.send_json_commit(conn, import_brasilapi_cnpj(conn, data.get("cnpj")))
                else:
                    self.send_error_json("Endpoint nao encontrado", 404)
        except Exception as exc:
            self.send_error_json(str(exc), 500)

    def handle_api_delete(self, parsed):
        parts = [part for part in parsed.path.split("/") if part]
        try:
            with connect() as conn:
                if len(parts) == 5 and parts[1] == "lists" and parts[3] == "companies":
                    self.send_json_commit(conn, remove_company_from_list(conn, int(parts[2]), int(parts[4])))
                else:
                    self.send_error_json("Endpoint nao encontrado", 404)
        except Exception as exc:
            self.send_error_json(str(exc), 500)


def main():
    init_db()
    host = os.environ.get("RADAR_CNPJ_HOST", "127.0.0.1")
    port = int(os.environ.get("RADAR_CNPJ_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), RadarHandler)
    print("Radar CNPJ Interno em http://%s:%s" % (host, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
