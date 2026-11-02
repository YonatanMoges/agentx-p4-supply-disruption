#!/usr/bin/env python3
"""
Minimal LLM agent loop for any problem's mock API (starter code - teams replace it with their own agent).

    pip install anthropic pandas openpyxl
    export ANTHROPIC_API_KEY=...
    python run_agent.py --problem 1 --scenario practice_01
    python run_agent.py --problem 8 --scenario practice
    python run_agent.py --problem 7 --scenario practice_02 --max-turns 300

It gives the model the API's tool definitions, executes each tool call through api.call()
and stops when the model stops calling tools or the turn limit is reached. The action log
is written to runs/<problem>/<scenario>/actions.jsonl and api.run_summary() is printed.
"""
import argparse
import importlib
import json

PROBLEMS = {
    1: ("plant_api", "PlantAPI", "p1_maintenance/data/public"),
    2: ("p2_terminal_api", "TerminalAPI", "data/P2_Container_Terminal_Data.xlsx"),
    3: ("p3_energy_api", "EnergyAPI", "data/P3_Energy_Agent_Data.xlsx"),
    4: ("p4_supply_api", "SupplyAPI", "data/P4_Supply_Disruption_Data.xlsx"),
    5: ("p5_bottling_api", "BottlingAPI", "data/P5_Defect_Detective_Data.xlsx"),
    6: ("p6_permit_api", "PermitAPI", "data/P6_Permit_Guardian_Data.xlsx"),
    7: ("p7_campus_api", "CampusAPI", "data/P7_Smart_Campus_Data.xlsx"),
    8: ("p8_career_api", "CareerAPI", "data/P8_Career_Navigator_Data.xlsx"),
    9: ("p9_services_api", "ServicesAPI", "data/P9_Student_Services_Data.xlsx"),
    10: ("p10_employment_api", "EmploymentAPI", "data/P10_Graduate_Employment_Data.xlsx"),
    11: ("p11_tto_api", "TTOAPI", "data/P11_Commercialization_Scout_Data.xlsx"),
    12: ("p12_permit_review_api", "PermitReviewAPI", "data/P12_Permit_Reviewer_Data.xlsx"),
}

SYSTEM = ("You are an operations agent working through the tools provided. Read the problem statement's rules, "
          "use the tools to gather facts before acting, never break a hard constraint, and keep going until the "
          "scenario is finished (the clock reports finished=true, or the queue returns done=true).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", type=int, required=True, choices=sorted(PROBLEMS))
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--data")
    ap.add_argument("--key", help="Organizers only: answer-key workbook for hidden scenarios (Problem 1: the hidden scenario folder)")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--max-turns", type=int, default=150)
    a = ap.parse_args()

    import anthropic
    mod, cls, data = PROBLEMS[a.problem]
    if a.problem == 1:                      # Problem 1 kit: different constructor and schema list
        import sys
        sys.path.insert(0, "p1_maintenance")
        m = importlib.import_module(mod)
        api = m.PlantAPI(a.data or data, a.scenario, **(dict(scenario_dir=a.key) if a.key else {}))
        tools = m.TOOL_SCHEMAS
    else:
        API = getattr(importlib.import_module(mod), cls)
        kw = dict(key_xlsx=a.key) if a.key else {}
        api = API(a.scenario, a.data or data, **kw)
        tools = API.tool_schemas()
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Scenario {a.scenario} of Problem {a.problem} has started. Begin."}]

    for turn in range(a.max_turns):
        resp = client.messages.create(model=a.model, max_tokens=4096, system=SYSTEM, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        calls = [b for b in resp.content if b.type == "tool_use"]
        for b in resp.content:
            if b.type == "text" and b.text.strip():
                print(f"[{turn}] {b.text.strip()[:300]}")
        if not calls:
            break
        results = []
        for c in calls:
            out = api.call(c.name, c.input)
            txt = json.dumps(out, ensure_ascii=False, default=str)
            if len(txt) > 20000:
                txt = txt[:20000] + " ...[truncated - narrow your query]"
            results.append({"type": "tool_result", "tool_use_id": c.id, "content": txt, "is_error": isinstance(out, dict) and "error" in out})
        messages.append({"role": "user", "content": results})

    if hasattr(api, "run_summary"):
        print(json.dumps(api.run_summary(), indent=2, ensure_ascii=False, default=str)[:5000])
    else:
        print("Run finished. Score it with: python p1_maintenance/score.py --public p1_maintenance/data/public "
              f"--key p1_maintenance/data/private/answer_keys/{a.scenario}.json --actions runs/{a.scenario}/actions.jsonl")


if __name__ == "__main__":
    main()
