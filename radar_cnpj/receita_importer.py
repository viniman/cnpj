import csv
import io
import os
import zipfile


def find_first(directory, token):
    token = token.upper()
    for name in os.listdir(directory):
        if token in name.upper() and not name.startswith("."):
            return os.path.join(directory, name)
    return None


def open_csv(path, encoding="latin-1"):
    return open(path, "r", encoding=encoding, newline="", errors="replace")


def read_domain_file(path):
    values = {}
    if not path:
        return values
    with open_csv(path) as handle:
        reader = csv.reader(handle, delimiter=";")
        for row in reader:
            if len(row) >= 2:
                values[row[0].strip()] = row[1].strip()
    return values


def read_domain_zip(path):
    values = {}
    if not path or not os.path.exists(path):
        return values
    for row in iter_zip_csv_rows(path):
        if len(row) >= 2:
            values[row[0].strip()] = row[1].strip()
    return values


def iter_zip_csv_rows(path, encoding="latin-1"):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if not names:
            return
        name = names[0]
        with archive.open(name) as raw:
            wrapper = io.TextIOWrapper(raw, encoding=encoding, newline="", errors="replace")
            reader = csv.reader(wrapper, delimiter=";")
            for row in reader:
                yield row


def find_zip(directory, prefix, chunk=None):
    names = os.listdir(directory)
    candidates = []
    for name in names:
        if not name.lower().endswith(".zip"):
            continue
        lower = name.lower()
        if chunk is None:
            if lower.startswith(prefix.lower()):
                candidates.append(name)
        else:
            if lower == ("%s%s.zip" % (prefix, chunk)).lower():
                candidates.append(name)
    if not candidates:
        return None
    candidates.sort()
    return os.path.join(directory, candidates[0])


PORTE_MAP = {
    "00": "NAO INFORMADO",
    "0": "NAO INFORMADO",
    "01": "ME",
    "1": "ME",
    "03": "EPP",
    "3": "EPP",
    "05": "DEMAIS",
    "5": "DEMAIS",
}

STATUS_MAP = {
    "01": "Nula",
    "1": "Nula",
    "02": "Ativa",
    "2": "Ativa",
    "03": "Suspensa",
    "3": "Suspensa",
    "04": "Inapta",
    "4": "Inapta",
    "08": "Baixada",
    "8": "Baixada",
}


def parse_receita_zip_directory(directory, chunk=1, limit=1000):
    """Parse Receita Federal ZIP files downloaded from the official share."""
    cnae_zip = find_zip(directory, "Cnaes")
    municipio_zip = find_zip(directory, "Municipios")
    natureza_zip = find_zip(directory, "Naturezas")
    qualificacao_zip = find_zip(directory, "Qualificacoes")
    empresas_zip = find_zip(directory, "Empresas", chunk)
    estabelecimentos_zip = find_zip(directory, "Estabelecimentos", chunk)
    socios_zip = find_zip(directory, "Socios", chunk)

    if not empresas_zip or not estabelecimentos_zip:
        raise ValueError("Baixe Empresas%s.zip e Estabelecimentos%s.zip antes de importar" % (chunk, chunk))

    cnaes = read_domain_zip(cnae_zip)
    municipios = read_domain_zip(municipio_zip)
    naturezas = read_domain_zip(natureza_zip)
    qualificacoes = read_domain_zip(qualificacao_zip)

    wanted_roots = set()
    establishments = []
    for row in iter_zip_csv_rows(estabelecimentos_zip):
        if len(row) < 28:
            continue
        status = row[5].strip()
        # For prospecting lists, active establishments are the useful default.
        if status not in ("02", "2"):
            continue
        cnpj_root = row[0].strip()
        cnae_code = row[11].strip()
        city_code = row[20].strip()
        phone = build_receita_phone(row)
        establishments.append(
            {
                "cnpj_root": cnpj_root,
                "cnpj": "%s%s%s" % (cnpj_root, row[1].strip(), row[2].strip()),
                "trade_name": row[4].strip(),
                "status": STATUS_MAP.get(status, status),
                "status_date": row[6].strip(),
                "opening_date": row[10].strip(),
                "main_cnae_code": cnae_code,
                "main_cnae_description": cnaes.get(cnae_code, ""),
                "secondary_cnaes": row[12].strip(),
                "establishment_type": "Matriz" if row[3].strip() == "1" else "Filial",
                "street_type": row[13].strip(),
                "street": row[14].strip(),
                "number": row[15].strip(),
                "complement": row[16].strip(),
                "district": row[17].strip(),
                "zip_code": row[18].strip(),
                "state": row[19].strip(),
                "city": municipios.get(city_code, city_code),
                "email": row[27].strip().lower(),
                "phone": phone,
                "partners": [],
            }
        )
        wanted_roots.add(cnpj_root)
        if len(establishments) >= int(limit or 1000):
            break

    companies_by_root = {}
    for row in iter_zip_csv_rows(empresas_zip):
        if len(row) < 7:
            continue
        root = row[0].strip()
        if root not in wanted_roots:
            continue
        legal_nature_code = row[2].strip()
        companies_by_root[root] = {
            "legal_name": row[1].strip(),
            "legal_nature": naturezas.get(legal_nature_code, legal_nature_code),
            "capital_social": row[4].strip().replace(",", "."),
            "size": PORTE_MAP.get(row[5].strip(), row[5].strip()),
        }
        if len(companies_by_root) >= len(wanted_roots):
            break

    partners_by_root = dict((root, []) for root in wanted_roots)
    if socios_zip:
        for row in iter_zip_csv_rows(socios_zip):
            if len(row) < 11:
                continue
            root = row[0].strip()
            if root not in partners_by_root:
                continue
            qualification_code = row[4].strip()
            partners_by_root[root].append(
                {
                    "name": row[2].strip(),
                    "document_masked": row[3].strip(),
                    "qualification": qualificacoes.get(qualification_code, qualification_code),
                    "entry_date": row[5].strip(),
                    "age_range": row[10].strip(),
                }
            )

    payloads = []
    for establishment in establishments:
        root = establishment.pop("cnpj_root")
        basic = companies_by_root.get(root, {})
        payload = {}
        payload.update(establishment)
        payload.update(
            {
                "legal_name": basic.get("legal_name") or establishment["cnpj"],
                "legal_nature": basic.get("legal_nature", ""),
                "capital_social": basic.get("capital_social", 0),
                "size": basic.get("size", ""),
                "partners": partners_by_root.get(root, []),
            }
        )
        payloads.append(payload)
    return payloads


