"""Where Feel Lab keeps its data (the checklist, the scenes) and writes its reports (FEELLAB_OUT, ~/.feellab)."""
import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
DATA = PACKAGE / "data"


def out(*parts):
    p = Path(os.environ.get("FEELLAB_OUT") or Path.home() / ".feellab").joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p
