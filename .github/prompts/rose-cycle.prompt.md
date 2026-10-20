---
name: rose-cycle
description: Run a bounded five-role semantic review cycle using supported delegation or explicit manual handoffs.
agent: Satya
---

Follow [the orchestration workflow](../../orchestration/workflow.md) for the
user's question. Default to the existing transaction/GL/CTR slice. Inspect host
capabilities, create a fresh run ledger, and obtain Eric's scope gate. Use actual
custom-agent calls when available; otherwise emit one complete handoff packet at
a time for manual profile selection. Share findings across all roles. Preserve
source provenance and conflicts. Stop after three refinement iterations or a
blocking evidence/tool gap. Produce a reviewable result and actual execution
record; no GitHub publication action is part of this prompt.