def build_receita_phone(row):
    if len(row) > 22 and row[21].strip() and row[22].strip():
        return "(%s) %s" % (row[21].strip(), row[22].strip())
    if len(row) > 24 and row[23].strip() and row[24].strip():
        return "(%s) %s" % (row[23].strip(), row[24].strip())
    return ""


def parse_receita_directory(directory, limit=1000):
    """Parse a reduced Receita Federal directory sample.

    This MVP parser is intended for samples and local validation. Full national
    imports should use staging tables and database COPY as described in docs.
    """
    empresa_path = find_first(directory, "EMPRE")
    estabelecimento_path = find_first(directory, "ESTABELE")
    socio_path = find_first(directory, "SOCIO")
    cnae_path = find_first(directory, "CNAE")
    municipio_path = find_first(directory, "MUNIC")

    if not empresa_path or not estabelecimento_path:
        raise ValueError("Diretorio precisa conter arquivos EMPRECSV e ESTABELE")

    cnaes = read_domain_file(cnae_path)
    municipios = read_domain_file(municipio_path)

    companies_by_root = {}
    with open_csv(empresa_path) as handle:
        reader = csv.reader(handle, delimiter=";")
        for row in reader:
            if len(row) < 7:
                continue
            root = row[0].strip()
            companies_by_root[root] = {
                "legal_name": row[1].strip(),
                "legal_nature": row[2].strip(),
                "capital_social": row[4].strip().replace(",", "."),
                "size": row[5].strip(),
            }

    payloads = []
    roots = set()
    with open_csv(estabelecimento_path) as handle:
        reader = csv.reader(handle, delimiter=";")
        for row in reader:
            if len(row) < 28:
                continue
            root = row[0].strip()
            basic = companies_by_root.get(root, {})
            cnpj = "%s%s%s" % (root, row[1].strip(), row[2].strip())
            cnae_code = row[11].strip()
            city_code = row[20].strip()
            phone = ""
            if row[21].strip() and row[22].strip():
                phone = "(%s) %s" % (row[21].strip(), row[22].strip())
            payloads.append(
                {
                    "cnpj": cnpj,
                    "legal_name": basic.get("legal_name") or cnpj,
                    "trade_name": row[4].strip(),
                    "status": "Ativa" if row[5].strip() == "02" else row[5].strip(),
                    "opening_date": row[10].strip(),
                    "main_cnae_code": cnae_code,
                    "main_cnae_description": cnaes.get(cnae_code, ""),
                    "secondary_cnaes": row[12].strip(),
                    "legal_nature": basic.get("legal_nature", ""),
                    "size": basic.get("size", ""),
                    "establishment_type": "Matriz" if row[3].strip() == "1" else "Filial",
                    "street_type": row[13].strip(),
                    "street": row[14].strip(),
                    "number": row[15].strip(),
                    "complement": row[16].strip(),
                    "district": row[17].strip(),
                    "zip_code": row[18].strip(),
                    "state": row[19].strip(),
                    "city": municipios.get(city_code, city_code),
                    "email": row[27].strip().lower(),
                    "phone": phone,
                    "capital_social": basic.get("capital_social", 0),
                    "partners": [],
                }
            )
            roots.add(root)
            if len(payloads) >= int(limit or 1000):
                break

    if socio_path:
        partners_by_root = dict((root, []) for root in roots)
        with open_csv(socio_path) as handle:
            reader = csv.reader(handle, delimiter=";")
            for row in reader:
                if len(row) < 11:
                    continue
                root = row[0].strip()
                if root not in partners_by_root:
                    continue
                partners_by_root[root].append(
                    {
                        "name": row[2].strip(),
                        "document_masked": row[3].strip(),
                        "qualification": row[4].strip(),
                        "entry_date": row[5].strip(),
                        "age_range": row[10].strip(),
                    }
                )
        for payload in payloads:
            root = "".join(ch for ch in payload["cnpj"] if ch.isdigit())[:8]
            payload["partners"] = partners_by_root.get(root, [])

    return payloads
