import base64
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from .database import now_iso
from .services import import_official_zip_directory, upsert_company


OFFICIAL_SHARE_TOKEN = "YggdBLfdninEJX9"
OFFICIAL_WEBDAV_URL = "https://arquivos.receitafederal.gov.br/public.php/webdav/"
OFFICIAL_PUBLIC_PAGE = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9"
OFFICIAL_DATASET_PAGE = "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj"
OFFICIAL_METADATA_PDF = "https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf"
BRASILAPI_CNPJ_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

SMALL_DOMAIN_FILES = [
    "Cnaes.zip",
    "Motivos.zip",
    "Municipios.zip",
    "Naturezas.zip",
    "Paises.zip",
    "Qualificacoes.zip",
]


def download_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "downloads", "receita"))


def auth_header():
    token = ("%s:" % OFFICIAL_SHARE_TOKEN).encode("utf-8")
    return "Basic " + base64.b64encode(token).decode("ascii")


def webdav_url(path=""):
    path = path.strip("/")
    if not path:
        return OFFICIAL_WEBDAV_URL
    quoted = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    return urllib.parse.urljoin(OFFICIAL_WEBDAV_URL, quoted)


def request_webdav(path="", method="GET", headers=None, timeout=30):
    req = urllib.request.Request(webdav_url(path), method=method)
    req.add_header("Authorization", auth_header())
    req.add_header("User-Agent", "RadarCNPJInterno/0.1")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return urllib.request.urlopen(req, timeout=timeout)


def propfind(path="", depth=1, timeout=60):
    with request_webdav(path, method="PROPFIND", headers={"Depth": str(depth)}, timeout=timeout) as response:
        return response.read()


def parse_propfind(xml_bytes):
    ns = {"d": "DAV:"}
    root = ET.fromstring(xml_bytes)
    items = []
    for response in root.findall("d:response", ns):
        href = response.findtext("d:href", default="", namespaces=ns)
        prop = response.find("d:propstat/d:prop", ns)
        if prop is None:
            continue
        resource_type = prop.find("d:resourcetype", ns)
        is_dir = resource_type is not None and resource_type.find("d:collection", ns) is not None
        size = prop.findtext("d:getcontentlength", default="", namespaces=ns)
        quota_size = prop.findtext("d:quota-used-bytes", default="", namespaces=ns)
        name = urllib.parse.unquote(href.rstrip("/").split("/")[-1])
        if not name:
            continue
        items.append(
            {
                "name": name,
                "href": href,
                "is_dir": is_dir,
                "size_bytes": int(size or quota_size or 0),
                "last_modified": prop.findtext("d:getlastmodified", default="", namespaces=ns),
                "etag": (prop.findtext("d:getetag", default="", namespaces=ns) or "").replace('"', ""),
                "content_type": prop.findtext("d:getcontenttype", default="", namespaces=ns),
            }
        )
    return items


def list_snapshots():
    items = parse_propfind(propfind("", depth=1))
    snapshots = [item for item in items if item["is_dir"] and is_snapshot_name(item["name"])]
    snapshots.sort(key=lambda item: item["name"], reverse=True)
    return snapshots


def is_snapshot_name(value):
    if len(value) != 7 or value[4] != "-":
        return False
    year, month = value.split("-")
    return year.isdigit() and month.isdigit()


def latest_snapshot():
    snapshots = list_snapshots()
    return snapshots[0] if snapshots else None


def list_snapshot_files(snapshot):
    items = parse_propfind(propfind(snapshot, depth=1))
    files = [item for item in items if not item["is_dir"]]
    files.sort(key=lambda item: item["name"])
    return files


def find_snapshot_file(files, filename):
    lower = filename.lower()
    for item in files:
        if item["name"].lower() == lower:
            return item
    return None


def local_snapshot_dir(snapshot):
    path = os.path.abspath(os.path.join(download_root(), snapshot))
    os.makedirs(path, exist_ok=True)
    return path


def local_file_path(snapshot, filename):
    directory = local_snapshot_dir(snapshot)
    target = os.path.abspath(os.path.join(directory, filename))
    if not target.startswith(directory):
        raise ValueError("Nome de arquivo invalido")
    return target


def record_source_file(conn, snapshot, file_info, local_path, status):
    conn.execute(
        """
        INSERT INTO source_files (snapshot, filename, url, size_bytes, etag, local_path, status, downloaded_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(snapshot, filename) DO UPDATE SET
            url = excluded.url,
            size_bytes = excluded.size_bytes,
            etag = excluded.etag,
            local_path = excluded.local_path,
            status = excluded.status,
            downloaded_at = excluded.downloaded_at,
            updated_at = excluded.updated_at
        """,
        (
            snapshot,
            file_info["name"],
            webdav_url("%s/%s" % (snapshot, file_info["name"])),
            file_info.get("size_bytes") or 0,
            file_info.get("etag") or "",
            local_path,
            status,
            now_iso(),
            now_iso(),
        ),
    )


def download_snapshot_file(conn, snapshot, filename, force=False):
    files = list_snapshot_files(snapshot)
    file_info = find_snapshot_file(files, filename)
    if not file_info:
        raise ValueError("Arquivo %s nao encontrado no snapshot %s" % (filename, snapshot))
    target = local_file_path(snapshot, file_info["name"])
    if os.path.exists(target) and not force and os.path.getsize(target) == file_info["size_bytes"]:
        record_source_file(conn, snapshot, file_info, target, "downloaded")
        return {"filename": file_info["name"], "path": target, "size_bytes": file_info["size_bytes"], "cached": True}

    temp_target = target + ".part"
    with request_webdav("%s/%s" % (snapshot, file_info["name"]), timeout=120) as response:
        with open(temp_target, "wb") as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    os.replace(temp_target, target)
    record_source_file(conn, snapshot, file_info, target, "downloaded")
    return {"filename": file_info["name"], "path": target, "size_bytes": file_info["size_bytes"], "cached": False}


