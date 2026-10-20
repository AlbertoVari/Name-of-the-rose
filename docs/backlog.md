# Product backlog

The first release helps a developer answer a concrete question: **what does this
COBOL slice actually mean, where is that meaning evidenced, and what remains to
be designed before an Italian bank could use it?** The product is a source-linked
interpretive layer and a Copilot collaboration kit. It is not a replacement core
banking engine or a regulatory reporting service.

## Accepted scope

The MVP follows `TXNPOST0` account posting and the GL instruction it returns;
examines `GLPOST0` as a separately invoked, one-account-at-a-time operation; and
models the `BSACTRO` / `CTRFIL0` US cash-reporting path. Associated copybooks and
the `EODPROC0` / `AUDTLOG0` integration context establish where a tempting
end-to-end interpretation is unsupported. Source evidence is pinned to commit
`03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4` of `NSEvent/cobol-banking-system`.

The scope includes objects, properties, links, actions, explicit rules, control
flow, alternative readings, uncertainty records, conceptual standards mappings,
five Copilot roles, deterministic local checks, and an evidence-based example.
All code and model outputs describe source behavior without changing that source.

## Release priorities

| ID | Priority | Outcome and business value | Owner | Completion gate |
| --- | --- | --- | --- | --- |
| MVP-01 | P0 | A pinned input manifest makes source claims reviewable and detects changed input. | Boris / coordinator | Hash and source-anchor validation pass; no upstream source is bundled. |
| MVP-02 | P0 | Banking nouns and verbs form an operational model a developer can inspect. | Peter | Objects, properties, links, actions, and rule mappings resolve to evidence; inferred relations are labeled. |
| MVP-03 | P0 | Competing meanings and control-flow gaps prevent confident but false modernization assumptions. | Umberto | Model explains returned GL intent versus posting, one-sided GL mutation, and local CTR lifecycle versus external filing. |
| MVP-04 | P0 | A developer can reproduce extraction and trace a question to a source location. | Boris | Documented CLI commands and automated tests run successfully on the pinned slice. |
| MVP-05 | P0 | The five named Copilot roles exchange bounded evidence packets and produce a reviewed result. | Satya | Agent/skill instructions, orchestration contract, example packet, and gate validation are present and coherent. |
| MVP-06 | P0 | Italian-bank reviewers see conceptual relevance and concrete implementation gaps. | Coordinator / Eric | BIAN, ISO 20022, CBI, SEPA, UIF/SOS, audit lineage, and resilience appear with sources, assumptions, and status. |
| MVP-07 | P0 | A clean checkout has a useful first experience and a releasable package. | Coordinator / Eric | README, license/third-party notice, demo, limitations, and acceptance evidence are complete. |
| MVP-08 | P0 | Release claims accurately reflect the work performed. | Eric | Local checks are distinguished from COBOL execution, live Copilot execution, and human regulatory approval. |

P0 is the release gate. A missing P0 outcome blocks the MVP; a disclosed product
limitation in the table below does not itself block an interpretive POC.

## GitHub delivery gate

`PUB-01` remains required: publish the reviewed project to a GitHub repository
and create a discoverable versioned release. Local package acceptance does not
satisfy this delivery gate. Publication is currently blocked by the available
environment: the connected GitHub interface exposes neither repository creation
nor release creation, and browser/CLI access to create the missing destination
is unavailable. An initialized writable repository would enable source delivery
through the connector; release publication additionally requires a supported
release operation. This is a delivery blocker, not an approved scope cut.

## Approved scope cuts

| Deferred capability | Reason for the cut | MVP treatment |
| --- | --- | --- |
| A complete COBOL compiler, parser, or whole-bank knowledge graph | A bounded extractor and curated model can answer the selected questions sooner. | Supported constructs and coverage boundaries are documented. |
| A live autonomous multi-agent service or a verified live Copilot run | Installation and platform execution are separate from deterministic offline artifact validation. | Runnable instructions, role handoffs, a validated example, and an honest demonstration label. |
| Automated posting, persistence, payment transmission, or regulatory filing | The POC explains the code; it must not imply missing production behavior. | Model actions describe observed mutations and explicitly identify missing integrations. |
| A full ISO 20022 / CBI / SEPA message implementation or certification | Conceptual correspondence does not establish message-profile conformance. | Version/profile selection and field-level validation remain design work. |
| Italian AML policy implementation or automatic US-to-Italy threshold conversion | Source CTR logic cannot determine Italian suspicious-transaction reporting duties. | US behavior and Italian adaptation questions are kept separate. |
| Interest accrual, holds, OFAC screening, and every adjacent banking module | Adding them would weaken the review depth of the posting/GL/CTR slice. | Referenced vocabulary may be identified as outside the implemented slice. |
| Bundling or relicensing VAULT-CBS source | The examined upstream snapshot does not supply a license granting redistribution. | Publish original analysis/tools and source references; acquire the source separately. |

## Next increments

| ID | Priority | Candidate increment | Evidence needed before acceptance |
| --- | --- | --- | --- |
| NEXT-01 | P1 | Verify the kit in a supported, authenticated GitHub Copilot host. | Host/version, selected agent, prompts, actual responses, limitations, and a reviewed transcript. |
| NEXT-02 | P1 | Characterize posting/GL boundaries with executable COBOL integration tests. | Caller-owned record setup, both GL sides, failed second-leg behavior, trial-balance provenance, and rollback expectations. |
| NEXT-03 | P1 | Review AML interpretation with an Italian bank's qualified compliance team. | Applicable policies, reporting obligations, case-management workflow, decision authority, and approved terminology. |
| NEXT-04 | P1 | Select exact ISO 20022, CBI, and EPC scheme/profile versions. | Licensed/access-permitted specifications, field mappings, message validation, scheme rules, and evidence of conformance. |
| NEXT-05 | P1 | Design durable lineage and audit storage. | Event identities, append-only controls, retention, replay, access control, redaction, and recovery requirements. |
| NEXT-06 | P2 | Add interest accrual as the next vertical slice. | Pinned `INTCALC0` inputs, rounding/day-count rules, ontology extension, and independent validation. |
| NEXT-07 | P2 | Add typed graph export and richer COBOL constructs. | A consumer requirement, schema migration strategy, regression fixtures, and explicit unsupported-syntax behavior. |

## Iteration and decision policy

Each cycle is analysis → model proposal → evidence/checks → Eric review. Technical
roles share source anchors, intermediate findings, schema changes, and unresolved
questions through the orchestration packet. Material disagreements remain visible
until evidence resolves them; a majority vote does not establish source truth.

Eric may cut a future capability while retaining the P0 outcome. Eric cannot waive
false source claims, failing reproducibility checks, missing provenance, or a
misleading compliance statement. The `docs/acceptance.md` decision concerns MVP
product quality; it is an AI product-owner review, not human compliance approval.
