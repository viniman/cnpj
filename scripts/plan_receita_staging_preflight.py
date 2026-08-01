import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from radar_cnpj.postgres_staging import expected_official_filenames, official_file_family
from scripts.plan_postgres_staging_snapshot import snapshot_manifests


REQUIRED_FAMILIES = [
    "cnaes",
    "motivos",
    "municipios",
    "naturezas",
    "paises",
    "qualificacoes",
    "simples",
    "empresas",
    "estabelecimentos",
    "socios",
]


def check_result(name, status, message, details=None):
    return {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {},
    }


def family_summary(items):
    summary = {}
    for item in items:
        family = item["family"]
        summary[family] = summary.get(family, 0) + 1
    return summary


def recognized_zip_files(source_dir):
    files = []
    ignored = []
    if not os.path.isdir(source_dir):
        return files, ignored

    for name in sorted(os.listdir(source_dir), key=str.lower):
        path = os.path.join(source_dir, name)
        if not os.path.isfile(path):
            continue
        classification = official_file_family(name)
        if not classification:
            ignored.append(name)
            continue
        item = dict(classification)
        item["path"] = os.path.abspath(path)
        item["size_bytes"] = os.path.getsize(path)
        files.append(item)
    return files, ignored


def disk_capacity_check(total_bytes, free_bytes=None, multiplier=3.0, scoped=False):
    if free_bytes is None:
        return check_result(
            "disk_capacity",
            "warn",
            "Disk capacity was not provided.",
            {
                "total_bytes": int(total_bytes or 0),
                "free_bytes": None,
                "required_bytes": int((total_bytes or 0) * float(multiplier)),
                "multiplier": float(multiplier),
                "scoped": bool(scoped),
            },
        )

    required_bytes = int((total_bytes or 0) * float(multiplier))
    details = {
        "total_bytes": int(total_bytes or 0),
        "free_bytes": int(free_bytes),
        "required_bytes": required_bytes,
        "multiplier": float(multiplier),
        "scoped": bool(scoped),
    }
    if scoped:
        return check_result(
            "disk_capacity",
            "pass" if int(free_bytes) > 0 else "warn",
            "Disk capacity check is informational for scoped imports.",
            details,
        )
    if int(free_bytes) < required_bytes:
        return check_result(
            "disk_capacity",
            "fail",
            "Insufficient free disk for full snapshot import.",
            details,
        )
    return check_result("disk_capacity", "pass", "Disk capacity is sufficient for full snapshot import.", details)


def build_next_commands(snapshot, families="", limit=0):
    base = (
        "powershell -NoProfile -ExecutionPolicy Bypass -File "
        "scripts\\import_postgres_staging_snapshot.ps1 -Snapshot %s"
    ) % snapshot
    smoke = base + " -Families cnaes,municipios,naturezas"
    full = base
    if families:
        full += " -Families %s" % families
    if limit:
        full += " -Limit %s" % int(limit)
    return {
        "apply_migrations": (
            "powershell -NoProfile -ExecutionPolicy Bypass -File "
            "scripts\\apply_postgres_migrations.ps1"
        ),
        "smoke_import": smoke,
        "snapshot_import": full,
    }


