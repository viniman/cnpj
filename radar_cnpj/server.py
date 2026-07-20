import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .database import connect, init_db
from .services import (
    add_companies_to_list,
    add_suppression,
    audit_events,
    create_list,
    dashboard,
    export_list,
    get_company,
    get_list,
    import_source,
    list_lists,
    remove_company_from_list,
    score_emails,
    search_companies,
    seed_sample,
    validate_emails,
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
                elif parsed.path == "/api/companies":
                    self.send_json(search_companies(conn, params))
                elif len(parts) == 3 and parts[1] == "companies":
                    company = get_company(conn, int(parts[2]))
                    if not company:
                        self.send_error_json("Empresa nao encontrada", 404)
                    else:
                        self.send_json(company)
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
                    extension = "xlsx" if params.get("format") == "xlsx" else "csv"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Disposition", 'attachment; filename="radar-cnpj-lista.%s"' % extension)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                elif parsed.path == "/api/audit":
                    self.send_json({"items": audit_events(conn, params.get("limit", 100))})
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
                    self.send_json(result)
                elif parsed.path == "/api/import":
                    result = import_source(
                        conn,
                        data.get("path", ""),
                        data.get("source_name") or "Importacao local",
                        data.get("source_url") or "",
                        data.get("legal_basis") or "Legitimo interesse B2B",
                        data.get("limit") or 1000,
                    )
                    self.send_json(result)
                elif parsed.path == "/api/lists":
                    name = (data.get("name") or "").strip()
                    if not name:
                        self.send_error_json("Nome da lista e obrigatorio")
                    else:
                        self.send_json(create_list(conn, name, data.get("description") or ""), 201)
                elif len(parts) == 4 and parts[1] == "lists" and parts[3] == "companies":
                    ids = data.get("company_ids") or []
                    self.send_json(add_companies_to_list(conn, int(parts[2]), ids))
                elif parsed.path == "/api/emails/validate":
                    results = validate_emails(conn, data.get("emails") or [], data.get("list_id"))
                    self.send_json({"items": results})
                elif parsed.path == "/api/emails/score":
                    results = score_emails(
                        conn,
                        emails=data.get("emails") or [],
                        list_id=data.get("list_id"),
                        company_id=data.get("company_id"),
                    )
                    self.send_json({"items": results})
                elif parsed.path == "/api/suppression":
                    self.send_json(add_suppression(conn, data.get("email"), data.get("reason") or "manual"))
                elif parsed.path == "/api/sources/official/download":
                    snapshot = data.get("snapshot")
                    filenames = data.get("filenames") or []
                    if not snapshot or not filenames:
                        self.send_error_json("Informe snapshot e filenames")
                    else:
                        self.send_json({"items": download_files(conn, snapshot, filenames, data.get("force") is True)})
                elif parsed.path == "/api/sources/official/sync":
                    self.send_json(
                        sync_official_snapshot(
                            conn,
                            snapshot=data.get("snapshot"),
                            chunk=data.get("chunk", 1),
                            limit=data.get("limit", 1000),
                            mode=data.get("mode", "domains"),
                        )
                    )
                elif parsed.path == "/api/sources/brasilapi/cnpj":
                    self.send_json(import_brasilapi_cnpj(conn, data.get("cnpj")))
                else:
                    self.send_error_json("Endpoint nao encontrado", 404)
        except Exception as exc:
            self.send_error_json(str(exc), 500)

    def handle_api_delete(self, parsed):
        parts = [part for part in parsed.path.split("/") if part]
        try:
            with connect() as conn:
                if len(parts) == 5 and parts[1] == "lists" and parts[3] == "companies":
                    self.send_json(remove_company_from_list(conn, int(parts[2]), int(parts[4])))
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
