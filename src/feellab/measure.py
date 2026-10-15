"""Measures from a timeline (timeline.py): what the player got, in numbers.

Every measure is a pure function of the timeline, so a game's probe and a test can feed it the same way. Names are
the metrics the checklist's items point to (feel.<name>); each returns None when the timeline cannot say (the scene
did not have what it needs), never a guess.

How an event is recognised: by its kind, then by its tags, then by words in its name (a game that tags its events
gets exact answers; one that only names them gets the name rules below, which a project can extend)."""
import math
import re
import statistics

# words in an asset's name that say what an effect or a sound is for, when the game gave no tag
NAME_RULES = {
    "muzzle": r"muzzle|flash",
    "shell": r"shell|casing|brass|eject",
    "impact": r"impact|hit_|_hit|bullethit|ricochet|spark|dust|debris",
    "blood": r"blood|gore|splat",
    "explosion": r"explo|blast|fireball|grenade|detonat",
    "tracer": r"tracer",
    "shot": r"fire|shot|gunshot|report",
    "reload": r"reload|mag_in|mag_out|magin|magout|bolt|charge|slide|foley",
    "dry": r"dry|empty|click",
    "footstep": r"foot|step",
    "land": r"land",
    "hurt": r"hurt|pain|grunt|damage",
    "heartbeat": r"heart|breath",
}


PROJECT_RULES = {}       # a project's own names (feel_rules.json beside its timelines): {tag: regex}, set by evaluate


def tags_of(e, extra_rules=None):
    """The event's tags: its own, then what its name says by the rules (the project's, then the built-in ones)."""
    tags = set(e.get("tags") or [])
    name = (e.get("name") or "").lower()
    rules = dict(NAME_RULES)
    for k, v in list(PROJECT_RULES.items()) + list((extra_rules or {}).items()):
        rules[k] = "(?:%s)|(?:%s)" % (v, rules[k]) if k in rules else v
    for tag, pat in rules.items():
        if re.search(pat, name):
            tags.add(tag)
    return tags


def events(tl, kind=None, tag=None, rules=None):
    return [e for e in tl.get("events", []) if (kind is None or e.get("kind") in ((kind,) if isinstance(kind, str) else kind))
            and (tag is None or tag in tags_of(e, rules) or e.get("name") == tag)]


def _ms(a, b):
    return round((b - a) * 1000.0, 1)


def _cam(tl):
    """The camera a frame, each moment once (a probe can record a tick twice)."""
    out = []
    for f in tl.get("frames", []):
        if out and f["t"] <= out[-1][0] + 1e-9:
            continue
        out.append((f["t"], f["cam"]))
    return out


def _ang(a, b):
    """The smallest turn between two angles (degrees)."""
    return (b - a + 180.0) % 360.0 - 180.0


# ------------------------------------------------------------------ latency
def latency(tl, cause_kind, cause_tag, answer_kind, answer_tag, window_s=0.5, rules=None):
    """For each cause, the time to the first answer after it (ms); the worst of them, or None without causes."""
    causes = events(tl, cause_kind, cause_tag, rules)
    answers = events(tl, answer_kind, answer_tag, rules)
    if not causes:
        return None
    worst = 0.0
    for c in causes:
        after = [a["t"] for a in answers if c["t"] - 1e-6 <= a["t"] <= c["t"] + window_s]
        if not after:
            return float("inf")
        worst = max(worst, _ms(c["t"], min(after)))
    return worst


def av_sync(tl, rules=None):
    """For each shot, the gap between its flash and its sound (ms, the worst): the eye and the ear notice past about
    45 ms of sound late or 125 ms early (ITU-R BT.1359)."""
    shots = events(tl, "shot")
    if not shots:
        return None
    flashes = [e["t"] for e in events(tl, "fx", "muzzle", rules)]
    sounds = [e["t"] for e in events(tl, "sound", "shot", rules)]
    if not flashes or not sounds:
        return None
    worst = 0.0
    for s in shots:
        f = min(flashes, key=lambda x: abs(x - s["t"]))
        a = min(sounds, key=lambda x: abs(x - s["t"]))
        worst = max(worst, abs(_ms(f, a)))
    return worst


# ------------------------------------------------------------------ the camera
def kick(tl, start=None, end=None):
    """The camera's turn away from where it started, over a span: (the peak in degrees, the seconds it takes to come
    back within a tenth of that peak after the span ends; None when it does not come back)."""
    cam = _cam(tl)
    if len(cam) < 3:
        return None, None
    t0 = start if start is not None else cam[0][0]
    t1 = end if end is not None else cam[-1][0]
    before = [c for t, c in cam if t < t0 - 1e-6]                    # where the camera was just before the cause
    base = before[-1] if before else cam[0][1]

    def off(c):
        return math.hypot(_ang(base[3], c[3]), _ang(base[4], c[4]))
    peak = max((off(c) for t, c in cam if t0 <= t <= t1), default=0.0)
    if peak <= 1e-3:
        return 0.0, None                                              # no kick: nothing to come back from
    back = next((t - t1 for t, c in cam if t > t1 and off(c) <= 0.1 * peak), None)
    return round(peak, 3), (round(back, 3) if back is not None else float("inf"))     # inf: it never came back