def download_files(conn, snapshot, filenames, force=False):
    results = []
    for filename in filenames:
        results.append(download_snapshot_file(conn, snapshot, filename, force=force))
    return results


def catalog():
    latest = latest_snapshot()
    files = list_snapshot_files(latest["name"]) if latest else []
    return {
        "official_public_page": OFFICIAL_PUBLIC_PAGE,
        "official_dataset_page": OFFICIAL_DATASET_PAGE,
        "official_metadata_pdf": OFFICIAL_METADATA_PDF,
        "webdav_url": OFFICIAL_WEBDAV_URL,
        "latest": latest,
        "snapshots": list_snapshots()[:12],
        "latest_files": files,
        "small_domain_files": SMALL_DOMAIN_FILES,
    }


def sync_official_snapshot(conn, snapshot=None, chunk=1, limit=1000, mode="domains"):
    selected_snapshot = snapshot or (latest_snapshot() or {}).get("name")
    if not selected_snapshot:
        raise ValueError("Nenhum snapshot oficial encontrado")

    files = list_snapshot_files(selected_snapshot)
    filenames = []
    for filename in SMALL_DOMAIN_FILES:
        if find_snapshot_file(files, filename):
            filenames.append(filename)

    if mode in ("chunk", "full"):
        chunk = int(chunk)
        for prefix in ("Empresas", "Estabelecimentos", "Socios"):
            filename = "%s%s.zip" % (prefix, chunk)
            if find_snapshot_file(files, filename):
                filenames.append(filename)

    if mode == "full":
        for item in files:
            if item["name"].lower().endswith(".zip") and item["name"] not in filenames:
                filenames.append(item["name"])

    downloaded = download_files(conn, selected_snapshot, filenames)
    imported = None
    if mode in ("chunk", "full"):
        imported = import_official_zip_directory(
            conn,
            local_snapshot_dir(selected_snapshot),
            source_name="Receita Federal - Dados Abertos CNPJ %s" % selected_snapshot,
            source_url=OFFICIAL_PUBLIC_PAGE,
            legal_basis="Legitimo interesse B2B com base em dados publicos oficiais",
            chunk=chunk,
            limit=limit,
        )
    return {
        "snapshot": selected_snapshot,
        "mode": mode,
        "downloaded": downloaded,
        "imported": imported,
    }


def brasilapi_lookup(cnpj):
    digits = "".join(ch for ch in str(cnpj or "") if ch.isdigit())
    if len(digits) != 14:
        raise ValueError("Informe um CNPJ com 14 digitos")
    url = BRASILAPI_CNPJ_URL.format(cnpj=digits)
    req = urllib.request.Request(url, headers={"User-Agent": "RadarCNPJInterno/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise ValueError("BrasilAPI retornou erro %s: %s" % (exc.code, message))
    return payload


def import_brasilapi_cnpj(conn, cnpj):
    payload = brasilapi_lookup(cnpj)
    company_payload = map_brasilapi_company(payload)
    company_id = upsert_company(
        conn,
        company_payload,
        source_name="BrasilAPI CNPJ",
        source_url=BRASILAPI_CNPJ_URL.format(cnpj="".join(ch for ch in str(cnpj) if ch.isdigit())),
        legal_basis="Legitimo interesse B2B com base em dados publicos",
    )
    return {"company_id": company_id, "company": company_payload, "raw": payload}


def map_brasilapi_company(payload):
    cnaes = payload.get("cnaes_secundarios") or []
    partners = []
    for partner in payload.get("qsa") or []:
        partners.append(
            {
                "name": partner.get("nome_socio") or "",
                "qualification": partner.get("qualificacao_socio") or "",
                "entry_date": partner.get("data_entrada_sociedade") or "",
                "age_range": partner.get("faixa_etaria") or "",
                "document_masked": partner.get("cnpj_cpf_do_socio") or "",
            }
        )
    return {
        "cnpj": payload.get("cnpj"),
        "legal_name": payload.get("razao_social") or payload.get("nome_fantasia") or payload.get("cnpj"),
        "trade_name": payload.get("nome_fantasia") or "",
        "status": payload.get("descricao_situacao_cadastral") or payload.get("situacao_cadastral") or "",
        "opening_date": payload.get("data_inicio_atividade") or "",
        "status_date": payload.get("data_situacao_cadastral") or "",
        "main_cnae_code": str(payload.get("cnae_fiscal") or ""),
        "main_cnae_description": payload.get("cnae_fiscal_descricao") or "",
        "secondary_cnaes": "; ".join(
            "%s - %s" % (item.get("codigo", ""), item.get("descricao", "")) for item in cnaes
        ),
        "legal_nature": payload.get("natureza_juridica") or "",
        "size": payload.get("porte") or "",
        "establishment_type": "Matriz" if payload.get("identificador_matriz_filial") == 1 else "Filial",
        "street_type": payload.get("descricao_tipo_de_logradouro") or "",
        "street": payload.get("logradouro") or "",
        "number": payload.get("numero") or "",
        "complement": payload.get("complemento") or "",
        "district": payload.get("bairro") or "",
        "city": payload.get("municipio") or "",
        "state": payload.get("uf") or "",
        "zip_code": payload.get("cep") or "",
        "email": (payload.get("email") or "").lower(),
        "phone": build_phone(payload.get("ddd_telefone_1"), payload.get("ddd_telefone_2")),
        "capital_social": payload.get("capital_social") or 0,
        "partners": partners,
    }


def build_phone(primary, secondary=None):
    if primary:
        return str(primary)
    if secondary:
        return str(secondary)
    return ""

