# The operational ontology

[`model/ontology.json`](../model/ontology.json) is a source-grounded semantic model of the selected VAULT-CBS posting, GL and US cash-reporting routines. It describes what the COBOL expresses and identifies where a caller or a future implementation must supply missing behavior. Its actions are explanatory records; they do not execute banking operations.

The baseline is [`NSEvent/cobol-banking-system@03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4`](https://github.com/NSEvent/cobol-banking-system/tree/03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4). The model contains **12 objects, 98 properties, 16 links, 8 actions and 22 rules**. It is a compact JSON graph definition, not an OWL ontology, executable business-rules engine, complete banking domain model or compliance certification.

## How to read a claim

Every object, link, action and rule has a globally unique `id`, human `label` and `description`, an `epistemic_status`, and source `evidence`. Evidence paths refer to the upstream repository; line numbers are one-based and inclusive at the pinned commit. Properties name an exact `source_field` and retain its exact COBOL `PIC` declaration as the `datatype`, with a declaration-line reference.

| Status | Meaning in this model | Example |
| --- | --- | --- |
| `observed` | A declaration, operation or direct dataflow is visible in source. | AGGR compares customer and date before accumulating. |
| `inferred` | A semantic interpretation or bounded absence claim is justified by cited source; the label itself is not a new implemented behavior. | The returned GL group is interpreted as a posting instruction; account/customer identifiers denote links without an evidenced lookup. |
| `proposed` | A target extension or integration remains unimplemented in this slice. | An adapter from TXNPOST0's GL instruction to GLPOST0's different input layout. |

`uncertainties` are part of the model. A consuming agent must preserve them when they materially affect an answer. A record's `observed` status does not certify every conceivable interpretation of its field names. In particular, source diagnostic strings such as “filed” or “written” have narrower implemented effects than their ordinary business meaning.

Action IDs denote modeled COBOL domain operations. Their “Explain …” labels describe how this toolkit presents those operations; `observed` attaches to the cited source behavior, not to a separate explanatory routine in COBOL. This toolkit has no execution adapter.

`inputs`, `outputs` and `rule_ids` on actions describe the source operation's conceptual dependencies. Outputs denote affected record types, not durable events. A self-link through an action does not assert a transaction boundary, persistence or a successful external operation.

## Objects and their meanings

| Object ID | Concrete source representation | Interpretation and boundary |
| --- | --- | --- |
| `object.account` | `CPYACCT` / `ACCT-RECORD` | Supplied account with balance, ownership and restriction fields. A numeric hold amount differs from the legal-hold flag. |
| `object.customer` | `CPYCIF` / `CIF-RECORD` | Customer identity vocabulary for references. This slice does not execute CIF maintenance or identity verification. |
| `object.transaction` | `CPYTXN` / `TXN-RECORD` | Movement data and balance snapshots. Declared status and reversal-reference fields are not proof they are maintained or checked by TXNPOST0. |
| `object.gl_instruction` | TXNPOST0 `LS-GL-ENTRIES` | Output accounts, amount and Y flag. It expresses a requested GL classification; no GL call occurs in TXNPOST0. |
| `object.gl_entry` | GLPOST0 `LS-GL-ENTRY` | Separate input layout, including description/date and a wider amount field, used with one supplied GL account. |
| `object.gl_account` | `CPYGL` / `GL-RECORD` | One account's normal direction, balance and debit/credit counters. POST changes one record per call. |
| `object.trial_balance` | GLPOST0 `LS-TRIAL-BAL` | Arithmetic over supplied totals or one-record fallback totals. Equality does not establish complete-ledger coverage. |
| `object.cash_event` | BSACTRO `LS-TXN-INFO` | Customer/date/direction/amount input, plus an account reference not used as an aggregation key. |
| `object.cash_daily_aggregate` | Customer/date and summary portions of `CPYCTR` | Customer-per-day directional totals and counts. The caller owns aggregate selection and event deduplication. |
| `object.cash_assessment` | BSACTRO function selector and `LS-BSA-RESULT` | Operation-qualified outcome. The same required flag denotes a CTR threshold result, a structuring heuristic or a pending-SAR assertion depending on operation. |
| `object.ctr_filing` | Filing portions of `CPYCTR` | US CTR record lifecycle. FILE sets local state; it does not send a report or receive a regulator acknowledgement. |
| `object.audit_event` | `CPYAUDT` / `AUDIT-RECORD` | Caller context stamped with process-local ID/time. AUDTLOG0 does not persist or retrieve an audit trail. |

The aggregate and filing objects deliberately share `CTR-RECORD` fields. They are two readings of the same record: one organizes cash observations by customer/day; the other organizes filing identity and status. This is not a claim that two independent tables exist. The assessment object similarly combines the operation selector with result fields because the result alone cannot carry a stable business meaning.

Property selection is focused on the vertical slice; it is not an exhaustive copybook export. For example, standalone Hold and SARCase objects are deferred. Existing hold amount/flag fields and the SAR-related signal remain visible without inventing an implemented hold lifecycle or a separate SAR case.

## Source action map

| Action ID | Source entry point | Principal semantic result | Important caller responsibility or gap |
| --- | --- | --- | --- |
| `action.post_transaction` | `TXNPOST0` main logic | Validated account amount change, before/after snapshots, local cash flag, GL instruction. | Account binding, type/direction consistency, transaction identity, downstream orchestration and durable commitment. |
| `action.map_gl_instruction` | `TXNPOST0:MAP-GL-ENTRIES` | Debit/credit routing by transaction type and deposit subtype. | An explicit adapter, two GL-side calls and verification are still needed. |
| `action.post_gl_side` | `GLPOST0` / `POST` | Current balance and directional MTD/YTD counters on one GL account. | Choose a matching account, commit both sides consistently and handle recovery. |
| `action.evaluate_trial_balance` | `GLPOST0` / `TBAL` | Difference and equality flag over chosen totals. | Establish that totals cover the intended ledger population. |
| `action.aggregate_cash` | `BSACTRO` / `AGGR` | Customer/day accumulation and directional CTR threshold outcome. | Valid inputs, correct bucket, unique events, currency/day policy and constituent-event lineage. |
| `action.assess_cash` | `BSACTRO` / `CHEK`, `STRC`, `SARQ` | Contextual threshold or heuristic/status result. | Keep function code with the output; do not infer a SAR case or Italian SOS. |
| `action.manage_ctr_state` | `CTRFIL0` / `CRTE`, `FILE`, `QURY`, `VOID` | P/F/V state changes and record timestamps. | Eligibility policy, complete filing data, durable uniqueness, authorized submission and acknowledgement. |
| `action.prepare_audit_record` | `AUDTLOG0` / `WRIT`, `READ` | Timestamp/ID/sequence preparation or nonblank-key check. | Durable logging, truth of supplied outcome, retention, lookup and tamper protection. |

EODPROC0 is contextual evidence, not a ninth action hiding a complete batch system. It supplies one account, calls TXNPOST0 for interest when due, calls GLPOST0 in TBAL mode with initialized zeros, and supplies an account annotation to AUDTLOG0. Its comment about automatic cash aggregation is not an executable call. See [F01–F02](findings.md#f01--returned-gl-instruction-is-not-a-posted-journal).

## Decision semantics that must survive translation

The 22 rule records preserve guard order, field mutation, thresholds and failure behavior. A consumer should answer questions through the associated action's `rule_ids`, then inspect the evidence and uncertainty fields.

| Question | Model records to inspect | Faithful answer |
| --- | --- | --- |
| Does a debit reduce available funds? | `rule.txn_available_funds`, `rule.txn_balance_transition` | It first checks amount against supplied available balance, changes ledger balance, then computes available as ledger minus hold amount. Pending debit/credit fields are not in that formula. |
| Does reversal restore an original posting? | `rule.txn_direction_and_reversal`, `rule.txn_gl_routing` | The source swaps input direction before further checks and uses cash/deposit GL routing. It does not retrieve or validate the original event. |
| Is every successful posting balanced? | `rule.gl_normal_side`, `rule.gl_trial_balance`, `rule.workflow_integration_boundaries` | TXNPOST0 returns an instruction; GLPOST0 changes one side; TBAL only checks supplied arithmetic. The slice does not implement an atomic two-sided workflow. |
| Is the cash bucket an account per day? | `rule.bsa_customer_day_key`, `link.cash_event_daily_aggregate` | The guard uses customer plus date. Account context exists but does not select a bucket or populate its constituent-account list. |
| Is exactly 10,000 reportable in this code? | `rule.txn_local_ctr_flag`, `rule.bsa_ctr_assessment` | The executable threshold is strictly greater than 10000.00. This describes the pinned US-oriented code, not Italian law. |
| Can cash-in and cash-out be netted? | `rule.bsa_ctr_assessment`, `rule.bsa_contextual_signals` | CTR assessment evaluates the two totals separately. STRC instead adds them for its 8000–9999.99 heuristic. Neither operation computes a net amount. |
| Does `required_flag=Y` always mean a CTR? | `object.cash_assessment`, `rule.bsa_contextual_signals` | Its meaning depends on CHEK/AGGR, STRC or SARQ. SARQ reads pending CTR status as a SAR signal without consulting a separate SAR record. |
| Does “FILE” submit a regulator report? | `rule.ctr_lifecycle` | It marks the supplied record F and updates a timestamp. The routine provides no transmission or acknowledgement. |

The examples above are static interpretations. They are not an assertion that COBOL scenarios have been executed. [The findings register](findings.md) describes the evidence and modernization consequences in more detail, including mutation before failed return, ambiguous equal-account suspense posting and partial aggregation after count overflow.

## Type and identity policy

Preserve COBOL fixed-point precision. For example, `PIC S9(13)V99` describes a signed field with thirteen integer and two fractional digits; GL entry/account amounts use `PIC S9(15)V99`. A graph adapter should use decimal values or decimal strings with explicit scale, not binary floating point. Identifier fields such as `PIC 9(12)` should be preserved as fixed-width lexical identifiers when leading zeros matter; numeric storage syntax does not make an account number a quantity.

The model does not add a currency property that the source lacks. USD may be a clearly labeled scenario assumption because the repository is US-oriented; EUR is not obtained by relabeling an amount. No conversion is implemented. Likewise, the source account number is not an IBAN, CIF identity is not a legal-entity identifier, and SSN/TIN is not codice fiscale.

Dates are encoded as numeric fields. A format convention is not proof of calendar validation. CTR and audit timestamps discard the offset supplied by COBOL `CURRENT-DATE`, so global ordering, time-zone policy and business-day identity remain unresolved. Process-local identifiers restart at one; graph ingestion must not assume they are unique across process lifetimes.

## Institutional alignment boundary

BIAN service-domain concepts, ISO 20022 business components, CBI/SEPA profiles and Italian AML expectations belong in a separately reviewed alignment layer. Shared words such as Account, Party, Entry, Transaction or Report are useful mapping candidates, not conformance evidence.

The operational JSON deliberately preserves source terms and flags. It does not replace the source US CTR with an Italian objective communication or SOS, replace OFAC state with an Italian sanctions screening result, or turn a US Call Report tag into an Italian supervisory classification. Any target extension must identify the jurisdiction, standard/profile version, responsible reviewer, required data, control changes and remaining gaps. Regulatory guidance and its source references are maintained separately from executable-code evidence.

A practical modernization extension could add a currency-qualified monetary amount, immutable cash event identity, explicit journal-side identity, durable audit lineage and an independently reviewed reporting assessment. These are proposals; the two `proposed` link records in this MVP only expose the immediate GL-adapter and transaction-audit integration opportunities.

## Updating the model

When the source commit changes, refresh extraction and rerun evidence validation before revising interpretations. Inspect actual control flow rather than carrying forward comments or prior assumptions. Keep source observations, semantic inferences and target proposals separate, and do not silently promote a proposed relation to observed.

A useful review sequence is: verify exact declaration and scope; trace reads, writes and guard order; locate the calling boundary; compare diagnostic wording with actual effects; attach uncertainties; then discuss institutional mapping. The model and [semiotic reading guide](semiotics.md) are designed for that repeatable developer conversation.
