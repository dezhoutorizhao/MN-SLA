# MN-SLA: Matched-Neutral Safety-Label Audit

This repository contains the code and public aggregate artifacts for MN-SLA, a
matched-neutral audit protocol for measuring social-pressure sensitivity in
safety judges. The manuscript source, compiled paper PDF, and manuscript
figures are intentionally not included in this repository.

MN-SLA fixes the underlying safety case and gold label, compares
pressure-wrapped judge inputs against matched neutral controls with the same
base case, layout, and format, and performs inference over base cases rather
than rendered prompt records. The project is a protocol-bounded audit and
artifact-governance contribution. It is not an unrestricted SOTA claim, an
equal-cost comparison, a trained mitigation model, or a deployable single-pass
defense.

## Repository Contents

- `src/sycophancy_guard/`: audit construction, metrics, diagnostics, claim
  gates, projection ablations, and baseline adapters.
- `scripts/`: commands for generating aggregate audits, diagnostic analyses,
  local annotation tooling, and reproducibility assets.
- `tests/`: regression tests for the audit pipeline and fail-closed behavior.
- `artifacts/`: public aggregate outputs for inspecting the MN-SLA claim
  boundary. These are summaries, tables, and JSON reports, not raw rendered
  benchmark prompts.
- `CLAIMS_FROM_RESULTS.md` and `NOVELTY_CHECK_REPORT.md`: short public summaries
  of the supported claim boundary and novelty positioning.

## Public Artifact Policy

The repository intentionally does not publish the manuscript source, compiled
paper PDF, manuscript figures, local raw rendered prompts, model weights,
Hugging Face caches, private annotation answer keys, or internal session
recovery logs. Large and sensitive local directories such as `paper/`,
`figures/`, `data/`, `outputs/`, `models/`, `.hf_cache/`, and `third_party/`
are ignored.

The public `artifacts/` directory contains aggregate diagnostics sufficient to
inspect the paper claims without exposing local-only or sensitive records.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install -r requirements.txt
```

## Tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

The latest recorded verification for the full local project ran 162 tests
successfully. The manuscript build artifacts are kept outside the public
repository.

## Claim Boundary

Supported: a narrow, protocol-bounded MN-SLA audit claim with base-level
inference, matched neutral controls, fail-closed artifact checks, raw-gap
replication diagnostics, and strong matched-control attenuation evidence.

Not supported: broad SOTA, equal-cost or single-pass robustness, deployable
model superiority, trained PACT, residual elimination at PKU2K scale for
mean-v1, source-general robustness, completed blinded human neutral-control
validation, or replacement of the frozen 50-base primary gate by PKU2K.