def preflight_report(
    snapshot,
    source_dir,
    families=None,
    limit=0,
    expected_files=37,
    free_bytes=None,
    disk_multiplier=3.0,
):
    source_dir = os.path.abspath(source_dir)
    selected_families = [item.strip().lower() for item in (families or []) if item.strip()]
    required_families = selected_families or REQUIRED_FAMILIES
    checks = []

    if os.path.isdir(source_dir):
        checks.append(check_result("source_dir", "pass", "Snapshot directory found.", {"source_dir": source_dir}))
    else:
        checks.append(check_result("source_dir", "fail", "Snapshot directory not found.", {"source_dir": source_dir}))
        return {
            "snapshot": snapshot,
            "source_dir": source_dir,
            "status": "fail",
            "checks": checks,
            "summary": {
                "recognized_files": 0,
                "ignored_files": 0,
                "expected_files": int(expected_files),
                "total_bytes": 0,
                "families": {},
            },
            "missing_expected_files": expected_official_filenames(),
            "ignored_files": [],
            "next_commands": build_next_commands(snapshot, ",".join(selected_families), limit),
        }

    files, ignored = recognized_zip_files(source_dir)
    families_count = family_summary(files)
    total_bytes = sum(item["size_bytes"] for item in files)
    scoped_import = bool(selected_families or limit)
    missing_families = [family for family in required_families if families_count.get(family, 0) == 0]
    expected_names = []
    for name in expected_official_filenames():
        classification = official_file_family(name)
        if not selected_families or classification["family"] in selected_families:
            expected_names.append(name)
    present_names = {item["filename"].lower() for item in files}
    missing_expected = [name for name in expected_names if name.lower() not in present_names]

    if files:
        checks.append(
            check_result(
                "recognized_files",
                "pass",
                "Official ZIP files recognized.",
                {"count": len(files), "total_bytes": total_bytes},
            )
        )
    else:
        checks.append(check_result("recognized_files", "fail", "No official ZIP files were recognized."))

    if missing_families:
        checks.append(
            check_result(
                "required_families",
                "fail",
                "Required official file families are missing.",
                {"missing_families": missing_families},
            )
        )
    else:
        checks.append(check_result("required_families", "pass", "All required official file families are present."))

    if expected_files and len(files) != int(expected_files):
        checks.append(
            check_result(
                "expected_file_count",
                "warn",
                "Recognized file count differs from the expected snapshot count.",
                {"expected": int(expected_files), "actual": len(files)},
            )
        )
    else:
        checks.append(
            check_result(
                "expected_file_count",
                "pass",
                "Recognized file count matches expected snapshot count.",
                {"expected": int(expected_files), "actual": len(files)},
            )
        )

    checks.append(disk_capacity_check(total_bytes, free_bytes=free_bytes, multiplier=disk_multiplier, scoped=scoped_import))

    try:
        manifests = snapshot_manifests(snapshot, source_dir, families=selected_families, limit=limit)
        checks.append(
            check_result(
                "snapshot_planner",
                "pass" if manifests else "fail",
                "Snapshot planner generated import manifests." if manifests else "Snapshot planner returned no manifests.",
                {"planned_files": len(manifests)},
            )
        )
    except Exception as exc:
        checks.append(
            check_result(
                "snapshot_planner",
                "fail",
                "Snapshot planner failed.",
                {"error": str(exc)},
            )
        )

    status = "pass"
    if any(check["status"] == "fail" for check in checks):
        status = "fail"
    elif any(check["status"] == "warn" for check in checks):
        status = "warn"

    return {
        "snapshot": snapshot,
        "source_dir": source_dir,
        "status": status,
        "checks": checks,
        "summary": {
            "recognized_files": len(files),
            "ignored_files": len(ignored),
            "expected_files": int(expected_files),
            "total_bytes": total_bytes,
            "families": families_count,
        },
        "missing_expected_files": missing_expected,
        "ignored_files": ignored,
        "next_commands": build_next_commands(snapshot, ",".join(selected_families), limit),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preflight da base oficial da Receita para Postgres staging.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--families", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--expected-files", type=int, default=37)
    parser.add_argument("--free-bytes", type=int, default=-1)
    parser.add_argument("--disk-multiplier", type=float, default=3.0)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    families = [item.strip() for item in args.families.split(",") if item.strip()]
    report = preflight_report(
        args.snapshot,
        args.source_dir,
        families=families,
        limit=args.limit,
        expected_files=args.expected_files,
        free_bytes=None if args.free_bytes < 0 else args.free_bytes,
        disk_multiplier=args.disk_multiplier,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["status"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
