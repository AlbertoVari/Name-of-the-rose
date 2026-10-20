# Reading the bank through its signs

This model describes the behavior of VAULT-CBS at commit [`03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4`](https://github.com/NSEvent/cobol-banking-system/tree/03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4). Source locations below are relative to that repository, with one-based lines. The model is a reviewable interpretation of a bounded slice, not a replacement specification for an Italian bank. No upstream source is bundled with this project.

## A claim has a layer

| Layer | What it asserts | Example | What would change the claim |
| --- | --- | --- | --- |
| Source fact | A declaration, executable operation, or control-flow edge exists in the pinned files. Comments are identified as comments. | `TXNPOST0` sets the supplied GL instruction flag after selecting accounts (`src/TXNPOST0.cob:260–293`). | A different commit or a source-analysis error. |
| Semantic interpretation | A named domain concept explains those facts. It keeps its evidence and uncertainty. | That result is a `GLInstruction`, expressing a proposed debit/credit pair. | Evidence that a caller persists or commits both journal sides, or a better interpretation. |
| Proposed Italian adaptation | A target requirement or design that is absent from, or unproven in, this slice. | Add currency, reviewed reporting policy, durable posting orchestration, and institution-specific message mappings. | Approved policy, jurisdiction, profile version, integration design, and validation evidence. |

An executable condition has stronger evidence for actual behavior than a comment announcing a capability. A copybook field proves representational capacity, not a successful business process. A result message proves the program returned that message, not that an external institution received a submission. An identifier named `CTR` is not sufficient evidence of an Italian AML reporting concept.

## The semiotic unit

For this project a useful unit is **sign → referent → interpretation → consequence**, with a source location attached. This is a working analytical convention, not a claim that COBOL implements a particular philosophical school.

* **Sign:** a field, code value, paragraph name, predicate, or result message.
* **Referent:** the record or state that the code actually reads or changes.
* **Interpretation:** a named banking concept, with scope and alternative readings.
* **Consequence:** the operational decision or mutation justified by that interpretation.

For example, `ACCT-LEGAL-HOLD = Y` combined with effective debit direction causes `E0035` and return (`src/TXNPOST0.cob:104–109`). The referent is the supplied account's flag, the interpretation is an outflow restriction, and the consequence is rejection by this subprogram. Calling it a completed sanctions-screening decision would add evidence that this function does not contain. The nearby OFAC discussion at lines 81–86 is a comment; no screening service is called here.

## Nouns, links, and limits

The names below are aligned with the ontology object identifiers. Record fragments can support several objects; several records can contribute to one object. COBOL storage groups do not force the ontology's boundaries.

| Model object | Source sign and evidence | Operational reading | Boundary or alternative reading |
| --- | --- | --- | --- |
| `object.customer` | `CIF-CUST-ID`, `copybooks/CPYCIF.cpy:5–20`; `ACCT-PRIMARY-CIF`/`ACCT-JOINT-CIF`, `copybooks/CPYACCT.cpy:9–15` | Customer identity referenced by accounts and cash aggregates. | A reference is not validated ownership, identity verification, or beneficial ownership. TXNPOST0 does not load CIF. |
| `object.account` | Account keys, balances, flags, `copybooks/CPYACCT.cpy:5–41,92–99` | The supplied account state whose ledger and availability can change. | Account number is a local identifier; it is not an IBAN. Available balance here uses ledger minus hold amount, not all potential pending obligations. |
| `object.transaction` | Key, detail, snapshots, `copybooks/CPYTXN.cpy:5–46` | An instruction and mutable result context for account posting. | “Transaction” can mean a requested operation or a business event; the copybook mixes both. It does not prove a database transaction or durable booking. |
| `object.gl_instruction` | `LS-GL-ENTRIES`, `src/TXNPOST0.cob:16–20,260–293` | The debit account, credit account, amount and ready flag returned by account posting. | It is not a posted journal. This structure also differs from GLPOST0's input layout (`src/GLPOST0.cob:16–21`); an explicit adapter is required. |
| `object.gl_entry` | GLPOST0 input and one-record mutations, `src/GLPOST0.cob:16–21,66–236` | A journal-side operation applied to the supplied GL account. | The source provides no persistent journal-entry identifier or proof of a committed two-sided journal. This is an interpretive object over the interface and mutation. |
| `object.gl_account` | `GL-ACCOUNT-NUM`, normal balance and accumulators, `copybooks/CPYGL.cpy:5–32` | A classification and running balance with MTD/YTD debit and credit totals. | A GL number is not itself a service domain, legal account classification, or standard message field. |
| `object.trial_balance` | `src/GLPOST0.cob:23–27,241–264` | A comparison of supplied debit/credit totals, with a fallback to one GL record's MTD totals. | Balanced supplied totals do not prove completeness, correct account selection, or ledger-wide reconciliation. |
| `object.cash_event` | BSA input, `src/BSACTRO.cob:18–25` | Caller-identified amount, direction, customer, account and date offered for aggregation. | The input has no event identifier; repeated aggregation is not detected. Currency is absent. |
| `object.cash_daily_aggregate` | `CTR-CUST-ID`, `CTR-TXN-DATE`, separate totals/counts; `src/BSACTRO.cob:93–175` | A customer/date bucket with distinct cash-in and cash-out measures. | This semantic facet shares the physical `CTR-RECORD` with a filing. It does not establish a submitted report or an Italian reporting obligation. |
| `object.cash_assessment` | Function selector and BSA result fields, `src/BSACTRO.cob:16,26–50` | An operation-qualified decision outcome over a cash input or aggregate. | The same flag carries different meanings under CHEK/AGGR, STRC and SARQ; retain the operation, result code, evidence and interpretation together. |
| `object.ctr_filing` | Filing key/status, `copybooks/CPYCTR.cpy:5–8,28–34`; lifecycle in `src/CTRFIL0.cob:64–181` | A local US-oriented filing record that can be created, marked filed, queried or voided. | “Filed” is a source state label; this module has no external transport or acknowledgement. |
| `object.audit_event` | Audit fields, `copybooks/CPYAUDT.cpy:5–23`; stamping, `src/AUDTLOG0.cob:56–77` | A supplied description of an operation with local timestamp and sequence information. | The logger does not persist an immutable audit trail in this implementation. |

The account–customer and transaction–account links are identity references. The model must distinguish **declared reference**, **validated relationship**, and **observed call**. In particular, TXNPOST0 accepts both a transaction and an account but does not check their account numbers for equality (`src/TXNPOST0.cob:25–51,56–194`). A proposed modernization should validate this relationship; the extraction must not pretend it already does.

## Verbs and business meaning

**Post an account operation.** TXNPOST0 validates positive amount and a D/C indicator; for `REV` it changes that indicator before account-status and balance checks. It then checks account eligibility and early CD withdrawal, captures balances, changes ledger balance, recomputes availability, captures the result, updates the low-balance watermark, returns the GL instruction, sets a per-item cash flag and updates the last-transaction date (`src/TXNPOST0.cob:30–51`). The order is part of the meaning: a reversal is checked under its new direction, and a rejected reversal can already have changed the caller's input direction.

**Apply a GL side.** GLPOST0's POST operation updates one supplied record using normal-balance direction, account-number comparison and amount. The comments assign responsibility for posting both sides to the caller (`src/GLPOST0.cob:54–64`); the implementation contains no enclosing atomic journal coordinator. An ontology may propose a `CommitJournal` action, but it must label that action as missing or proposed, not extract it as implemented.

**Accumulate cash.** BSACTRO AGGR stamps a customer/date on an initially unkeyed record or rejects a different customer/date, then updates the appropriate cash amount and count when `IS-CASH = Y`. It tests cash-in and cash-out separately against the threshold after aggregation. An exemption suppresses the requirement flag but does not undo the accumulated totals (`src/BSACTRO.cob:93–175`). Therefore the aggregate describes observed cash activity and the flag describes a separate decision.

**Change filing status.** CTRFIL0 CRTE checks nonzero customer and at least one positive cash total, assigns an in-memory sequence and current timestamp, and sets P. FILE permits P→F; VOID permits P→V (`src/CTRFIL0.cob:64–181`). Neither action performs delivery to a regulator. Create does not independently enforce a cash threshold. Status V exists in executable logic although the copybook comment only lists P/F/E (`copybooks/CPYCTR.cpy:32–34`).

## Four signs with competing readings

| Sign | Plausible reading from its name | Evidence-constrained reading | Required explanation |
| --- | --- | --- | --- |
| `LS-GL-POST-FLAG = Y` | Both journal sides were posted. | A GL instruction is ready; TXNPOST0 contains no CALL and writes this flag at `src/TXNPOST0.cob:292–293`. | Show the integration gap before describing accounting completion. |
| `LS-BSA-CTR-REQUIRED = Y` | A CTR threshold was met. | CHEK/AGGR use threshold logic; STRC also uses Y for a structuring heuristic; SARQ uses Y for a claim based on pending status (`src/BSACTRO.cob:73–85,162–175,209–218,234–240`). | Qualify the flag by operation and rule. Never merge these propositions into one legal obligation. |
| `CTR-FILING-STATUS = P` | A CTR filing is pending. | That is the lifecycle meaning in CTRFIL0, while SARQ treats the same value as a pending SAR (`src/CTRFIL0.cob:103–107`; `src/BSACTRO.cob:223–240`). | Preserve the conflict as an unresolved source ambiguity; do not manufacture a SAR case record. |
| “Filed with FinCEN” result | Successful regulatory submission. | A returned message following a local state/timestamp change (`src/CTRFIL0.cob:113–141`). | Distinguish `MarkFiledLocally` from proposed dispatch/acknowledgement actions. |

The unresolved readings are useful. They identify where a developer must seek the caller contract, production integration, policy owner, or missing persistence layer before modernization. Openness to interpretation does not permit inventing execution edges.

## Italian institutional interpretation is a separate layer

The alignment documentation governs standards references and review dates. In this semiotic layer, the following are **proposals**, never assertions that the US source already meets an Italian obligation:

* Relate account servicing, accounting and compliance capabilities to candidate BIAN service domains. Capability correspondence does not establish a standardized BIAN implementation.
* Relate selected account and transaction concepts to candidate ISO 20022 components only after choosing a message family/version and the relevant CBI or SEPA implementation profile. A numeric local account key and a signed amount are insufficient to produce a valid message. Currency, parties, identifiers, direction, dates and profile constraints require explicit treatment.
* Keep the source's US cash-threshold decision, structuring heuristic and filing state separate from a proposed Italian AML assessment and any SOS workflow. No US CTR threshold or exemption is transplanted into an Italian rule. A candidate SOS needs independently reviewed policy, assessment, authority and submission evidence.
* Add evidence-bearing operational actions: verify identity links, coordinate both ledger sides, deduplicate requests, preserve failure outcomes, persist lineage, and reconcile. These are a modernization backlog, not hidden features of the legacy implementation.

Each translated statement should carry source commit, path, line span, semantic layer, operation context, confidence, unresolved questions and applicable jurisdiction. A proposed standard mapping also needs the external standard/profile identifier, version, reviewer and review date. That record of interpretation is the bridge between exploration and an auditable modernization decision.

## A useful question and a bounded answer

**Question:** “A customer makes two cash deposits of 6,000 and 5,000. Explain the banking meaning and what an Italian bank could reuse.”

**Source fact:** Starting with zero totals and counts, two AGGR calls for the same supplied customer/date, each identified as cash-in, produce an 11,000 cash-in total and a cash-in count of two if both calls succeed. For a nonexempt record, 11,000 exceeds the source constant 10,000 (`src/BSACTRO.cob:98–175`; `copybooks/CPYCONST.cpy:7–8`). This is an analytical trace of those calls, not an assertion that TXNPOST0 invoked them.

**Interpretation:** The reusable concepts are a cash event, customer/date aggregate and a threshold decision with lineage. A filing, a submitted report and two-sided GL commitment have not thereby been established.

**Proposed Italian adaptation:** Reuse those concepts to ask the institution's reviewed AML policy a different question. Do not conclude “SOS required” from this arithmetic. Preserve missing currency, caller orchestration and reporting-policy requirements as open implementation work.

See [findings.md](findings.md) for the source conflicts and their release implications.
