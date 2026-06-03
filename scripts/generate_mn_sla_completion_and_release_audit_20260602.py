from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "mn_sla_completion_and_release_audit_20260602"
REQUIRED_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "mn_sla_required_experiments_20260601"
    / "mn_sla_required_experiments_summary.json"
)
ARTIFACT_MANIFEST_PATH = (
    ROOT / "outputs" / "mn_sla_required_experiments_20260601" / "artifact_manifest.csv"
)
FRESH_GRID_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "fresh_neutral_template_grid_20260601"
    / "fresh_neutral_template_grid_summary.json"
)
E6_SCORE_LEVEL_SUMMARY_PATH = (
    ROOT / "outputs" / "e6_score_level_analysis_20260603" / "e6_score_level_summary.json"
)


BASELINE_CATALOG = (
    ("DynaGuard", "dynamic_policy_guard"),
    ("WildGuard", "open_moderation_guard"),
    ("ShieldLM", "open_moderation_guard"),
    ("Qwen3Guard", "probability_logit_guard"),
    ("HarmAug", "distilled_probability_guard"),
    ("BingoGuard", "open_moderation_guard"),
    ("LlamaGuard", "open_moderation_guard"),
    ("NemotronGuard", "open_moderation_guard"),
    ("ShieldGemma", "open_moderation_guard"),
    ("OpenAI Moderation API", "external_api_guard"),
    ("Perspective API", "external_api_guard"),
)


def main() -> None:
    report = generate_audit()
    write_audit(report, OUTPUT_DIR)
    print(f"Wrote MN-SLA completion/release audit to {OUTPUT_DIR}")


def generate_audit() -> dict[str, Any]:
    required_summary = _read_json(REQUIRED_SUMMARY_PATH)
    fresh_grid = _read_json(FRESH_GRID_SUMMARY_PATH)
    artifact_manifest = _read_csv(ARTIFACT_MANIFEST_PATH)
    e6_score_summary = _read_json(E6_SCORE_LEVEL_SUMMARY_PATH) if E6_SCORE_LEVEL_SUMMARY_PATH.exists() else {}
    validate_fail_closed_claims(required_summary, fresh_grid)

    requirement_status = build_requirement_status(required_summary)
    baseline_ledger = build_baseline_ledger(required_summary, artifact_manifest, e6_score_summary=e6_score_summary)
    release_policy_manifest = build_release_policy_manifest()
    release_check = build_release_check(release_policy_manifest)

    return {
        "artifact_type": "mn_sla_completion_and_release_audit",
        "created_at": "2026-06-02",
        "raw_text_emitted": False,
        "claim_boundary": {
            "supports": (
                "local completion audit, baseline inclusion/exclusion governance, "
                "and deny-by-default public-release policy over existing aggregate artifacts"
            ),
            "does_not_support": (
                "new model inference, new baseline result, deployable defense claims, "
                "expanded human IAA beyond the completed local packet, or public release of raw rendered prompts"
            ),
        },
        "fail_closed_checks": {
            "p0_1_completion_requires_passing_human_iaa_report": True,
            "wildguard_fresh_grid_positive_attenuation_rejected": True,
            "release_policy_deny_by_default": True,
        },
        "requirement_status": requirement_status,
        "baseline_ledger": baseline_ledger,
        "release_policy_manifest": release_policy_manifest,
        "release_check": release_check,
        "source_artifacts": {
            "required_summary": _rel(REQUIRED_SUMMARY_PATH),
            "artifact_manifest": _rel(ARTIFACT_MANIFEST_PATH),
            "fresh_grid_summary": _rel(FRESH_GRID_SUMMARY_PATH),
            "e6_score_level_summary": _rel(E6_SCORE_LEVEL_SUMMARY_PATH),
        },
    }


