---
name: rose-review
description: Review a semantic claim or change against evidence and the POC acceptance gates.
agent: Eric
---

Review the supplied claim, diff, or run ledger using
[the gate criteria](../../orchestration/workflow.md). If no target is supplied,
review `model/ontology.json` as a model gate. Return accept/revise/block with
evidence references and unresolved gaps. Explicitly check proposed-vs-observed GL
integration, local filing-vs-external dispatch, and US-vs-Italian assumptions.
Do not edit files, publish, or imply regulatory approval.
