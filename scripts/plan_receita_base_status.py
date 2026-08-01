import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.plan_receita_staging_preflight import preflight_report


def status_from_preflight(preflight):
    if preflight.get("status") == "fail":
        failed = [check for check in preflight.get("checks", []) if check.get("status") == "fail"]
        if any(check.get("name") == "disk_capacity" for check in failed):
            return "blocked_disk"
        return "blocked_preflight"
    if preflight.get("status") == "warn":
        return "ready_with_warnings"
    return "ready_for_smoke"


def build_base_status(snapshot, source_dir, free_bytes=None, disk_multiplier=3.0):
    preflight = preflight_report(
        snapshot,
        source_dir,
        free_bytes=free_bytes,
        disk_multiplier=disk_multiplier,
    )
    disk_check = next((check for check in preflight.get("checks", []) if check.get("name") == "disk_capacity"), None)
    smoke_counts_command = (
        "powershell -NoProfile -ExecutionPolicy Bypass -File "
        "scripts\\check_receita_staging_counts.ps1 -Snapshot %s -Families cnaes,municipios,naturezas -RequireData"
    ) % snapshot
    full_counts_command = (
        "powershell -NoProfile -ExecutionPolicy Bypass -File "
        "scripts\\check_receita_staging_counts.ps1 -Snapshot %s -RequireData"
    ) % snapshot
    return {
        "snapshot": snapshot,
        "source_dir": os.path.abspath(source_dir),
        "status": status_from_preflight(preflight),
        "preflight": {
            "status": preflight.get("status"),
            "recognized_files": preflight.get("summary", {}).get("recognized_files", 0),
            "total_bytes": preflight.get("summary", {}).get("total_bytes", 0),
            "missing_expected_files": preflight.get("missing_expected_files", []),
            "disk_capacity": disk_check,
        },
        "commands": {
            "preflight": (
                "powershell -NoProfile -ExecutionPolicy Bypass -File "
                "scripts\\check_receita_staging_preflight.ps1 -Snapshot %s"
            )
            % snapshot,
            "smoke_import": preflight.get("next_commands", {}).get("smoke_import", ""),
            "full_import": preflight.get("next_commands", {}).get("snapshot_import", ""),
            "smoke_counts": smoke_counts_command,
            "full_counts": full_counts_command,
        },
        "next_gate": next_gate(preflight),
    }


def next_gate(preflight):
    disk_check = next((check for check in preflight.get("checks", []) if check.get("name") == "disk_capacity"), None)
    if disk_check and disk_check.get("status") == "fail":
        return {
            "key": "disk_capacity",
            "status": "blocked",
            "message": "Provisionar espaço suficiente para a carga completa e repetir o preflight.",
            "details": disk_check.get("details", {}),
        }
    if preflight.get("status") == "fail":
        return {
            "key": "preflight",
            "status": "blocked",
            "message": "Corrigir checks com falha no preflight.",
            "details": {},
        }
    return {
        "key": "full_import",
        "status": "ready",
        "message": "Executar importação completa e validar contagens.",
        "details": {},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera relatório consolidado da base Receita/Postgres.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--free-bytes", type=int, default=-1)
    parser.add_argument("--disk-multiplier", type=float, default=3.0)
    args = parser.parse_args(argv)
    report = build_base_status(
        args.snapshot,
        args.source_dir,
        free_bytes=None if args.free_bytes < 0 else args.free_bytes,
        disk_multiplier=args.disk_multiplier,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
