# A short demonstration: what does “posted” mean?

This demonstration combines **actually executed Python commands** with a
**reviewed interpretation** and **prompts to run in Copilot**. The project was
constructed and reviewed by the five named AI roles in the build environment.
That collaboration was not a GitHub Copilot runtime session. No transcript of a
live Copilot run or execution of the COBOL is claimed.

## 1. Reproduce the evidence

From the project root, acquire the source as described in README, then run:

```sh
python3 -m rose query 'double entry' --limit 2
python3 -m rose query 'threshold' --limit 2
python3 -m rose query 'CTRFIL0' --limit 2
make check SOURCE=.upstream
```

Actual command outputs from the release review are committed in
[`demo-output/`](demo-output/): [double entry](demo-output/double-entry.txt),
[threshold](demo-output/threshold.txt), [filing](demo-output/filing.txt), and
[validation/tests](demo-output/checks.txt). Timing in a test log is incidental;
the four generated semantic artifacts are checked deterministically.

## 2. Explore the decision

**Developer question:** “A cash deposit was successfully posted. Can I assume
the GL balances and the regulatory report was filed?”

**Reviewed answer:** No such end-to-end guarantee is established in this slice.
TXNPOST0 changes the supplied account and emits a GL instruction plus a local
cash flag. GLPOST0's POST changes one supplied GL account; a caller must coordinate
both sides. BSACTRO's customer/day cash assessment is a separate operation.
CTRFIL0's FILE changes local record status and time; it does not submit a report.

The returned query records link directly to these source boundaries:

| Question | Model evidence | Developer value |
| --- | --- | --- |
| What is actually posted? | `rule.workflow_integration_boundaries`, `rule.gl_normal_side` | Locate the missing GL adapter and commitment boundary before rewriting code. |
| Is exactly 10,000 flagged? | `rule.txn_local_ctr_flag`, `rule.bsa_ctr_assessment` | Preserve strict comparison and separate directional totals; avoid silently changing legacy behavior. |
| Is the cash flag always a CTR decision? | `object.cash_assessment`, `rule.bsa_contextual_signals` | Keep the operation selector with the result; separate threshold, heuristic and pending-status readings. |
| Does FILE prove submission? | `rule.ctr_lifecycle` | Identify missing transport, receipt and durable audit evidence. |
| Can this become an Italian SOS? | `uif-sos` in the standards crosswalk | Treat as a new reviewed case workflow, not a translated threshold label. |

A hypothetical 6,000 cash-in event followed by 5,000 cash-in for the same customer
and day can illustrate the distinction between individual and aggregate checks.
That walkthrough assumes the caller supplies and preserves the correct aggregate,
valid flags and unique events. It is analytical, not a COBOL execution result.
A production scenario also needs explicit currency; none is inferred here.

## 3. Run the Copilot conversation

Select **Umberto** and ask:

> Explain the different meanings of posted, reportable and filed in this slice.
> Cite the source commit and line ranges. Separate executable effects from comments.

Select **Peter** and ask:

> Trace Transaction → GL Instruction and Cash Event → Daily Cash Aggregate →
> Cash Assessment. Identify proposed links and show the operation-qualified flag.

Select **Boris** and ask:

> Run the validation commands, inspect the lexical CALL edges, and report which
> integration claims the evidence does and does not support.

Select **Eric** and ask:

> Review those claims against the Italian alignment crosswalk. Which data and
> controls are missing before an Italian-bank modernization pilot?

For one coordinated cycle, select **Satya** with the bounded request in
`docs/copilot.md`. Persist actual tool calls, findings, conflicts and review
outcomes using `orchestration/workflow.md`. If delegation is unavailable, use
the manual profile sequence and record it as manual. Never turn the example
ledger into evidence of execution merely by changing a boolean.

## 4. What the construction review changed

| Review role | Actual contribution | Refinement made |
| --- | --- | --- |
| Umberto | Source-grounded ambiguity and integration review | Preserved local-only GL, CTR and audit effects and documented eleven findings. |
| Peter | Source-to-object model and exact properties | Added Cash Assessment to disambiguate the overloaded result flag; preserved 98 PIC definitions. |
| Satya | Five Copilot profiles and shared-memory protocol | Added bounded iteration, manual fallback, conflict/acceptance gates and sixteen ledger tests. |
| Boris | Extractor, validators, exports and tests | Added exact source checks, crosswalk validation and deterministic artifact checks. |
| Eric | Product and acceptance review | Required explicit publication/live-runtime boundaries and improved double-entry query discoverability. |

These review outcomes are documented artifacts of this build, not a compliance
officer's approval. The next live validation is to run the same questions in the
chosen Copilot host and record its actual responses and citations.