def validate_fail_closed_claims(required_summary: dict[str, Any], fresh_grid: dict[str, Any]) -> None:
    p0_1 = _requirement(required_summary, "P0-1")
    p0_1_status = str(p0_1.get("status") or "").strip().lower()
    blockers = required_summary.get("blockers", [])
    has_p0_1_blocker = any(_is_p0_1_blocker(blocker) for blocker in blockers)
    if p0_1_status == "blocked":
        if _is_positive_completion_claim(p0_1.get("claim")):
            raise ValueError("P0-1 claim reads as completed, but independent human annotations are missing")
        _reject_p0_1_completion_text(required_summary)
        if not has_p0_1_blocker:
            raise ValueError("Required summary must retain an explicit P0-1 independent-human-IAA blocker")
    elif p0_1_status in {"completed", "completed_human_iaa"}:
        if has_p0_1_blocker:
            raise ValueError("P0-1 is marked completed but still has an independent-human-IAA blocker")
        human_iaa = required_summary.get("human_iaa_summary", {})
        if human_iaa.get("passed") is not True:
            raise ValueError("P0-1 completion requires human_iaa_summary.passed == True")
        evidence = str(p0_1.get("evidence_path") or human_iaa.get("evidence_path") or "")
        if "human_validation_overlap" not in evidence or "fail_closed_report.json" not in evidence:
            raise ValueError("P0-1 completion must point to the human IAA fail_closed_report.json")
    else:
        raise ValueError(f"P0-1 has unsupported status={p0_1_status!r}")

    allowed_claim = str(fresh_grid.get("claim_safety", {}).get("allowed_claim") or "").lower()
    forbidden_phrases = (
        "wildguard preserves positive attenuation",
        "wildguard shows positive attenuation",
        "all guards show positive attenuation",
    )
    if any(phrase in allowed_claim for phrase in forbidden_phrases):
        raise ValueError("Fresh-grid claim overstates WildGuard positive attenuation")

    wildguard_rows = [
        row
        for row in fresh_grid.get("rows", [])
        if str(row.get("guard") or "").strip().lower() == "wildguard"
    ]
    if not wildguard_rows:
        raise ValueError("Fresh-grid summary is missing the WildGuard row")
    for row in wildguard_rows:
        positive_rate = _required_float(row, "attenuation_positive_rate")
        median_attenuation = _required_float(row, "median_attenuation_mean")
        if positive_rate > 0.0 or median_attenuation > 0.0:
            raise ValueError(
                "WildGuard fresh-grid attenuation must not be treated as positive "
                f"(positive_rate={positive_rate}, median={median_attenuation})"
            )


