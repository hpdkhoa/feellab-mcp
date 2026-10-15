"""Writes example timelines for two made-up games (feellab.demo): python examples/demo_timelines.py <folder>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from feellab.demo import game  # noqa: E402

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_timelines"
    game(out, "Juicy", True)
    game(out, "Bare", False)
    print("written to", out)
