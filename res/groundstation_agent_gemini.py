#!/usr/bin/env python
"""LLM agent that plans the ground-station schedule, via the Gemini API.

Same propose -> validate -> revise loop as the post: the model never enforces
the constraints, the validator does, and feeds violations back. Reuses `passes`
from groundstation_schedule_demo.py.
"""
import json
from collections import defaultdict
from google import genai
from google.genai import types

MODEL = "gemini-3-flash-preview"
KEYFILE = "/Users/paolo/.local/share/opencode/auth.json"


def api_key():
    return json.load(open(KEYFILE))["google"]["key"]


SUBMIT = types.FunctionDeclaration(
    name="submit_schedule",
    description="Submit the chosen contacts as a list of pass IDs. No two chosen "
                "passes may overlap on the same station (plus a 300s slew gap) or "
                "on the same satellite.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"pass_ids": types.Schema(
            type="ARRAY", items=types.Schema(type="INTEGER"))},
        required=["pass_ids"]),
)

PROMPT = (
    "You are scheduling ground-station contacts. Maximize total weighted contact "
    "time. Constraints: a station runs one contact at a time with a 300-second "
    "slew gap between contacts; a satellite talks to one station at a time. Call "
    "submit_schedule with the pass IDs you choose. Catalog of candidate passes "
    "(times in seconds from epoch):\n\n"
)


def check(passes, chosen, slew_gap=300):
    violations, by_station, by_sat = [], defaultdict(list), defaultdict(list)
    for i in chosen:
        p = passes[i]
        for j, (s, e) in by_station[p.station]:
            if not (p.end + slew_gap <= s or p.start >= e + slew_gap):
                violations.append(f"passes {i} and {j} overlap at station {p.station}")
        for j, (s, e) in by_sat[p.sat]:
            if not (p.end <= s or p.start >= e):
                violations.append(f"passes {i} and {j} overlap on satellite {p.sat}")
        by_station[p.station].append((i, (p.start, p.end)))
        by_sat[p.sat].append((i, (p.start, p.end)))
    return violations


def llm_schedule(passes, max_rounds=6):
    client = genai.Client(api_key=api_key())
    catalog = [{"id": i, "sat": p.sat, "station": p.station,
                "start": round(p.start), "end": round(p.end),
                "weight": round(p.weight)} for i, p in enumerate(passes)]
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[SUBMIT])],
        tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(
            mode="ANY", allowed_function_names=["submit_schedule"])))
    contents = [types.Content(role="user",
                              parts=[types.Part(text=PROMPT + json.dumps(catalog))])]
    chosen = []
    for r in range(max_rounds):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
        part = resp.candidates[0].content.parts[0]
        fc = part.function_call
        chosen = [int(x) for x in fc.args["pass_ids"]]
        violations = check(passes, chosen)
        weight = sum(passes[i].weight for i in chosen)
        print(f"[gemini] round {r}: {len(chosen)} contacts, weighted {weight:.0f}, "
              f"{len(violations)} violations")
        if not violations:
            return chosen
        contents.append(resp.candidates[0].content)
        contents.append(types.Content(role="user", parts=[types.Part.from_function_response(
            name="submit_schedule",
            response={"feasible": False,
                      "fix_these_overlaps": violations[:40]})]))
    return chosen


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "res")
    from groundstation_schedule_demo import passes, opt_obj, opt_pick, greedy_obj
    picked = llm_schedule(passes)
    weight = sum(passes[i].weight for i in picked)
    feasible = not check(passes, picked)
    print(f"\n[gemini] final: {len(picked)} contacts, weighted {weight:.0f}, "
          f"feasible={feasible}")
    print(f"[gemini] optimal (CP-SAT): {len(opt_pick)} contacts, weighted {opt_obj:.0f}")
    print(f"[gemini] greedy:           weighted {greedy_obj:.0f}")
    print(f"[gemini] agent reaches {weight / opt_obj:.1%} of the optimum")
