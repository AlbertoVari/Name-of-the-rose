# Italian institutional alignment

Reviewed **2026-10-18**. This is a source-grounded gap analysis for an Italian-bank
modernization discussion, not a compliance assessment, approved filing system or
legal opinion. The source is US-oriented; its rules are preserved without silently
changing thresholds, currencies or meanings. The machine-readable companion is
[`model/standards-crosswalk.json`](../model/standards-crosswalk.json).

## Service and message semantics

| Source/model concept | Candidate institutional vocabulary | Mapping judgment and missing evidence |
| --- | --- | --- |
| Account; posting balances, fees and interest | BIAN Current Account / deposit servicing | Conceptual decomposition only. Checking, savings, money-market and term-deposit subtypes must not all become Current Account. Select the applicable versioned service contract before implementation. |
| GL instruction, one-side GL mutation, trial-balance arithmetic | BIAN Financial Accounting | Candidate boundary for accounting responsibility. The source does not provide atomic journal posting, complete-ledger reconciliation or a BIAN API. |
| Transaction/customer/account | ISO 20022 payment and account business concepts | Semantic similarities do not establish message equivalence. An internal movement is not necessarily an interbank payment. |
| Customer payment initiation; interbank transfer; account statement | `pain.001`; `pacs.008`; `camt.053` families | Proposed future adapters with different business purposes. No XML is emitted by this POC, and no schema/profile validation has run. |
| Cash assessment and filing state | AML assessment, reporting workflow | Keep source US CTR labels. Italian SOS, OGG and sanctions decisions require distinct policies and records. |

BIAN's published landscape is version 14.0; this POC uses candidate domain names,
not a claim of conformance to 14.0 operations. The Current Account interpretation
is supported by the separately versioned 12.0 capability description. An upgrade
must explicitly resolve renamed or changed domains [B1, B2]. ISO's message
catalogue identifies message families and versions [I1]; the applicable community
profile can mandate a different version from the catalogue's newest message.

## ISO 20022, CBI and SEPA acceptance boundary

At review, EPC lists **2025 SCT rulebook v1.2**, published 30 September 2026;
its implementation guidelines use the **2019 ISO 20022 message version**.
The EPC page describes a delayed end date for unstructured addresses [E1].
Do not carry an old November 2026 address deadline into this model as a fixed rule.

CBI's public notice identifies an IPR-related XML SEPA payment release effective
5 October 2025 and places detailed documentation in its restricted area [C1].
Those restricted specifications were not retrieved. Consequently the exact
current CBI profile, XSD, usage constraints and change notices are an open dependency.
This POC neither invents proprietary field mappings nor claims CBI compliance.

Before building an adapter, a bank must select its scheme/channel/profile release,
obtain the relevant CBI specifications, and test schemas plus usage rules. Proposed
data requirements include explicit currency, IBAN/account identification policy,
debtor/creditor and agent roles, message and end-to-end identifiers, remittance data,
status/reject/return semantics, and independently reviewed date/address rules.
Numeric `ACCT-NUMBER` is not an IBAN; a transaction amount has no currency field
in this slice. US ACH/wire concepts are outside this release and cannot be relabeled
as SEPA. SCT Instant timing, availability and verification-of-payee obligations
are also unimplemented, not implied by ordinary transaction posting.

## AML: preserve three different decisions

| Decision | Scope and source | Consequence for the POC |
| --- | --- | --- |
| Source CTR threshold | TXNPOST0 checks one cash amount; BSACTRO checks separate customer/day cash-in and cash-out totals, strictly greater than 10000.00. | Preserve executable comparison and unit uncertainty. This is a description of code, not a validation of US legal compliance. |
| Italian SOS | UIF describes suspicion based on transaction circumstances and customer context, with reporting without delay and confidentiality protections [U1]. | Do not generate SOS from a US threshold or from `CTR-REQUIRED=Y`. A reviewed case assessment, decision rationale, authorization and UIF acknowledgement are separate proposed objects. |
| Italian OGG | UIF describes monthly cash aggregation of at least EUR 10,000, including qualifying component operations of at least EUR 1,000, with customer/executor attribution; monthly XML reporting uses Infostat-UIF [U2]. | Daily directional US aggregates are not equivalent. Preserve event-level identity, subject roles, currency and month before designing a reviewed OGG policy. Current 2026 technical documentation must be selected separately. |

