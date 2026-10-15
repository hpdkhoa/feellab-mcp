"""feellab <command>
  serve                          the MCP server (also: feellab-mcp)
  checklist [group]              the checklist
  judge <folder> [subject]       judge a folder of timelines (prints the report)
  check <timeline.json>          a timeline against the contract
  demo <folder>                  example timelines of two made-up games"""
import json
import sys


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "serve":
        from .server import main as serve
        serve()
        return 0
    from . import evaluate as E, timeline as T
    if a[0] == "checklist":
        c = E.checklist()
        for i in c["items"]:
            if len(a) < 2 or i["group"] == a[1]:
                print("%-4s %-8s %s: %s" % (i["id"], i["check"], i["name"], i["expect"]))
        return 0
    if a[0] == "judge":
        for s, tls in E.load_folder(a[1], a[2] if len(a) > 2 else None).items():
            print(E.report_md(s, E.judge(tls)))
        return 0
    if a[0] == "demo":
        from .demo import game
        game(a[1], "Juicy", True)
        game(a[1], "Bare", False)
        print("written to", a[1])
        return 0
    if a[0] == "check":
        from pathlib import Path
        bad = T.check(json.loads(Path(a[1]).read_text(encoding="utf-8-sig")))
        print(json.dumps({"ok": not bad, "problems": bad}, indent=1))
        return 0 if not bad else 1
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
