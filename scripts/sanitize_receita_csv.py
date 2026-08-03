"""Remove embedded NUL bytes from an extracted Receita raw file.

Official Receita Federal exports are delimited text in LATIN1, but some
published files contain stray 0x00 bytes inside field values. PostgreSQL's
``text`` type rejects embedded NUL bytes under any encoding, so the byte
must be stripped before ``COPY`` runs. Deleting the byte does not shift
delimiters or line breaks, since only the corrupt byte itself is removed.
"""

import json
import os
import sys
import tempfile

CHUNK_SIZE = 8 * 1024 * 1024


def sanitize(path: str) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    has_null = False
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            if b"\x00" in chunk:
                has_null = True
                break

    if not has_null:
        return {"path": path, "sanitized": False, "removed_bytes": 0}

    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".sanitize-", dir=directory)
    removed = 0
    try:
        with open(path, "rb") as src, os.fdopen(fd, "wb") as dst:
            while True:
                chunk = src.read(CHUNK_SIZE)
                if not chunk:
                    break
                cleaned = chunk.replace(b"\x00", b"")
                removed += len(chunk) - len(cleaned)
                dst.write(cleaned)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return {"path": path, "sanitized": True, "removed_bytes": removed}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: sanitize_receita_csv.py <path>", file=sys.stderr)
        return 2

    result = sanitize(sys.argv[1])
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
