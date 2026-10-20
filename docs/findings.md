# Findings that constrain the translation

These are static observations and reasoned consequences from VAULT-CBS commit [`03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4`](https://github.com/NSEvent/cobol-banking-system/tree/03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4). Locations are upstream repository paths and one-based line spans. A consequence described below is not an executed COBOL test result unless a separate validation report explicitly records execution. This project preserves the source; it does not silently fix its behavior.

“Release-critical” means the semantic release must disclose the finding and avoid an unsupported claim. It does not mean a production fix is included in this POC.

## F01 — Returned GL instruction is not a posted journal

**Source fact.** TXNPOST0 performs internal paragraphs, changes the supplied account and returns LS-GL-ENTRIES (`src/TXNPOST0.cob:25–51,260–293`). It contains no executable CALL. GLPOST0 POST mutates one supplied GL-RECORD; its comments require two caller-managed POST calls (`src/GLPOST0.cob:54–66,98–236`). TXNPOST0's GL result and GLPOST0's input are also different layouts (`src/TXNPOST0.cob:16–20`; `src/GLPOST0.cob:16–21`).

**Interpretation and consequence.** The slice supplies pieces of accounting behavior. It does not demonstrate an atomic end-to-end double-entry posting. `LS-GL-POST-FLAG = Y` means an instruction has been populated, not that both ledger sides are committed. An adapter must deliberately map fields and supply description/date; passing the result buffer directly would not satisfy the second interface's layout.

**Release decision.** Release-critical. Model the instruction and applied GL side separately. Any two-side demonstration must be marked as explicit caller orchestration or analytical scenario, not as an extracted TXNPOST0→GLPOST0 call. Production follow-up: journal identity, atomicity/compensation, persistence and recovery.

## F02 — EOD does not close the accounting or cash-integration gaps

**Source fact.** EODPROC0 initializes both GL-RECORD and trial totals immediately before calling GLPOST0 with TBAL (`src/EODPROC0.cob:155–165`). GLPOST0 falls back to that record's MTD totals when both supplied totals are zero (`src/GLPOST0.cob:241–260`). EOD's successful interest-payment path consumes the TXNPOST0 result code and advances payment state, but never posts the returned GL instruction (`src/EODPROC0.cob:251–294`). EOD's comment says cash aggregation is handled by TXNPOST0 through BSACTRO (`src/EODPROC0.cob:211–214`); there is no such executable call in TXNPOST0 or EODPROC0. EOD's actual calls are GLPOST0 at 161, INTCALC0 at 229, TXNPOST0 at 263 and AUDTLOG0 at 398.

**Interpretation and consequence.** In this EOD path the trial-balance check compares initialized zeros; it cannot validate the account's transactions or a ledger population. The cash-integration comment is an intended-design assertion contradicted by the visible call graph. Copying CPYCTR and declaring BSA work areas does not implement aggregation.

**Release decision.** Release-critical. Draw EOD→GLPOST0 as TBAL only and EOD→TXNPOST0 as interest payment. Do not infer BSACTRO or CTRFIL0 edges. A whole-bank EOD/reconciliation claim is outside the demonstrated scope.

## F03 — Account direction and GL classification can disagree

**Source fact.** TXNPOST0 validates D/C membership but not consistency with transaction type (`src/TXNPOST0.cob:71–77`). Ledger increase/decrease depends on D/C (`src/TXNPOST0.cob:206–223`), while the normal DEP/WDL/FEE/INT GL mapping depends on transaction type (`src/TXNPOST0.cob:260–274`). The routine accepts the supplied account without comparing its number to TXN-ACCT-NUMBER (`src/TXNPOST0.cob:25–51,56–194`).

**Interpretation and consequence.** With otherwise valid inputs, DEP+D follows the debit balance branch but returns the deposit-style GL pair. A mismatched transaction account reference is not rejected by this program. The likely caller invariants are plausible, but they are not enforced here.

**Release decision.** Record caller obligations as assumptions, not implemented guards. Example data must state consistent account identity and type/direction. Candidate follow-up: explicit validation and negative tests at the integration boundary.

## F04 — Reversal is an in-place polarity swap, not a verified inverse event

**Source fact.** REV swaps TXN-DR-CR before account-status and funds validation (`src/TXNPOST0.cob:35–39,143–160`). No lookup of an original transaction occurs. Reversal GL logic distinguishes only the resulting direction and selects cash/deposit accounts (`src/TXNPOST0.cob:275–286`). The copybook declares reversal identifiers, but TXNPOST0 does not read them (`copybooks/CPYTXN.cpy:45–46`).

**Interpretation and consequence.** A call rejected after the swap still leaves the caller's direction changed. Reusing that same buffer for a retry can reverse direction again. The program's REV behavior is not evidence that it verifies a unique original transaction, prevents repeated reversal, or reverses arbitrary fee/interest GL history.

**Release decision.** Describe `ReverseDirection` as source behavior with restricted cash/deposit mapping. A robust `ReverseOriginalPosting` action is proposed work requiring original-event linkage and idempotency. Do not promise rejection leaves every input unchanged.

## F05 — GL account membership and equal-sided suspense require review

**Source fact.** For a debit-normal GL account, GLPOST0 checks whether the account matches the credit side; otherwise it follows the debit branch (`src/GLPOST0.cob:98–159`). For a credit-normal account it checks whether it matches the debit side; otherwise it follows the credit branch (`src/GLPOST0.cob:160–220`). This default applies even when the supplied account matches neither side. TXNPOST0 maps unknown transaction types to debit and credit account 9999 (`src/TXNPOST0.cob:287–293`), and unknown subtypes to deposit GL 9999 (`src/TXNPOST0.cob:298–310`).

**Interpretation and consequence.** Success does not prove the supplied GL account belongs to the instruction. An equal-account suspense pair cannot be treated as normal two-sided posting without explicit caller semantics; this interface chooses side by matching account numbers, making that case ambiguous.

**Release decision.** Preserve the fallbacks as observed behavior. Surface account-membership and equal-account checks as proposed validation. Never describe “suspense” as proof that a manual-review workflow was actually opened.

## F06 — Cash checks are separate, and their boundaries differ

**Source fact.** TXNPOST0 CHECK-CTR compares only TXN-CASH-AMOUNT with the source threshold (`src/TXNPOST0.cob:315–320`). BSACTRO CHEK first returns for exempt records or an explicit N cash flag, then tests the input amount and either aggregate total (`src/BSACTRO.cob:56–88`). AGGR accumulates only an explicit Y cash flag; it then applies exemption and separate cash-in/cash-out checks (`src/BSACTRO.cob:114–175`). The constant is 10,000 and the executable comparisons are strictly greater-than (`copybooks/CPYCONST.cpy:7–8`). CTRFIL0's header says greater-than-or-equal (`src/CTRFIL0.cob:7`), but CRTE only checks nonzero customer and some positive cash (`src/CTRFIL0.cob:64–79`).

**Interpretation and consequence.** A per-item TXN flag is not an aggregate decision and does not apply the exemption test. CHEK and AGGR treat malformed cash flags differently. A source comment cannot change the strict executable boundary. A locally created CTR record need not have crossed that boundary, because creation does not enforce it.

**Release decision.** Release-critical. Keep the three decisions separately named and contextualized. At exactly 10,000 the observed threshold predicates are false. This is a claim about code, not independent legal advice or an Italian threshold.

## F07 — Aggregation has caller and failure-state assumptions

**Source fact.** AGGR stamps customer/date when CTR-CUST-ID is zero before checking whether the transaction is cash (`src/BSACTRO.cob:98–114`). It rejects a different customer/date only for an already nonzero key. It does not validate positive cash amount, nonzero input customer, valid calendar date, or unique event. Amount is added before its count; the count-overflow branch returns without rolling back the preceding successful amount addition (`src/BSACTRO.cob:117–145`). LS-BSA-ACCT-NUMBER exists (`src/BSACTRO.cob:25`) but AGGR does not populate the CTR account list declared in `copybooks/CPYCTR.cpy:23–27`.

**Interpretation and consequence.** Negative input may reduce a total while still increasing its count. Customer zero continues to function as an uninitialized sentinel. Noncash input can stamp identity/date. Retried input can double count, and an error can leave partial aggregation. Cross-account aggregation is possible by supplying one customer/date record, but a reconciled constituent-account list is not maintained here.

**Release decision.** State the input-quality, identity and retry assumptions explicitly. Proposed modernization includes immutable cash-event identity, validation, lineage to constituent events and transactional aggregation. Do not claim the existing totals constitute a complete auditable history.

## F08 — The CTR-required field carries three incompatible propositions

**Source fact.** STRC tests combined cash-in plus cash-out in the range 8,000 through 9,999.99 and total count greater than one, then returns E0082 and Y in LS-BSA-CTR-REQUIRED (`src/BSACTRO.cob:182–221`; `copybooks/CPYCONST.cpy:11–14`). SARQ sets the same flag for CTR-FILING-STATUS P and returns a pending-SAR message (`src/BSACTRO.cob:223–240`). CTRFIL0 sets P when creating a CTR (`src/CTRFIL0.cob:103–107`).

**Interpretation and consequence.** The same field can mean a threshold outcome, a structuring heuristic alert, or a pending-SAR assertion. A pending CTR is not evidence of an independently created SAR. The STRC heuristic combines directions, unlike CTR aggregation thresholding. E0082 is an alert-bearing result here, so treating every non-E0000 as a uniform technical failure loses meaning.

**Release decision.** Release-critical. Interpret result fields with operation context and preserve the semantic conflict. Do not infer SAR creation, human assessment, regulatory submission, or an Italian SOS obligation from this flag.

## F09 — “Filed” and “written” describe local state, not external proof

**Source fact.** CTRFIL0 FILE changes P to F and a timestamp, without transport, persistence or acknowledgement (`src/CTRFIL0.cob:113–141`). Its filing sequence restarts at one, a limitation acknowledged in its source comment (`src/CTRFIL0.cob:12–15`). AUDTLOG0 WRIT stamps an input record and increments a similarly process-local ID (`src/AUDTLOG0.cob:23–26,56–77`); READ only checks for a nonblank entity key (`src/AUDTLOG0.cob:83–91`). EOD audit construction hardcodes E0000 and a completion description even though account error paths exist, and it does not check the audit result (`src/EODPROC0.cob:240–246,276–294,387–400`).

**Interpretation and consequence.** These routines provide record enrichment and lifecycle labels. They do not prove durable logs, regulatory receipt, restart-safe identity or truthful per-account outcome. A returned success message is not sufficient audit evidence.

**Release decision.** Release-critical for compliance wording. Describe lifecycle state and audit metadata as available concepts; make durable append, outcome propagation, acknowledgement and recovery explicit gaps. These gaps motivate operational-resilience work, not a claim of regulatory noncompliance adjudication.

## F10 — Present fields do not prove maintained business state

**Source fact.** CPYTXN declares TXN-STATUS and TXN-GL-* fields (`copybooks/CPYTXN.cpy:41–51`), but TXNPOST0 returns its GL data in a separate linkage structure and does not set those declared fields (`src/TXNPOST0.cob:16–20,260–293`). It computes an early-CD-withdrawal penalty when acknowledged (`src/TXNPOST0.cob:168–194`) but account posting changes the ledger only by TXN-AMOUNT (`src/TXNPOST0.cob:206–223`). Available balance is ledger minus hold amount, although the account copybook also has pending debit/credit and collected balance (`src/TXNPOST0.cob:228–238`; `copybooks/CPYACCT.cpy:26–32`).

**Interpretation and consequence.** Posting success is not evidence that TXN-STATUS was set to P or that a penalty was charged. The penalty is a computed result for another decision. Field availability and field maintenance require separate mappings. A richer availability definition is a possible target policy, not the formula executed here.

**Release decision.** Keep declaration maps distinct from write/decision maps. Explain the exact balance and penalty formula before proposing financial-policy changes.

## F11 — Currency and jurisdiction are unstated in the core records

**Source fact.** Amounts are signed fixed-point decimal fields without associated currency fields in the slice's transaction, GL and CTR records (`copybooks/CPYTXN.cpy:18–40`; `copybooks/CPYGL.cpy:18–26`; `copybooks/CPYCTR.cpy:17–22`). CTR and CIF identity representations include numeric SSN/TIN fields (`copybooks/CPYCTR.cpy:9–16`; `copybooks/CPYCIF.cpy:13–15`). GLPOST0 maps account numbers to US-oriented Call Report codes (`src/GLPOST0.cob:282–309`).

**Interpretation and consequence.** The repository's US framing makes USD a plausible analytical assumption, but amount precision alone does not encode USD. An Italian translation cannot rename SSN/TIN to codice fiscale or treat a US Call Report mapping as an Italian prudential reporting map. Precision, identifier scheme and jurisdiction must be explicit dimensions.

**Release decision.** Label currency and jurisdiction assumptions on examples. Any ISO 20022, CBI, SEPA or Italian reporting alignment remains a versioned, reviewed candidate mapping. Never assert conformity from shared nouns.

## Review backlog

These are later modernization priorities, not release-blocking repairs for the interpretive POC. The POC gate is faithful disclosure of the gaps above.

| Production priority | Question for the next iteration | Evidence needed to resolve it |
| --- | --- | --- |
| P0 | Which caller owns atomic account and two-sided GL commitment? | Actual caller code, storage transaction boundary, rollback/recovery tests and journal identity. |
| P0 | How is each cash event deduplicated and joined to customer, account and business day? | Event identity, currency and business-day policy, caller validation, aggregate lineage and restart tests. |
| P0 | What is the actual reporting workflow and jurisdiction? | Reviewed policy, independent assessment, authorized submission interface, acknowledgements and immutable history. |
| P1 | Is reversal limited to cash deposits/withdrawals or expected to reverse fees and interest? | Original-event contract and mapping tests for supported operation types. |
| P1 | Which source comments describe intended integration rather than current execution? | Reconciled architecture and executable call graph at a named commit. |
| P1 | Which flags and outcomes must be persisted for audit and recovery? | Retention/access requirements, durable event schema, error propagation and replay design. |

An accepted POC makes these questions visible while preserving what the code does. It need not repair the upstream banking system to deliver useful, faithful semantics.
