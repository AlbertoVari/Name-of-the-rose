# The Name of the Rose

**An evidence-linked semantic layer over COBOL banking logic, with five GitHub Copilot agents.**

Translate what the code actually says into objects, relationships, actions and
business rules. Keep observed behavior, interpretation and proposed modernization
separate. Start with transaction posting, GL accounting and the US CTR path in
[VAULT-CBS](https://github.com/NSEvent/cobol-banking-system), pinned at
`03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4`.

**v0.1.0 POC:** 12 objects, 98 properties, 16 links, 8 descriptive actions,
22 rules, 15 source files and 5 Copilot profiles. This is an exploration and
documentation tool; it does not execute financial actions or certify compliance.
The GitHub workflow publishes v0.1.0 only after validation passes on main.
A live Copilot smoke test remains a separate delivery gate.

## Try it in two minutes

Use Python 3.10+ from this repository root. No runtime dependencies, API key,
database or package installation is required for the Python commands.

```sh
python3 -m rose query 'double entry'
python3 -m rose query 'CTR'
python3 -m rose query 'ACCT-AVAIL-BAL'
```

Queries search reviewed annotations and return pinned source links. They work
offline and do not invent a natural-language answer. Read the
[worked demonstration](docs/demo.md) for the questions to ask Copilot next.

To reproduce extraction and validation, acquire the locked source separately:

```sh
python3 scripts/fetch_source.py --dest .upstream
python3 -m rose validate --source .upstream
python3 -m rose build --source .upstream --output build --check
make test
```

Network-restricted environment with an existing checkout:

```sh
python3 scripts/fetch_source.py --dest .upstream --from-checkout ../upstream
```

The downloader refuses mismatched source bytes. To intentionally regenerate
exports after a reviewed model change, omit `--check`, inspect the diff and rerun
the checks. The selected source is not bundled: the inspected upstream commit
has no license file. See [NOTICE.md](NOTICE.md).

## Ask the agents

Open this repository in a Copilot-enabled IDE and select a custom agent.

| Agent | Responsibility | First useful question |
| --- | --- | --- |
| Umberto | Semiotic reading and ambiguity | Which meanings of “posted” and “filed” are justified by executable code? |
| Peter | Operational ontology | Map Account, Transaction, GL Instruction and Cash Assessment with evidence. |
| Satya | Bounded collaboration | Run a review cycle using the shared ledger; state which delegations actually ran. |
| Boris | Extraction, checks and implementation | Validate the source pin and explain unsupported parser constructs. |
| Eric | Scope and acceptance | Review the evidence and Italian-alignment gaps before accepting a change. |

Profiles live in `.github/agents/`; a reusable trace skill and three prompt files
are included. Automatic delegation depends on the Copilot host. Manual profile
selection and context packets provide a portable fallback. Follow the
[Copilot guide](docs/copilot.md) and [workflow](orchestration/workflow.md).
An agent instruction file by itself does not launch a multi-agent process.

## What the slice reveals

- `TXNPOST0` returns a GL instruction; it does not call `GLPOST0`.
- `GLPOST0` changes one supplied account per POST call. Double-entry commitment
  and complete-ledger reconciliation remain caller responsibilities.
- The CTR assessment uses customer/day directional aggregates and a strict
  greater-than comparison. Its meaning must not be replaced by an Italian rule.
- `CTRFIL0 FILE` changes local record state; it does not transmit a regulatory
  report. `AUDTLOG0` similarly prepares a record without durable logging.

These are static findings with pinned evidence, not executed COBOL test results.
The [findings register](docs/findings.md) includes reversal mutation, status
ambiguities, absent currency and incomplete integration boundaries.

## Deliverables

| Path | Purpose |
| --- | --- |
| `model/ontology.json` | Reviewed ontology and rule annotations |
| `model/standards-crosswalk.json` | BIAN/ISO/CBI/SEPA/UIF/lineage/resilience proposals and gaps |
| `build/ontology.jsonld` | Portable semantic graph export |
| `build/mappings.csv`, `build/mappings.md` | Source-to-model links with excerpt hashes |
| `build/evidence.json` | Lexical copybook, paragraph, COPY/CALL/PERFORM index |
| `source-lock.json` | Immutable upstream pin and exact file hashes |
| `.github/agents/`, `.github/skills/`, `.github/prompts/` | Copilot entry points |
| `orchestration/` | Shared context, run schema, gate checker and tests |
| `docs/acceptance.md`, `docs/backlog.md` | Review outcomes and next increments |

Read [architecture](docs/architecture.md), [ontology](docs/ontology.md),
[semiotics](docs/semiotics.md) and [Italian alignment](docs/compliance-italy.md).
The latter cites primary institutional sources and preserves the distinction
between US CTR, Italian SOS and OGG. Restricted CBI profiles were not accessed;
no ISO/CBI/SEPA schema conformance is claimed.

## Verification and release

`make check SOURCE=.upstream` runs tests, validates source/model references and
checks deterministic artifacts. GitHub Actions is configured to repeat these
checks against the pinned upstream commit; a configured workflow is not a claim
of a successful hosted run. The extractor is lexical, not a compiler or complete
control-flow analyzer. No COBOL execution or live Copilot session is asserted.

See [release instructions](RELEASING.md), [release notes](CHANGELOG.md) and the
[acceptance record](docs/acceptance.md) for exact completion boundaries.

MIT for this project's original materials; third-party rights remain separate.
