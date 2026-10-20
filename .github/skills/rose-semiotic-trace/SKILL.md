---
name: rose-semiotic-trace
description: Trace a VAULT-CBS COBOL banking concept to source evidence, ontology objects and actions, and qualified Italian standards mappings. Use for semantic explanations, rule lineage, modernization questions, or claim reviews in The Name of the Rose.
license: MIT
---

# Trace one banking meaning

Read [repository instructions](../../copilot-instructions.md) and
[workflow](../../../orchestration/workflow.md). Work from the repository root.
This skill supplies a repeatable method; it does not launch agents by itself or
pre-approve shell tools.

1. Identify one question, such as “What does posting a transaction change?” or
   “Does filing a CTR send anything to an authority?” Record the source pin
   `03ea874c84b5c00b11b78c6ca1498ec1a9cb7bb4` and the requested jurisdiction.
2. Read `model/ontology.json` and, when shell execution is available and authorized,
   run `python -m rose query 'Transaction'` with the requested term as one literal
   argument. Use `--model model/ontology.json` for an explicit model path.
   Do not interpolate a user question into an executable shell expression.
3. Follow the returned evidence to declarations, selectors/guards, state changes,
   control flow, and errors. If an independent source checkout is available, run
   `python -m rose validate --source ../upstream --model model/ontology.json`.
   Otherwise state that the committed mapping was inspected but its source was
   not revalidated in this session.
4. Separate observed behavior, justified inference, proposed target semantics,
   and unknowns. Cross-check `docs/semiotics.md` and `docs/findings.md`; do not
   confuse a comment or possible function call with a demonstrated call edge.
5. Give standards mappings only with their stated scope and provenance. A US
   reporting path is not Italian SOS; an internal transaction is not an ISO 20022
   message, CBI conformance result, or SEPA scheme implementation.
6. Return the output below. For changes, hand the packet to Satya and follow
   Eric's gates. For an explanation, finish without changing files.

## Response contract

- **Answer**: one operationally useful sentence.
- **Trace**: source construct → model ID → business meaning, with evidence IDs
  and pinned source links for each factual statement.
- **Behavior**: preconditions, mutation, failure path, and persistence/caller
  limits evidenced in the selected slice.
- **Reading**: observed / inferred / proposed / unknown; retain alternatives.
- **Alignment**: conceptual standard anchor, jurisdiction, missing controls.
- **Next evidence**: the smallest inspection or test that resolves an uncertainty.

## Example requests (canned inputs, not execution records)

“Trace a deposit from TXNPOST0 to account balance and identify whether a GL caller
is actually present.”

“Explain why CTR-required has different meanings under BSA function selectors.”

“Which extra semantics would be needed before mapping this flow to an Italian
payment/AML process? Separate proposals from existing implementation.”