def shake(tl, start=None, end=None, window=None):
    """The camera's shake over a span: how much it zig-zags from one frame to the next (half the second difference of
    its turn and its move, counted only where the motion turns back), the 75th percentile over the span's frames. A
    shake goes back and forth every frame or two; a recoil's climb or a turn of the head goes one way, so it never
    counts, however few frames a second the game draws. (degrees, cm)"""
    cam = _cam(tl)
    if len(cam) < 5:
        return None, None
    t0 = start if start is not None else cam[0][0]
    t1 = end if end is not None else cam[-1][0]
    # angles unwrapped against the first frame: a camera facing yaw 180 crosses from +180 to -180 without turning
    ref = cam[0][1]
    c = [(t, [x[0], x[1], x[2], _ang(ref[3], x[3]), _ang(ref[4], x[4]), _ang(ref[5], x[5])]) for t, x in cam]
    rot, loc = [], []
    for i in range(1, len(c) - 1):
        t = c[i][0]
        if not (t0 <= t <= t1):
            continue
        a, b, n_ = c[i - 1][1], c[i][1], c[i + 1][1]

        def turns(ks):
            # a shake turns back: the move into this frame and the move out of it point opposite ways
            return any((b[k] - a[k]) * (n_[k] - b[k]) < 0 and abs(b[k] - a[k]) > 1e-4 and abs(n_[k] - b[k]) > 1e-4 for k in ks)
        z = [b[k] - (a[k] + n_[k]) / 2.0 for k in range(6)]
        rot.append(math.sqrt(z[3] ** 2 + z[4] ** 2 + z[5] ** 2) if turns((3, 4, 5)) else 0.0)
        loc.append(math.sqrt(z[0] ** 2 + z[1] ** 2 + z[2] ** 2) if turns((0, 1, 2)) else 0.0)
    if not rot:
        return None, None

    def p75(v):
        v = sorted(v)
        return v[min(len(v) - 1, int(0.75 * len(v)))]
    return round(p75(rot), 4), round(p75(loc), 3)


def bob(tl):
    """The camera's up and down while walking: its height's range once its slow drift is taken away (cm)."""
    cam = _cam(tl)
    if len(cam) < 10:
        return None
    z = [c[2] for t, c in cam]
    n = len(z)
    drift = [(z[0] + (z[-1] - z[0]) * i / (n - 1)) for i in range(n)]
    d = [a - b for a, b in zip(z, drift)]
    return round(max(d) - min(d), 3)


def fov_change(tl):
    """The field of view's range over the scene (degrees)."""
    cam = _cam(tl)
    if not cam:
        return None
    f = [c[6] for t, c in cam]
    return round(max(f) - min(f), 3)


# ------------------------------------------------------------------ presence and matching
def count(tl, kind, tag=None, rules=None):
    return len(events(tl, kind, tag, rules))


def per_cause(tl, cause_kind, cause_tag, answer_kind, answer_tag, window_s=0.3, rules=None):
    """The share of causes that got at least one answer within the window (1.0: every one)."""
    causes = events(tl, cause_kind, cause_tag, rules)
    if not causes:
        return None
    answers = [a["t"] for a in events(tl, answer_kind, answer_tag, rules)]
    got = sum(1 for c in causes if any(c["t"] - 1e-6 <= a <= c["t"] + window_s for a in answers))
    return round(got / len(causes), 3)


def rate(tl, kind, tag=None, rules=None):
    """Events a second over the scene."""
    cam = _cam(tl)
    span = (cam[-1][0] - cam[0][0]) if len(cam) > 1 else 0.0
    if span <= 0:
        return None
    return round(count(tl, kind, tag, rules) / span, 3)


# ------------------------------------------------------------------ smoothness
def hitch(tl, around_kind=None, window_s=0.25):
    """The longest frame against the median frame (1.0: even), over the scene or round one kind of event."""
    frames = tl.get("frames", [])
    if len(frames) < 5:
        return None
    med = statistics.median(f["dt"] for f in frames) or 1e-6
    if around_kind:
        ts = [e["t"] for e in tl.get("events", []) if e.get("kind") == around_kind]
        if not ts:
            return None
        sel = [f["dt"] for f in frames if any(abs(f["t"] - t) <= window_s for t in ts)]
    else:
        sel = [f["dt"] for f in frames]
    return round(max(sel) / med, 3) if sel else None
