# MVP acceptance

**Status: v0.1.0 technical release package accepted on 2026-10-18.** GitHub
publication remains blocked; a live Copilot smoke test is deferred. The requested
hosted release is therefore not yet delivered. Eric reviewed concrete artifacts
and executed the checks recorded below. Eric is an AI product-owner role; this
decision cannot certify banking compliance or substitute for a bank's accountable
human review.

## Review basis

- Source: `https://github.com/NSEvent/cobol-banking-system`.
- Pinned commit: `03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4`.
- Slice: account posting, returned GL intent, standalone GL posting, and the US
  BSA/CTR path, with adjacent integration/audit evidence needed to explain gaps.
- Value criterion: a developer can inspect an object or action, find its source
  evidence, distinguish executable behavior from a comment or interpretation,
  and identify the work an Italian-bank adaptation would still require.

## Acceptance matrix

| Gate | Pass condition | Evidence to inspect | State |
| --- | --- | --- | --- |
| A1 — Source fidelity | Inputs are commit-pinned, hashes and line anchors validate, and absent integrations remain absent. | `source-lock.json`, source validator, generated evidence hashes/links, no-invented-CALL regression. | Reviewed; pass |
| A2 — Semantic model | Objects, properties, links, actions, rules, copybook fields, and control flows cover the agreed slice. | 12 objects, 98 properties, 16 links, 8 actions, 22 rules; JSON-LD and source mapping exports; `docs/ontology.md`. | Reviewed; pass |
| A3 — Interpretive precision | Observed code, comments, inferred meaning, and proposed adaptation are distinguished; ambiguities are preserved. | `docs/semiotics.md`, `docs/findings.md`, `model/ontology.json` uncertainty records. | Reviewed; pass |
| A4 — Operational truth | Returned GL intent is not described as an atomic posted journal; CTR status mutation is not described as regulator submission. | Separate GLInstruction/GL Entry objects; rules for one-sided posting and local CTR state; findings F01/F02/F08/F09. | Reviewed; pass |
| A5 — Italian alignment | BIAN / ISO 20022 / CBI / SEPA / UIF / lineage / resilience references are sourced and classified as conceptual, gap, or future work. | `docs/compliance-italy.md`; eight proposed mappings and ten references in `model/standards-crosswalk.json`; explicit US/Italy and version/profile gaps. | Reviewed; pass for conceptual alignment |
| A6 — Copilot kit | All five agents, a reusable skill, example prompts, and bounded orchestration are documented and internally consistent. | `.github/agents/`, `.github/skills/`, `.github/prompts/`, `docs/copilot.md`, `orchestration/`; 16 configuration/ledger tests. | Reviewed; pass for offline kit |
| A7 — Reproducibility | Documented commands run; automated checks cover meaningful failure cases and output determinism. | 25 extractor/model/export/crosswalk tests; 16 orchestration tests; four generated artifacts verified byte-for-byte. | Reviewed; pass |
| A8 — Demonstrated value | A source-linked example answers business questions and exposes at least one consequential integration/regulatory gap. | `docs/demo.md`, actual saved CLI/check outputs, reproducible queries, and explicit Copilot prompts; empty run template accurately labeled. | Reviewed; pass for local demonstration |
| A9 — Release hygiene | Original work is licensed, upstream provenance is retained, source redistribution is avoided, and usage/limitations are clear. | README, MIT license, third-party notice, release instructions, release file inventory, and valid local documentation links. | Reviewed; pass for package |
| A10 — Honest claims | Documentation says exactly which local checks were executed and does not claim a live Copilot run, executed COBOL behavior, or certified compliance without evidence. | README, demo labels, saved test outputs, release notes, and explicit blocked publication gate. | Reviewed; pass |

**Separate delivery gate — GitHub publication: blocked.** The requested new
repository/release has not been published. The current connector does not expose
repository or release creation, and attempted browser/CLI access to create the
missing destination is unavailable in this environment. A local commit, tag, or
downloadable package can be accepted as release-ready work; none is proof of a
hosted GitHub repository or release. This gate remains open after technical MVP
acceptance and is not waived by Eric.

## Required demonstration questions

1. What does posting a transaction change, and what does its GL result actually
   authorize a caller to do?
2. Does the source prove that both GL legs are posted atomically? Where does the
   caller's responsibility begin?