The SOS page describes portal entry or XBRL upload; OGG uses its distinct XML
schema [U1, U2]. ISO 20022 payment XML is neither of these reporting formats.
`CTRFIL0 FILE` only changes a supplied record. It provides no authority-facing
transport, acknowledgement or durable proof of filing. `STRC` and `SARQ` reuse a
CTR-named flag; include the function selector in every interpretation.

OFAC-related comments and account legal-hold flags do not demonstrate EU/Italian
sanctions screening. Screening lists, matching rules, beneficial ownership,
customer due diligence, escalation, authorization and evidence retention need
their own policy review and implementation. No numerical Italian cash-payment
limit or retention period is inferred from the US source.

## Audit, lineage and resilience

| Proposed control objective | What exists here | What remains for a bank implementation |
| --- | --- | --- |
| Reproducible code-to-meaning lineage | Commit pin, file SHA256/Git blob hashes, line evidence, excerpt hashes, versioned model and deterministic output checks. | Immutable runtime event identities; input-to-aggregate-to-report lineage; authoritative clock and business-day policy; access controls and governed retention. |
| Accounting integrity | Source mapping and explicit one-side GL semantics. | Atomic commitment or controlled compensation, idempotency, recovery after each write, population-complete reconciliation and tests against actual COBOL execution. |
| Operational evidence | Reviewed findings and a bounded agent decision ledger. | Durable/tamper-evident operational audit, truthful success/failure outcomes, monitoring, incident handling and segregated approval. |
| Resilience/change governance | Static extraction, drift failure and reproducible build gates. | Critical-function mapping, restore/replay exercises, capacity and failure tests, recovery objectives, incident procedures and ICT third-party risk governance. |

BCBS 239 provides risk-data governance, accuracy, completeness, timeliness and
adaptability principles; its formal scope must be assessed for the institution.
This project uses those principles as design guidance, not as an assertion that
all institutions have identical obligations [R1]. Banca d'Italia highlights ICT
change-management and access-control concerns in its DORA communication [D1].
DORA covers ICT risk management, incidents, resilience testing and third-party
risk; applicability and implementing acts need institution-specific review [D2].
Passing the POC's tests is evidence about the semantic tooling only.

## Primary reference register

- **B1 — BIAN landscape:** https://bian.org/deliverables/service-landscape/
- **B2 — Current Account, 12.0 capability:** https://bian.org/servicelandscape-12-0-0/object_21.html?object=37122
- **I1 — ISO 20022 catalogue:** https://www.iso20022.org/iso-20022-message-definitions
- **E1 — EPC SCT rulebook and IGs:** https://www.europeanpaymentscouncil.eu/what-we-do/epc-payment-schemes/sepa-credit-transfer-sct/sepa-credit-transfer-rulebook-and
- **C1 — CBI public release notice:** https://www.cbi-org.eu/News/Servizio-CBI-pubblicazione-nell-8217-area-8220-Prossime-Release-8221-della-versione-IPR-compliant-della-funzione-8220-Disposizioni-di-Pagamento-XML-SEPA-8220
- **U1 — UIF SOS:** https://uif.bancaditalia.it/adempimenti-operatori/segnalazioni-sos/index.html
- **U2 — UIF OGG:** https://uif.bancaditalia.it/adempimenti-operatori/comunicazioni-oggettive/index.html
- **R1 — Basel Framework SRP36:** https://www.bis.org/committees/bcbs/basel-framework/standard/srp/36/inforce/2019-12-15/published/2019-12-15
- **D1 — Banca d'Italia ICT communication:** https://www.bancaditalia.it/compiti/vigilanza/avvisi-pub/2024.12.23-com-ict/Comunicazione-ICT.pdf
- **D2 — DORA, Regulation (EU) 2022/2554:** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554

References were reviewed for the narrow statements above. Linked technical
schemas and bank-specific procedures were not audited. Recheck versions and
bank applicability before implementing any target rule.
