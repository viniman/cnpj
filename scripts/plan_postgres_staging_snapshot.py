import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from radar_cnpj.postgres_staging import build_staging_import_manifest, official_file_family


FAMILY_ORDER = {
    "cnaes": 10,
    "motivos": 20,
    "municipios": 30,
    "naturezas": 40,
    "paises": 50,
    "qualificacoes": 60,
    "simples": 70,
    "empresas": 100,
    "estabelecimentos": 200,
    "socios": 300,
}


def sort_key(item):
    chunk = item.get("chunk")
    return (FAMILY_ORDER.get(item["family"], 999), -1 if chunk is None else int(chunk), item["filename"].lower())


def snapshot_manifests(snapshot, source_dir, families=None, limit=0, extract_root="", container_dir="/tmp/radar-cnpj-staging"):
    selected_families = {item.strip().lower() for item in (families or []) if item.strip()}
    manifests = []
    for name in os.listdir(source_dir):
        classification = official_file_family(name)
        if not classification:
            continue
        if selected_families and classification["family"] not in selected_families:
            continue
        zip_path = os.path.join(source_dir, name)
        if not os.path.isfile(zip_path):
            continue
        manifest = build_staging_import_manifest(
            snapshot,
            classification["filename"],
            zip_path=zip_path,
            extract_root=extract_root or None,
            container_dir=container_dir,
        )
        manifest["zip_size_bytes"] = os.path.getsize(zip_path)
        manifests.append(manifest)
    manifests.sort(key=sort_key)
    if limit:
        manifests = manifests[: int(limit)]
    return manifests


def main(argv=None):
    parser = argparse.ArgumentParser(description="Planeja importação de snapshot oficial para receita_staging.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--families", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extract-root", default="")
    parser.add_argument("--container-dir", default="/tmp/radar-cnpj-staging")
    args = parser.parse_args(argv)

    families = [item for item in args.families.split(",") if item.strip()]
    manifests = snapshot_manifests(
        args.snapshot,
        args.source_dir,
        families=families,
        limit=args.limit,
        extract_root=args.extract_root,
        container_dir=args.container_dir,
    )
    print(
        json.dumps(
            {
                "snapshot": args.snapshot,
                "source_dir": os.path.abspath(args.source_dir),
                "count": len(manifests),
                "items": manifests,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
