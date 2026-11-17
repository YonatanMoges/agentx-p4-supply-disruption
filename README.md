# P4 Supply Disruption Responder

**First-place project — AgentX@CCI 2026, University of Sharjah**

A five-agent workflow prototype for responding to supplier disruptions. It monitors evidence of delays, assesses potential inventory and production impact, compares response options, and passes consequential procurement decisions through safety and approval checks. An accompanying Streamlit dashboard turns saved practice-run outputs into an understandable timeline and agent-by-agent explanation.

## How it works

| Agent | Responsibility |
| --- | --- |
| 1 — Orchestrator | Coordinates monitoring cycles and routes information between agents. |
| 2 — Disruption detector | Checks supplier communications and other signals, verifies disruptions, and flags suspicious instructions. |
| 3 — Impact analyst | Estimates shortages, affected manufacturing orders, and revenue at risk. |
| 4 — Response planner | Compares alternatives and recommends buying, waiting, or escalating. |
| 5 — Procurement and approval | Applies procurement checks, requests approval where required, and executes permitted actions. |

The system was implemented in **n8n** using APIs and AI-assisted steps. The **Streamlit** dashboard displays the results in human-readable form instead of requiring an evaluator to inspect individual workflow nodes.

## Repository layout

```text
dashboard/
  app.py                       Streamlit dashboard and saved practice-run examples
  requirements.txt             Dashboard dependencies
workflows/
  agent_01_orchestrator.json
  agent_02_disruption_detector.json
  agent_03_impact_analyst.json   Synthetic offline demonstration data
  agent_04_response_planner.json
  agent_05_procurement_approval.json
docs/
  setup-and-limitations.md     Import notes, security, and demonstration scope
```

## Run the dashboard

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Select a saved practice run from the sidebar. The dashboard supports pasted or uploaded n8n output and an optional simulator connection. **The saved examples are demonstration outputs, not a live connection to the simulation environment.**

## Demonstrated safeguards

- Disruption claims are checked before action.
- Suspicious email instructions (including approval-bypass attempts) are flagged.
- Procurement can be blocked or escalated instead of automatically placing an order.
- Buyers remain responsible for approvals and ambiguous decisions.
- The dashboard shows what each agent found, what it decided, and when human review was required.

## Scope and attribution

This is a **competition prototype**, not a production supply-chain system. The n8n exports require the event simulator/tool API, renewed local credentials, and re-mapping of subworkflow IDs before they can run in a new n8n instance. The sample data and monetary impacts shown in the dashboard come from practice scenarios, not actual company sales or verified savings.

Built as a five-member team project at the University of Sharjah by **Yonatan Moges, Mohamed Nasser Moneim, Mohamed Ahmed, Muhammad Azhar, and Rafi Ibne Nur**. The team won first place at **AgentX@CCI 2026**. Individual contributions and code ownership should not be inferred from this portfolio copy.

The published exports have been sanitized; no API keys or n8n credential bindings are provided. Agent 3's original embedded competition spreadsheet has been replaced with six entirely synthetic demonstration rows and is **not** a complete offline replica. See [setup and limitations](docs/setup-and-limitations.md).
