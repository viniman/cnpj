import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from radar_cnpj.postgres_staging import build_staging_import_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Planeja importação de arquivo oficial para receita_staging.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--zip-path", default="")
    parser.add_argument("--csv-path", default="")
    parser.add_argument("--extract-root", default="")
    parser.add_argument("--container-dir", default="/tmp/radar-cnpj-staging")
    args = parser.parse_args(argv)

    manifest = build_staging_import_manifest(
        args.snapshot,
        args.filename,
        zip_path=args.zip_path or None,
        csv_path=args.csv_path or None,
        extract_root=args.extract_root or None,
        container_dir=args.container_dir,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
