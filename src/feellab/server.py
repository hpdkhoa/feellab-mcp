"""Feel Lab over MCP. Run: feellab-mcp (or python -m feellab serve)."""
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from . import __version__, evaluate as E, metrics as MX, timeline as T
from .config import out

mcp = MCPServer("feellab", title="Feel Lab", version=__version__, instructions=(
    "Feel Lab checks how a first-person shooter feels, interaction by interaction: a shot (its flash, its sound, its "
    "kick, its shake, the case it throws), a hit (the impact, its sound, the hole, the marker, the blood), a hit taken "
    "(the flinch, the indicator, the sound), a blast near and far, a step. Your game's probe plays standard scenes and "
    "writes a timeline of what happened, frame by frame (the camera, every sound, effect and mark); Feel Lab measures "
    "latency, kick, shake, presence, match and smoothness from it and judges each checklist item. Items no timeline "
    "can show are left for a person, with what to look for."))


def _err(f, *a, **k):
    try:
        return f(*a, **k)
    except (ValueError, FileNotFoundError, KeyError) as e:
        raise ToolError(str(e))


@mcp.tool()
def list_checklist(group: Annotated[str | None, Field(description="A to J, or leave out for all")] = None) -> dict:
    """The checklist: every interaction, what the player should get, and how it is checked (measured or by a person)."""
    c = E.checklist()
    items = [i for i in c["items"] if not group or i["group"] == group]
    return {"groups": c["groups"], "items": items}


@mcp.tool()
def list_scenes() -> dict:
    """The standard scenes a probe plays, one timeline each, and what each asks it to do."""
    return E.scenes()


@mcp.tool()
def list_metrics() -> dict:
    """Every metric: its scene, unit, which way is better, its rule and the rule's source (estimate or evidence)."""
    return {m: {"scenes": list(MX.scenes_of(m)), "unit": v[2], "better": v[3], "rule": list(v[4]), "source": v[5], "estimate": v[6]}
            for m, v in MX.METRICS.items()}


@mcp.tool()
def check_timeline(path: str) -> dict:
    """A timeline file against the contract (feellab-timeline/1): every problem, or none."""
    import json
    from pathlib import Path
    bad = T.check(json.loads(Path(path).read_text(encoding="utf-8-sig")))
    return {"ok": not bad, "problems": bad}


@mcp.tool()
def judge_folder(folder: Annotated[str, Field(description="a folder of <subject>_<scene>_timeline.json files")],
                 subject: str | None = None) -> dict:
    """Each subject's scenes judged against the checklist: every measured item's values, rules and verdict, a
    summary, and a Markdown report written beside them."""
    runs = _err(E.load_folder, folder, subject)
    res = {}
    for s, tls in runs.items():
        r = E.judge(tls)
        p = out("reports") / ("%s.md" % s)
        p.write_text(E.report_md(s, r), encoding="utf-8")
        res[s] = {"summary": r["summary"], "report": str(p), "items": [i for i in r["items"] if i["verdict"] != "person"]}
    return res


@mcp.tool()
def gate_rows(folder: str, subject: str) -> list:
    """The metrics as rows for a gate (Weapon Lab's row format): subject, scene, metric, value."""
    runs = _err(E.load_folder, folder, subject)
    if subject not in runs:
        raise ToolError("no timelines for %s in %s" % (subject, folder))
    return E.rows(subject, runs[subject])


def main():
    mcp.run()