def build_requirement_status(required_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in required_summary.get("requirement_status", []):
        requirement_id = str(row.get("id") or "")
        status = str(row.get("status") or "")
        rows.append(
            {
                "id": requirement_id,
                "name": row.get("name"),
                "status": status,
                "status_class": _status_class(requirement_id, status),
                "evidence_path": row.get("evidence_path"),
                "claim": row.get("claim"),
            }
        )
    return rows


def build_baseline_ledger(
    required_summary: dict[str, Any],
    artifact_manifest: list[dict[str, str]],
    e6_score_summary: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    manifest_by_guard: dict[str, list[dict[str, str]]] = {}
    for row in artifact_manifest:
        guard = str(row.get("guard") or "").strip()
        if guard:
            manifest_by_guard.setdefault(_key(guard), []).append(row)

    probability_guards = {
        _key(guard)
        for guard in required_summary.get("probability_threshold_summary", {}).get("available_probability_guards", [])
    }
    harmaug_score_paths = _harmaug_external_score_paths(e6_score_summary or {})

    rows = []
    for baseline, category in BASELINE_CATALOG:
        manifest_rows = manifest_by_guard.get(_key(baseline), [])
        existing_manifest_rows = [row for row in manifest_rows if _manifest_row_exists(row)]
        status = _baseline_status(
            baseline,
            existing_manifest_rows,
            probability_guards,
            harmaug_score_external_completed=bool(harmaug_score_paths),
        )
        evidence_paths = sorted({row.get("path", "") for row in existing_manifest_rows if row.get("path")})
        artifact_roles = sorted({row.get("role", "") for row in existing_manifest_rows if row.get("role")})
        if baseline == "HarmAug" and harmaug_score_paths:
            evidence_paths = sorted({*evidence_paths, *harmaug_score_paths})
            artifact_roles = sorted({*artifact_roles, "external_score_probability_pku200_beavertails200"})
        fallback = _baseline_fallback_evidence(baseline)
        rows.append(
            {
                "baseline": baseline,
                "category": category,
                "status": status,
                "evidence_paths": ";".join(evidence_paths) if evidence_paths else fallback,
                "artifact_roles": ";".join(artifact_roles),
                "claim_boundary": _baseline_claim_boundary(status),
            }
        )
    return rows


def _manifest_row_exists(row: dict[str, Any]) -> bool:
    value = row.get("exists")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def build_release_policy_manifest() -> list[dict[str, str]]:
    return [
        _policy("**/*", "deny_by_default", "Only explicit aggregate allowlist entries may be released.", "unknown"),
        _policy("artifacts/**/*", "allow_aggregate", "Curated public aggregate artifact mirror.", "low"),
        _policy(
            "outputs/mn_sla_completion_and_release_audit_20260602/*",
            "allow_aggregate",
            "Generated governance audit outputs.",
            "low",
        ),
        _policy(
            "outputs/mn_sla_required_experiments_20260601/*.md",
            "allow_aggregate_after_check",
            "Aggregate experiment summaries; re-scan before packaging.",
            "low",
        ),
        _policy(
            "outputs/mn_sla_required_experiments_20260601/*.csv",
            "allow_aggregate_after_check",
            "Aggregate ledgers only; reject raw-text columns.",
            "low_to_medium",
        ),
        _policy(
            "outputs/fresh_neutral_template_grid_20260601/*summary*",
            "allow_aggregate_after_check",
            "Fresh holdout diagnostic summaries without raw prompt text.",
            "low",
        ),
        _policy("data/**/*", "deny", "Local source data may contain raw benchmark text.", "high"),
        _policy(
            "outputs/**/*.jsonl",
            "deny_unless_separately_allowlisted",
            "Prediction ledgers and annotation packets may contain raw text or model raw output.",
            "high",
        ),
        _policy("outputs/**/*SENSITIVE*", "deny", "Local-only sensitive annotation artifacts.", "high"),
        _policy("outputs/**/private_answer_key*", "deny", "Private annotation answer keys.", "medium"),
        _policy("third_party/**/*", "deny", "External repositories are not release artifacts.", "unknown"),
        _policy("models/**/*", "deny", "Model weights and caches are outside the artifact release.", "unknown"),
        _policy(".hf_cache/**/*", "deny", "Local Hugging Face cache must not be packaged.", "unknown"),
        _policy("paper/**/*", "deny", "Manuscript source/build artifacts are not part of this release.", "medium"),
    ]


def build_release_check(release_policy_manifest: list[dict[str, str]]) -> dict[str, Any]:
    deny_entries = [row for row in release_policy_manifest if row["decision"].startswith("deny")]
    allow_entries = [row for row in release_policy_manifest if row["decision"].startswith("allow")]
    return {
        "status": "policy_defined_not_packaged",
        "deny_by_default": True,
        "n_allow_entries": len(allow_entries),
        "n_deny_entries": len(deny_entries),
        "required_manual_gate": (
            "Before packaging, run a path and field-name scan over the candidate release tree; "
            "do not include raw rendered prompts, local-only annotation packets, private keys, "
            "model caches, or unreviewed JSONL prediction ledgers."
        ),
    }


def write_audit(report: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "audit.md").write_text(render_markdown(report), encoding="utf-8")
    (output / "release_check.md").write_text(render_release_check_markdown(report), encoding="utf-8")
    _write_csv(output / "baseline_ledger.csv", report["baseline_ledger"], _baseline_fields())
    _write_csv(output / "release_policy_manifest.csv", report["release_policy_manifest"], _release_policy_fields())


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MN-SLA Completion And Release Audit",
        "",
        "This report is aggregate-only and emits no raw rendered prompt text.",
        "",
        "## Claim Boundary",
        "",
        f"- Supports: {report['claim_boundary']['supports']}",
        f"- Does not support: {report['claim_boundary']['does_not_support']}",
        "",
        "## P0 Requirement Status",
        "",
        "| ID | Status | Status class | Claim |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["requirement_status"]:
        lines.append(f"| {row['id']} | {row['status']} | {row['status_class']} | {_md(row.get('claim'))} |")

    lines.extend(
        [
            "",
            "## P1 Baseline Ledger",
            "",
            "| Baseline | Category | Status | Claim boundary |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["baseline_ledger"]:
        lines.append(
            f"| {row['baseline']} | {row['category']} | {row['status']} | {_md(row['claim_boundary'])} |"
        )

    lines.extend(
        [
            "",
            "## Release Policy",
            "",
            "| Path pattern | Decision | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in report["release_policy_manifest"]:
        lines.append(f"| `{row['path_pattern']}` | {row['decision']} | {_md(row['reason'])} |")

    lines.extend(
        [
            "",
            "## Fail-closed Checks",
            "",
            "- P0-1 completion is accepted only when backed by a passing human IAA fail-closed report.",
            "- WildGuard fresh-grid positive attenuation claims are rejected.",
            "- Raw prompt, source-data, private-key, and model-cache paths are deny-by-default.",
            "",
        ]
    )
    return "\n".join(lines)


def render_release_check_markdown(report: dict[str, Any]) -> str:
    check = report["release_check"]
    return "\n".join(
        [
            "# MN-SLA Release Check",
            "",
            "This is a policy check, not a packaged release.",
            "",
            f"- status: `{check['status']}`",
            f"- deny_by_default: `{check['deny_by_default']}`",
            f"- allow entries: `{check['n_allow_entries']}`",
            f"- deny entries: `{check['n_deny_entries']}`",
            f"- required manual gate: {check['required_manual_gate']}",
            "",
        ]
    )


def _baseline_status(
    baseline: str,
    manifest_rows: list[dict[str, str]],
    probability_guards: set[str],
    *,
    harmaug_score_external_completed: bool = False,
) -> str:
    roles = " ".join(str(row.get("role") or "").lower() for row in manifest_rows)
    if baseline in {"DynaGuard", "WildGuard"} and (
        "primary_scale_gate" in roles or "confirmatory_external_open_dataset_replication" in roles
    ):
        return "evaluated"
    if baseline == "Qwen3Guard" and "external_500base_score_logit_extension" in roles:
        return "evaluated_score_logit"
    if baseline == "HarmAug" and harmaug_score_external_completed:
        return "evaluated_score_probability"
    if baseline in {"BingoGuard", "LlamaGuard", "NemotronGuard", "ShieldGemma"} and (
        "confirmatory_external_open_dataset_replication" in roles
    ):
        return "evaluated"
    if _key(baseline) in probability_guards:
        return "diagnostic"
    if baseline == "ShieldLM" and manifest_rows:
        return "supplementary_only"
    if baseline in {"BingoGuard", "LlamaGuard", "NemotronGuard", "ShieldGemma"} and _baseline_has_adapter(baseline):
        return "runner_available_no_formal_run"
    if baseline in {"OpenAI Moderation API", "Perspective API"}:
        return "excluded"
    return "no_formal_run"


def _baseline_has_adapter(baseline: str) -> bool:
    paths = {
        "BingoGuard": ROOT / "src" / "sycophancy_guard" / "run_bingoguard.py",
        "LlamaGuard": ROOT / "scripts" / "run_llamaguard.py",
        "NemotronGuard": ROOT / "scripts" / "run_nemotron_guard.py",
        "ShieldGemma": ROOT / "src" / "sycophancy_guard" / "run_shieldgemma.py",
    }
    return paths.get(baseline, Path("__missing__")).exists()


def _baseline_fallback_evidence(baseline: str) -> str:
    paths = {
        "BingoGuard": "outputs/bingoguard_adapter_audit_20260429;src/sycophancy_guard/run_bingoguard.py",
        "HarmAug": "outputs/harmaug_guard_contract_smoke_20260429",
        "LlamaGuard": "scripts/run_llamaguard.py",
        "NemotronGuard": "scripts/run_nemotron_guard.py",
        "ShieldGemma": "src/sycophancy_guard/run_shieldgemma.py",
    }
    return paths.get(baseline, "")


def _baseline_claim_boundary(status: str) -> str:
    if status == "evaluated":
        return "Existing aggregate artifacts may be cited only within their declared diagnostic/confirmatory scope."
    if status == "evaluated_score_logit":
        return "Score/logit baseline evaluated on PKU200 and BeaverTails external ledgers; not broad guard-family certification."
    if status == "evaluated_score_probability":
        return "Score/probability baseline evaluated on PKU200 and BeaverTails external ledgers; not broad guard-family certification."
    if status == "diagnostic":
        return "Probability/logit or supplementary diagnostic only; not broad baseline-family completion."
    if status == "supplementary_only":
        return "Supplementary contract evidence only; not selected-main proof."
    if status == "runner_available_no_formal_run":
        return "Runner or adapter file exists, but no current formal required-experiment result is counted."
    if status == "no_formal_run":
        return "No local formal prediction ledger; do not count as completed baseline expansion."
    return "Excluded from local P1 evidence without a separate approved protocol."


def _harmaug_external_score_paths(e6_score_summary: dict[str, Any]) -> list[str]:
    if e6_score_summary.get("status") != "completed_two_score_guard_families_with_external":
        return []
    required_datasets = {"PKU200", "BeaverTails200"}
    paths_by_dataset: dict[str, str] = {}
    for run in e6_score_summary.get("runs", []):
        if str(run.get("guard") or "") != "HarmAug":
            continue
        dataset = str(run.get("dataset") or "")
        if dataset not in required_datasets:
            continue
        if run.get("exists") is not True or run.get("status") != "completed_score_level_analysis":
            continue
        path = str(run.get("path") or "")
        if path:
            paths_by_dataset[dataset] = path
    if set(paths_by_dataset) != required_datasets:
        return []
    return [paths_by_dataset[dataset] for dataset in sorted(required_datasets)]


def _status_class(requirement_id: str, status: str) -> str:
    if requirement_id == "P0-1":
        if status in {"completed", "completed_human_iaa"}:
            return "local_completed_human_iaa"
        return "blocked_external_dependency"
    if status.startswith("completed"):
        return "local_completed_diagnostic"
    return "local_status_review_required"


def _is_p0_1_blocker(blocker: dict[str, Any]) -> bool:
    requirement = str(blocker.get("requirement") or "").lower()
    status = str(blocker.get("status") or "").lower()
    is_p0_1 = "p0-1" in requirement or "human iaa" in requirement or "independent human" in requirement
    return is_p0_1 and "blocked" in status


def _is_positive_completion_claim(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    positive_markers = ("completed", "passed", "done", "validated")
    if not any(marker in text for marker in positive_markers):
        return False
    for contrast in (" but ", " however ", "; however", ", however"):
        if contrast in text:
            suffix = text.split(contrast, 1)[1]
            if any(marker in suffix for marker in positive_markers):
                return True
    negative_markers = (
        "not completed",
        "do not claim",
        "do not prove",
        "does not prove",
        "not prove",
        "does not support",
        "do not support",
        "cannot support",
        "not human iaa",
        "not human validation",
        "missing",
        "blocked",
        "without independent",
    )
    if any(marker in text for marker in negative_markers):
        return False
    return True


def _reject_p0_1_completion_text(value: Any) -> None:
    for path, text in _walk_strings(value):
        path_lowered = path.lower()
        if path_lowered.endswith("evidence_path"):
            continue
        lowered = text.lower()
        is_p0_1_related = any(
            marker in lowered
            for marker in (
                "p0-1",
                "human iaa",
                "independent human",
                "overlapping human",
                "human validation",
            )
        ) or "p0-1" in path_lowered or "human" in path_lowered or "iaa" in path_lowered
        if is_p0_1_related and _is_positive_completion_claim(text):
            raise ValueError(f"P0-1 completion-like wording found at {path}: {text!r}")


def _walk_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        rows: list[tuple[str, str]] = []
        for key, item in value.items():
            rows.extend(_walk_strings(item, f"{path}.{key}"))
        return rows
    if isinstance(value, list):
        rows = []
        for index, item in enumerate(value):
            rows.extend(_walk_strings(item, f"{path}[{index}]"))
        return rows
    if isinstance(value, str):
        return [(path, value)]
    return []


def _requirement(required_summary: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for row in required_summary.get("requirement_status", []):
        if row.get("id") == requirement_id:
            return row
    raise ValueError(f"Missing requirement status for {requirement_id}")


def _policy(path_pattern: str, decision: str, reason: str, raw_text_risk: str) -> dict[str, str]:
    return {
        "path_pattern": path_pattern,
        "decision": decision,
        "reason": reason,
        "raw_text_risk": raw_text_risk,
    }


def _read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def _baseline_fields() -> tuple[str, ...]:
    return (
        "baseline",
        "category",
        "status",
        "evidence_paths",
        "artifact_roles",
        "claim_boundary",
    )


def _release_policy_fields() -> tuple[str, ...]:
    return ("path_pattern", "decision", "reason", "raw_text_risk")


def _float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _required_float(row: dict[str, Any], field: str) -> float:
    if field not in row or row[field] in (None, ""):
        raise ValueError(f"Fresh-grid WildGuard row is missing required field: {field}")
    return float(row[field])


def _key(value: str) -> str:
    return value.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def _rel(path: str | Path) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
