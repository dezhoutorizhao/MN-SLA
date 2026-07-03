#!/usr/bin/env sh
set -eu

usage() {
  echo "usage: tools/verify_paper_audits.sh PAPER_DIR [--assurance submission|draft]" >&2
}

if [ "$#" -lt 1 ]; then
  usage
  exit 2
fi

paper_dir=$1
shift
assurance="draft"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --assurance)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      assurance=$2
      shift 2
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if command -v python3 >/dev/null 2>&1; then
  python_cmd=python3
elif command -v python >/dev/null 2>&1; then
  python_cmd=python
else
  echo "error: Python interpreter not found; expected python3 or python in PATH" >&2
  exit 127
fi

"$python_cmd" - "$paper_dir" "$assurance" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

paper_dir = Path(sys.argv[1]).resolve()
assurance = sys.argv[2]
required = [
    ("PROOF_AUDIT.json", {"PASS", "WARN", "NOT_APPLICABLE"}),
    ("PAPER_CLAIM_AUDIT.json", {"PASS", "WARN", "NOT_APPLICABLE"}),
    ("CITATION_AUDIT.json", {"PASS", "WARN", "NOT_APPLICABLE"}),
]
blocking = {"FAIL", "BLOCKED", "ERROR"}
report = {
    "assurance": assurance,
    "paper_dir": str(paper_dir),
    "audits": [],
    "status": "OK",
    "issues": [],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def windows_drive_path_to_posix(key: str):
    if os.name == "nt" or len(key) < 3:
        return None
    if key[1] != ":" or not key[0].isalpha() or key[2] not in {"/", "\\"}:
        return None
    drive = key[0].lower()
    rest = key[3:].replace("\\", "/")
    return Path("/mnt") / drive / rest


def resolve_hash_path(key: str) -> Path:
    p = Path(key)
    if p.is_absolute():
        return p
    wsl_path = windows_drive_path_to_posix(key)
    if wsl_path is not None:
        return wsl_path
    return paper_dir / p


def add_issue(message: str) -> None:
    report["issues"].append(message)
    report["status"] = "FAIL"


for filename, allowed_nonblocking in required:
    path = paper_dir / filename
    entry = {"file": filename, "exists": path.is_file()}
    report["audits"].append(entry)
    if not path.is_file():
        add_issue(f"{filename}: missing mandatory audit JSON")
        continue
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        add_issue(f"{filename}: invalid JSON: {exc}")
        continue

    verdict = data.get("verdict")
    entry["verdict"] = verdict
    if verdict in blocking:
        add_issue(f"{filename}: blocking verdict {verdict}")
    elif assurance == "submission" and verdict not in allowed_nonblocking:
        add_issue(f"{filename}: unsupported verdict {verdict!r}")

    hashes = data.get("audited_input_hashes")
    if not isinstance(hashes, dict) or not hashes:
        add_issue(f"{filename}: missing nonempty audited_input_hashes object")
        continue

    stale = []
    for key, expected in hashes.items():
        if not isinstance(expected, str):
            stale.append(f"{key}: hash is not a string")
            continue
        expected = expected.removeprefix("sha256:")
        if len(expected) != 64:
            stale.append(f"{key}: hash is not sha256")
            continue
        source = resolve_hash_path(key)
        if not source.is_file():
            stale.append(f"{key}: source missing")
            continue
        actual = sha256(source)
        if actual.lower() != expected.lower():
            stale.append(f"{key}: stale")
    entry["stale_hashes"] = stale
    for item in stale:
        add_issue(f"{filename}: {item}")

out_dir = paper_dir / ".aris"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "audit-verifier-report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

if report["issues"]:
    print(json.dumps(report, indent=2, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
print(json.dumps(report, indent=2, ensure_ascii=False))
PY
