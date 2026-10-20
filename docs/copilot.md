# Using the five Copilot profiles

The project includes **Umberto**, **Peter**, **Satya**, **Boris**, and **Eric** in
`.github/agents/`. They are repository-scoped role instructions. The Python CLI
extracts and checks evidence without an LLM. Copilot supplies the interactive
reasoning and, where the host supports it, actual agent delegation. This release
does not bundle a Copilot runtime or claim a live Copilot demonstration.

## Start with one question

1. Open this repository's root in a Copilot-enabled development environment.
2. Follow the README installation steps. An independent, pinned upstream checkout
   is needed to re-extract/validate source; the committed model can be read without
   it. Keep source outside the release repository.
3. Select **Umberto** in the custom-agent picker and ask:

   > Explain transaction posting as signs, objects, state changes, and business
   > rules. Cite pinned source evidence and distinguish observed behavior from
   > proposed GL integration.

4. Select **Peter** to propose a model change, or **Eric** to review its evidence.
   Select **Satya** for a bounded multi-role cycle. All roles can be selected
   manually; role names are case-sensitive when used for delegation.

The repository skill `.github/skills/rose-semiotic-trace/SKILL.md` provides the
same trace method for hosts that load project skills. If automatic discovery is
unavailable, attach/read that file and the selected agent profile explicitly.

## Supported surfaces and boundaries

| Surface | Entry point | What the project relies on |
| --- | --- | --- |
| Copilot-enabled VS Code | Agent picker: Umberto/Peter/Satya/Boris/Eric | `.github/agents/*.agent.md`, shared instructions, project skill |
| VS Code Local harness | `/rose-explain`, `/rose-review`, `/rose-cycle` | `.github/prompts/*.prompt.md`; custom `agent` selected by name |
| VS Code with working subagent tools | Select Satya and explicitly request the cycle | `agent` tool set and restricted `agents` list; actual tool invocations |
| GitHub Copilot cloud agent / CLI | Select an available repository custom agent | Common profile fields and tool aliases; host-dependent delegation |
| Any host without delegation | Select profiles sequentially using packets | Manual workflow in `orchestration/workflow.md`; no hidden agent process |
| No Copilot entitlement/runtime | Run Python CLI and inspect model | Deterministic extraction/query/validation only |

GitHub documents `read`, `search`, `edit`, `execute`, and `agent` as tool aliases.
Missing tools can be ignored by the host, so Satya must check availability and
record a fallback. Our profiles omit model names, MCP servers, hooks, and blanket
tool grants. Tool permissions remain controlled by the host. [GitHub configuration
reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration).

In VS Code's Local harness, enable/select Run Subagent (`agent/runSubagent`) in
Configure Tools if needed. No nested delegation is required. Every invocation
receives a complete packet because a worker need not inherit the parent chat.
The coordinator asks for a new review with fresh context rather than assuming a
persistent worker. The optional `agents` allowlist is a VS Code feature; the
instruction body maintains the same restriction elsewhere. [VS Code
subagents](https://code.visualstudio.com/docs/agents/run/subagents).

Prompt-file slash commands are a VS Code Local-harness convenience, not a
portable shell or GitHub command. Other hosts use the agent picker, the skill, or
the same prompt text. [Prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files).
No handoff button is required: a suggested next role or Markdown packet does not
itself run an agent. GitHub cloud does not support the VS Code `handoffs` field,
so these profiles deliberately avoid it.

## Local commands the agents can use

Run from this repository root, with Python installed as described in the README.

```sh
python -m rose extract --source ../upstream --output build/evidence.json
python -m rose validate --source ../upstream --model model/ontology.json
python -m rose build --source ../upstream --output build
python -m rose query 'Transaction'
python -m rose query 'CTR'
python orchestration/check.py orchestration/run.example.json
python -m unittest discover -s orchestration -p 'test_*.py' -v
```

The commands above are examples, not results. Keep exact command output in a
run-specific log when executing them. Query is a deterministic model search; it
does not answer arbitrary questions using an LLM. CLI success checks traceability
within the supported subset, not full program equivalence or compliance.

## A first bounded cycle

Ask Satya:

> Use Umberto, Peter, Boris, and Eric for one review of the transaction/GL/CTR
> model. First verify available tools. Follow orchestration/workflow.md, preserve
> all evidence and disagreements, and save a run ledger. Do not modify upstream
> COBOL or publish. Stop after at most three iterations. Tell me which agent
> calls and checks actually ran.

Without delegation, follow the manual sequence in the workflow and pass the same
ledger and context packets to each role. With delegation, inspect the recorded
tool calls. The run ledger is inspectable collaboration memory, not a trusted
audit system; an unverified JSON assertion is not proof a tool ran.

## Verification status and references

The repository's automated checks cover the model/evidence contracts and ledger
invariants. They do **not** launch Copilot or validate host UI discovery. Treat
live host acceptance as a separate smoke test: select each role, run one read-only
trace, inspect its citations, exercise one actual delegation or manual handoff,
then save the host/version and genuine transcript reference in a new ledger.

Configuration was checked against official documentation on **2026-10-18**:

- [GitHub custom-agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents)
- [VS Code subagents](https://code.visualstudio.com/docs/agents/run/subagents)
- [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files)
- [GitHub project skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Creating a Copilot skill](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)

These are compatibility references, not a guarantee that every account, policy,
model, or host exposes every capability.
