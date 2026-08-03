"""Drop and recreate indexes on the large Receita raw tables around a bulk load.

Maintaining GIN trigram and btree indexes row-by-row while inserting tens of
millions of rows is far slower than building the index once after the data
is loaded. The index definitions are parsed directly from the staging
migration file so there is a single source of truth for the DDL instead of
a second hardcoded copy that could drift out of sync.
"""

import argparse
import json
import os
import re
import sys

MIGRATION_PATH = os.path.join(
    "infra", "postgres", "migrations", "20260801190000_create_receita_staging_raw_tables.sql"
)

BULK_LOAD_TABLES = frozenset({"empresas_raw", "estabelecimentos_raw", "socios_raw"})

INDEX_LINE_RE = re.compile(
    r"^CREATE INDEX IF NOT EXISTS (?P<name>\w+) ON receita_staging\.(?P<table>\w+)"
)


def parse_bulk_load_indexes(migration_path=MIGRATION_PATH, tables=BULK_LOAD_TABLES):
    tables = set(tables)
    indexes = []
    with open(migration_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            match = INDEX_LINE_RE.match(stripped)
            if not match:
                continue
            if match.group("table") not in tables:
                continue
            indexes.append(
                {
                    "name": match.group("name"),
                    "table": match.group("table"),
                    "create_sql": stripped,
                }
            )
    return indexes


def drop_sql(indexes):
    return "\n".join(
        "DROP INDEX IF EXISTS receita_staging.%s;" % index["name"] for index in indexes
    )


def create_sql(indexes):
    return "\n".join(index["create_sql"] for index in indexes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["drop", "create", "list"])
    parser.add_argument("--migration-path", default=MIGRATION_PATH)
    parser.add_argument(
        "--tables",
        default=",".join(sorted(BULK_LOAD_TABLES)),
        help="Comma-separated table names to scope the index toggle to.",
    )
    args = parser.parse_args()

    tables = {name.strip() for name in args.tables.split(",") if name.strip()}
    indexes = parse_bulk_load_indexes(migration_path=args.migration_path, tables=tables)

    if args.action == "list":
        print(json.dumps(indexes))
    elif args.action == "drop":
        print(drop_sql(indexes))
    elif args.action == "create":
        print(create_sql(indexes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
