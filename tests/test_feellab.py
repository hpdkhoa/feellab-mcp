"""Feel Lab's own checks, on the example timelines (examples/demo_timelines.py): a game with every answer passes
every measured item; a bare prototype fails the ones it lacks; the contract refuses broken timelines."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from feellab import evaluate as E, measure as M, metrics as MX, timeline as T  # noqa: E402


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    d = tmp_path_factory.mktemp("tl")
    subprocess.run([sys.executable, str(ROOT / "examples" / "demo_timelines.py"), str(d)], check=True, capture_output=True)
    return E.load_folder(d)


def test_the_checklist_is_whole():
    c = E.checklist()
    assert len(c["items"]) == 82
    ids = [i["id"] for i in c["items"]]
    assert len(ids) == len(set(ids))
    for i in c["items"]:
        for m in i["measures"]:
            assert m in MX.METRICS, (i["id"], m)
    for m, v in MX.METRICS.items():
        assert v[5], m                     # every rule names its source or why it is an estimate


def test_a_game_with_every_answer_passes(runs):
    r = E.judge(runs["Juicy"])
    assert r["summary"]["fail"] == 0 and r["summary"]["pass"] == 23, [(i["id"], i["verdict"]) for i in r["items"] if i["verdict"] not in ("pass", "person")]


def test_a_bare_prototype_fails_what_it_lacks(runs):
    v = {i["id"]: i["verdict"] for i in E.judge(runs["Bare"])["items"]}
    for item in ("A5", "A7", "B1", "B2", "B3", "B10", "C3", "C6", "D1", "D2"):
        assert v[item] == "fail", item
    assert v["A2"] == "pass" and v["C1"] == "pass"


def test_measures(runs):
    j = runs["Juicy"]
    assert M.av_sync(j["fire_wall"]) == 0.0
    peak, back = M.kick(j["fire_wall"], 0.1, 1.0)
    assert peak > 0.3 and back is not None
    assert M.shake(j["blast_5"])[0] > M.shake(j["blast_50"])[0] * 3
    assert 1.0 < M.bob(j["walk"]) < 5.0
    assert M.latency(runs["Bare"]["fire_zombie"], "damage_dealt", None, "marker", None) == 170.0


def test_rows_follow_the_row_format(runs):
    rows = E.rows("Juicy", runs["Juicy"])
    assert rows and all(set(r) >= {"weapon", "action", "metric", "value"} and r["metric"].startswith("feel.") for r in rows)


def test_the_contract_refuses_broken_timelines():
    assert T.check({"scene": "x", "subject": "y", "frames": [], "events": []})
    bad = {"scene": "x", "subject": "y", "frames": [{"t": 0, "dt": 16, "cam": [0] * 7}, {"t": 0.1, "dt": 16, "cam": [0] * 6}],
           "events": [{"t": 0.0, "kind": "boom"}]}
    text = " ".join(T.check(bad))
    assert "cam is" in text and "kind must be" in text


def test_a_camera_facing_yaw_180_does_not_shake_by_wrapping():
    # the ToangTown probe faces yaw 180: its frames read 179.9 and -179.9 with no turn at all
    frames = [{"t": i / 60, "dt": 16.7, "cam": [0, 0, 150, 0.0, (179.95 if i % 2 else -179.95), 0.0, 90]} for i in range(60)]
    tl = {"scene": "blast_5", "subject": "x", "frames": frames, "events": []}
    assert M.shake(tl)[0] < 0.2


def test_a_recoil_climb_is_not_a_shake():
    # ten shots, each lifting the view 0.4 degrees and staying there (a climb, as ToangTown's AR-15 does): no shake
    frames = [{"t": i / 60, "dt": 16.7, "cam": [0, 0, 150, -0.4 * min(10, i // 9), 0.0, 0.0, 90]} for i in range(120)]
    tl = {"scene": "fire_wall", "subject": "x", "frames": frames, "events": []}
    assert M.shake(tl)[0] < 0.01


def test_a_climb_at_a_low_frame_rate_is_not_a_shake():
    # ToangTown's editor game at 33 frames a second: a 0.91 degree step every 6 frames, and a tick recorded twice
    frames, t = [], 0.0
    for i in range(60):
        frames.append({"t": t, "dt": 30, "cam": [0, 0, 150, 0.91 * (i // 6), 180.0, 0.0, 90]})
        if i == 3:
            frames.append(dict(frames[-1]))
        t += 0.03
    tl = {"scene": "fire_wall", "subject": "x", "frames": frames, "events": []}
    assert M.shake(tl)[0] == 0.0


def test_a_project_names_its_own_sounds(tmp_path):
    frames = [{"t": i / 60, "dt": 16.7, "cam": [0, 0, 150, 0, 0, 0, 90]} for i in range(30)]
    tl = {"contract": "feellab-timeline/1", "scene": "dry_fire", "subject": "G", "frames": frames,
          "events": [{"t": 0.1, "kind": "sound", "name": "sfx_wpn_hgn_reload_01_slideLock_Cue"}]}
    (tmp_path / "G_dry_fire_timeline.json").write_text(json.dumps(tl))
    assert MX.value("feel.dry_click", E.load_folder(tmp_path)["G"]) == 0
    (tmp_path / "feel_rules.json").write_text(json.dumps({"dry": "slidelock"}))
    assert MX.value("feel.dry_click", E.load_folder(tmp_path)["G"]) == 1


def test_shell_pairs_each_shot_once():
    from feellab import measure as M
    ev = [{"t": 0.0, "kind": "shot", "name": "s"}, {"t": 0.1, "kind": "shot", "name": "s"},
          {"t": 0.12, "kind": "fx", "name": "case", "tags": ["shell"]}]
    tl = {"frames": [], "events": ev}
    assert M.per_cause(tl, "shot", None, "fx", "shell") == 1.0          # one case answers both shots
    assert M.per_cause(tl, "shot", None, "fx", "shell", window_s=1.0, once=True) == 0.5
    pump = {"frames": [], "events": [{"t": 0.0, "kind": "shot", "name": "s"}, {"t": 0.6, "kind": "fx", "name": "c", "tags": ["shell"]}]}
    assert M.per_cause(pump, "shot", None, "fx", "shell", window_s=1.0, once=True) == 1.0


def test_kick_of_one_shot():
    from feellab import metrics as MX
    fr = [{"t": 0.0, "dt": 16, "cam": [0, 0, 0, 0, 0, 0, 90]}, {"t": 0.05, "dt": 16, "cam": [0, 0, 0, 3.0, 0, 0, 90]},
          {"t": 0.6, "dt": 16, "cam": [0, 0, 0, 0.1, 0, 0, 90]}]
    tl = {"frames": fr, "events": [{"t": 0.0, "kind": "shot", "name": "s"}]}
    assert MX.METRICS["feel.kick_deg"][1](tl) == 3.0