3. Which cash threshold and aggregation rules are implemented? How can one flag
   or status carry multiple meanings in the US reporting path?
4. Does `CTRFIL0 FILE` transmit a report, or change a caller-supplied record?
5. Which parts conceptually resemble BIAN/ISO 20022 concepts, and why does that
   leave Italian CBI/SEPA profile conformance and UIF suspicious-transaction
   reporting unresolved?

## Evidence record

The local review commands, from the repository root with the separately acquired
pinned source at `../upstream`, are:

```sh
python -m unittest discover -s tests -v
python -m rose validate --source ../upstream
python -m rose build --source ../upstream --output build
python -m rose build --source ../upstream --output build --check
python -m rose query 'double entry'
python orchestration/check.py orchestration/run.example.json
python -m unittest discover -s orchestration -p 'test_*.py' -v
```

Actual outcomes are recorded below. Local semantic-analysis checks are separate
from execution of the upstream COBOL programs or the GitHub Copilot service.
The coordinator also recorded a full `make check SOURCE=.upstream` execution
against the same verified source bytes in [demo-output/checks.txt](demo-output/checks.txt).

| Executed review | Observed result | Limit |
| --- | --- | --- |
| `python -m rose validate --source ../upstream` | Passed: 15 exact source files, 58 semantic records, and eight proposed standards mappings. | Static evidence and schema checks, not COBOL execution. |
| `python -m unittest discover -s tests -v` | Passed: 25 tests. | Lexical extraction, evidence/model/crosswalk invariants, failure cases, and deterministic export; no COBOL runtime. |
| `python -m rose build --source ../upstream --output build --check` | Passed: four deterministic artifacts match exact regenerated output. | Supported slice only; no whole-program equivalence claim. |
| `make demo` | Passed: all three configured queries returned annotations; no empty-query notices. | Local CLI demonstration only. |
| `python -m rose query 'double entry' --limit 2` | Returned `rule.gl_normal_side` and `rule.workflow_integration_boundaries` with absolute commit-pinned source links. | Deterministic token search over reviewed annotations, not a generated natural-language answer. |
| `python orchestration/check.py orchestration/run.example.json` | Passed: ledger shape and review invariants; template has no fabricated history. | Does not launch agents or attest source/execution truth. |
| `python -m unittest discover -s orchestration -p 'test_*.py' -v` | Passed: 16 tests. | Role configuration, evidence references, gate reopening, conflict handling, bounded iterations, append-only history, and live-transcript requirements. |
| Manual source/model review | Model and semiotic notes preserve returned GL intent, the standalone GL caller contract, operation-specific cash flags, and local-only filing/audit. | The review is bounded to the pinned slice. |
| Standards/crosswalk review | All eight crosswalk entries resolve model/reference IDs, retain proposed status, and name missing evidence. Official BIAN, EPC, UIF SOS and OGG pages were reopened to confirm the cited distinctions and review-date version statements. | Conceptual mapping only; no restricted CBI specifications, message conformance tests, or institutional compliance review. |
| Release documentation and file inventory review | README, architecture, demonstration, release instructions, license/notice, and local documentation links were inspected. Source/caches are excluded from the package inventory. | Package review precedes creation of the local release commit/tag; no remote publication or hosted Actions execution was verified. |

Review identified and resolved an initial discoverability issue: the phrase
`double entry` now matches the relevant GL annotations after the conventional
term was added without changing source semantics. Source-link formatting was
also inspected; current query output contains absolute commit-pinned GitHub URLs.

## Product-owner decision

**Accept the bounded v0.1.0 package.** The demonstrated value is a developer's
ability to move from a banking question to a precise source claim, understand
where a plausible interpretation would be false, and identify the data and
controls needed for an Italian-bank adaptation. All ten technical package gates
above pass within their stated limits. The 41 automated tests, source validation,
deterministic artifact comparison, and reviewed demonstration support this scope.

The approved cuts in [backlog.md](backlog.md) remain visible. Next actions are
to create the local release commit/tag and archive, complete `PUB-01` with a
writable GitHub repository and supported release operation, and perform the
separately documented live Copilot smoke test. Only the actual hosted repository
and release URLs can close publication; only a genuine host transcript can close
live Copilot validation.

No local test result or model mapping establishes production readiness, legal
compliance, regulator acceptance, complete banking accounting, or operational
resilience. These are product boundaries, not claims that those properties were
tested and failed.
