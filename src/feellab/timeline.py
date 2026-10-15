"""The timeline contract (feellab-timeline/1): what a game's probe records while it plays one scene, for Feel Lab to
measure. A timeline is one JSON file a scene:

{"contract": "feellab-timeline/1",
 "scene": "fire_wall",                    which standard scene this is (scenes.json), or the game's own name
 "subject": "Rifle_M4",                   the weapon (or whatever the scene is about)
 "params": {"distance_m": 5},             the scene's settings as the probe ran it
 "frames": [{"t": 0.0, "dt": 16.6,        seconds from the scene's start; the frame's length in ms
             "cam": [x, y, z, pitch, yaw, roll, fov]}],   the player's camera in the world (cm, degrees)
 "events": [{"t": 0.21, "kind": "sound", "name": "sfx_wpn_ar_fire_01", "at": [x, y, z], "value": 1.0, "tags": ["shot"]}]}

Event kinds (a probe reports the ones it has; Feel Lab judges what it gets):
  input        the probe pressed something (name: fire, reload, jump, ...)
  shot         a round left the gun (value: rounds; tags: calibre)
  sound        a sound started (name: the asset; value: volume; tags: what it is for, when the game knows)
  fx           a visual effect started (name: the asset; tags: muzzle, shell, impact, blood, explosion, tracer, ...)
  decal        a mark was left on a surface (tags: the surface)
  impact       a round met the world or a body (tags: the surface or "flesh"; value: the damage)
  marker       a hit marker was shown (tags: hit, kill, headshot)
  damage_dealt the player's hit landed (value: the damage; tags: headshot, kill)
  damage_taken the player was hurt (value: the damage; at: where the hit came from)
  camera       a camera effect started (name: shake, flinch, kick; value: its size)
  ui           a screen effect started or changed (name: damage_indicator, blood_overlay, low_health, ...)
  debug        something drawn for developers only (a debug point where an impact should be)
Positions in cm, the world's axes; time in seconds from the scene's start."""
import json
import math
from pathlib import Path

CONTRACT = "feellab-timeline/1"
KINDS = ("input", "shot", "sound", "fx", "decal", "impact", "marker", "damage_dealt", "damage_taken", "camera", "ui", "debug")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check(tl):
    """Every problem with a timeline, as sentences; empty when it follows the contract."""
    bad = []
    if not isinstance(tl, dict):
        return ["a timeline is a JSON object"]
    if tl.get("contract", CONTRACT) != CONTRACT:
        bad.append("contract is %r; Feel Lab reads %s" % (tl.get("contract"), CONTRACT))
    for k in ("scene", "subject"):
        if not isinstance(tl.get(k), str) or not tl.get(k):
            bad.append("%s is required (a string)" % k)
    frames = tl.get("frames")
    if not isinstance(frames, list) or len(frames) < 2:
        bad.append("frames: at least two frames are needed")
        frames = []
    last = -1.0
    for i, f in enumerate(frames):
        if not isinstance(f, dict) or not _num(f.get("t")) or not _num(f.get("dt")):
            bad.append("frames[%d]: t and dt are numbers" % i)
            continue
        if f["t"] < last:
            bad.append("frames[%d]: t goes back in time" % i)
        last = f["t"]
        cam = f.get("cam")
        if not (isinstance(cam, list) and len(cam) == 7 and all(_num(x) for x in cam)):
            bad.append("frames[%d]: cam is [x, y, z, pitch, yaw, roll, fov]" % i)
        if len(bad) > 20:
            break
    events = tl.get("events")
    if not isinstance(events, list):
        bad.append("events: a list is required (it may be empty)")
        events = []
    for i, e in enumerate(events):
        if not isinstance(e, dict) or not _num(e.get("t")):
            bad.append("events[%d]: t is a number" % i)
            continue
        if e.get("kind") not in KINDS:
            bad.append("events[%d]: kind must be one of %s" % (i, KINDS))
        if "at" in e and e["at"] is not None and not (isinstance(e["at"], list) and len(e["at"]) == 3 and all(_num(x) for x in e["at"])):
            bad.append("events[%d]: at is [x, y, z]" % i)
        if "tags" in e and not (isinstance(e["tags"], list) and all(isinstance(t, str) for t in e["tags"])):
            bad.append("events[%d]: tags is a list of strings" % i)
        if len(bad) > 40:
            break
    return bad


def load(path):
    tl = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    bad = check(tl)
    if bad:
        raise ValueError("%s breaks the timeline contract: %s" % (path, "; ".join(bad[:6])))
    return tl
