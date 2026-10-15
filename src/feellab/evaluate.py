"""A run's timelines judged against the checklist: each measured item's metrics with their values and rules, each
item's verdict (pass, fail, or not measured), and rows for a gate (the probe contract's row format)."""
import json
from pathlib import Path

from . import metrics as MX
from . import timeline as T
from .config import DATA


def checklist():
    return json.loads((DATA / "checklist.json").read_text(encoding="utf-8"))


def scenes():
    return json.loads((DATA / "scenes.json").read_text(encoding="utf-8"))


def load_folder(folder, subject=None):
    """{subject: {scene: timeline}} from a folder of <subject>_<scene>_timeline.json files (the contract checked). A
    feel_rules.json beside them ({tag: regex over asset names, lower case}) tells Feel Lab what the game's own sounds
    and effects are for, where their names do not say it (a dry click named after a slide lock)."""
    from . import measure as M
    rules = Path(folder) / "feel_rules.json"
    M.PROJECT_RULES.clear()
    if rules.exists():
        M.PROJECT_RULES.update(json.loads(rules.read_text(encoding="utf-8")))
    out = {}
    for p in sorted(Path(folder).glob("*_timeline.json")):
        tl = T.load(p)
        if subject and tl["subject"] != subject:
            continue
        out.setdefault(tl["subject"], {})[tl["scene"]] = tl
    return out


def judge(timelines):
    """One subject's scenes ({scene: timeline}) against every measured item."""
    vals = {m: MX.value(m, timelines) for m in MX.METRICS}
    items = []
    for it in checklist()["items"]:
        if not it["measures"]:
            items.append({"id": it["id"], "name": it["name"], "verdict": "person", "how": it.get("how")})
            continue
        res = []
        for m in it["measures"]:
            scene, _fn, unit, _better, rule, source, est = MX.METRICS[m]
            v = vals[m]
            res.append({"metric": m, "value": (None if v == float("inf") else v), "never": v == float("inf"), "unit": unit,
                        "rule": list(rule), "pass": MX.holds(m, v) if v != float("inf") else False, "source": source, "estimate": est})
        if all(r["pass"] is None for r in res):
            verdict = "not measured"
        elif all(r["pass"] for r in res if r["pass"] is not None) and not any(r["pass"] is None for r in res):
            verdict = "pass"
        elif any(r["pass"] for r in res):
            verdict = "partial"
        else:
            verdict = "fail"
        items.append({"id": it["id"], "name": it["name"], "expect": it["expect"], "verdict": verdict, "measures": res})
    return {"items": items, "summary": {k: sum(1 for i in items if i["verdict"] == k) for k in ("pass", "partial", "fail", "not measured", "person")},
            "scenes": sorted(timelines)}


def rows(subject, timelines):
    """The metrics as gate rows (weapon: the subject, action: the metric's first scene)."""
    out = []
    for m in MX.METRICS:
        v = MX.value(m, timelines)
        if v is None:
            continue
        out.append({"weapon": subject, "action": MX.scenes_of(m)[0], "metric": m, "value": (999999.0 if v == float("inf") else float(v)),
                    **({"note": "never came"} if v == float("inf") else {})})
    return out


def report_md(subject, result):
    lines = ["# Feel Lab: %s" % subject, "", "Scenes: %s." % ", ".join(result["scenes"]), "",
             "Pass %(pass)d, partial %(partial)d, fail %(fail)d, not measured %(not measured)d, for a person %(person)d." % result["summary"], "",
             "| Item | Interaction | Verdict | Measures |", "|---|---|---|---|"]
    for it in result["items"]:
        if it["verdict"] == "person":
            continue
        ms = "; ".join("%s %s %s (rule %s %s)" % (r["metric"].split(".", 1)[1], "never" if r["never"] else r["value"], r["unit"] if not r["never"] else "",
                                                     r["rule"][0], r["rule"][1]) for r in it["measures"])
        lines.append("| %s | %s | %s | %s |" % (it["id"], it["name"], it["verdict"], ms))
    return "\n".join(lines) + "\n"


def self_eval(folder):
    """Feel Lab's own eval, for a gate's trust: the bare prototype's missing answers must all be caught, and the game
    with every answer must pass every measured item."""
    from .demo import game
    game(folder, "Juicy", True)
    game(folder, "Bare", False)
    runs = load_folder(folder)
    bare = {i["id"]: i["verdict"] for i in judge(runs["Bare"])["items"]}
    juicy = {i["id"]: i["verdict"] for i in judge(runs["Juicy"])["items"]}
    planted = ["A5", "A7", "A8", "A13", "B1", "B2", "B3", "B5", "B7", "B10", "C3", "C4", "C6", "D1", "D2"]
    faults = [{"fault": "the bare prototype lacks %s" % k, "caught": bare.get(k) == "fail"} for k in planted]
    good = [{"good": "the full game keeps %s" % k, "passed": v == "pass"} for k, v in juicy.items() if v != "person"]
    return {"suite": "feellab-demo-1", "caught": sum(f["caught"] for f in faults), "faults": len(faults),
            "passed_good": sum(g["passed"] for g in good), "good": len(good), "details": faults + good}
