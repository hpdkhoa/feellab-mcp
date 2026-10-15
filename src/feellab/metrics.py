"""Feel Lab's metrics: each one a number from one scene's timeline (or from a few scenes, for a match), with its unit,
which way is better, and the rule its checklist item holds it to. A rule's source is named; a range from game practice
rather than evidence is marked estimate, with why.

Scenes (scenes.json says what each asks the probe to do): fire_wall, fire_zombie, dry_fire, reload, hurt_front,
hurt_left, hurt_back, blast_5, blast_15, blast_50, walk."""
from . import measure as M

ITU = "ITU-R BT.1359-1 (1998): sound later than the picture by more than about 45 ms, or earlier by 125 ms, is noticed"
FRAME = "one frame at 60 frames a second is 16.7 ms: an answer on the same frame as its cause cannot be faster"
CADENCE = "walking cadence of adults: about 100 steps a minute and up (Tudor-Locke et al., 'How fast is fast enough? Walking cadence (steps/min) as a practical estimate of intensity in adults', Br J Sports Med 2018)"
GAIT_Z = "the head rises and falls about 4 to 5 cm a stride in walking (the body's centre of mass; J. Perry and J. Burnfield, Gait Analysis: Normal and Pathological Function, 2nd ed., 2010); games keep a fraction of it"
SHAKE = "screen shake as feedback: J. W. Nijman, 'The art of screenshake', 2013; M. Jonasson and P. Purho, 'Juice it or lose it', GDC Europe 2012"
SWINK = "S. Swink, Game Feel (2008): a response within about 100 ms reads as instant, past 240 ms as sluggish"


def _span(tl, kind):
    ts = [e["t"] for e in tl.get("events", []) if e.get("kind") == kind]
    return (min(ts), max(ts)) if ts else (None, None)


def _shake_scene(tl):
    return M.shake(tl)[0]


def _kick_fire(tl):
    a, b = _span(tl, "shot")
    return M.kick(tl, a, b, reach=0.25)[0] if a is not None else None


def _kick_back(tl):
    a, b = _span(tl, "shot")
    return M.kick(tl, a, b, reach=0.25)[1] if a is not None else None


def _shake_fire(tl):
    a, b = _span(tl, "shot")
    return M.shake(tl, a, b + 0.2)[0] if a is not None else None


def _flinch(tl):
    a, b = _span(tl, "damage_taken")
    return M.kick(tl, a, b + 0.3)[0] if a is not None else None


# name: (scene or scenes, function of the timeline (or of {scene: timeline}), unit, better, rule, source, estimate)
METRICS = {
    "feel.input_shot_ms": ("fire_wall", lambda tl: M.latency(tl, "input", "fire", "shot", None), "ms", "lower",
                           ("<=", 33.4), FRAME + "; two frames allowed for a gun's first round", True),
    "feel.shot_flash_ms": ("fire_wall", lambda tl: M.latency(tl, "shot", None, "fx", "muzzle"), "ms", "lower", ("<=", 16.7), FRAME, False),
    "feel.shot_sound_ms": ("fire_wall", lambda tl: M.latency(tl, "shot", None, "sound", "shot"), "ms", "lower", ("<=", 16.7), FRAME, False),
    "feel.av_sync_ms": ("fire_wall", M.av_sync, "ms", "lower", ("<=", 45.0), ITU, False),
    "feel.kick_deg": ("fire_wall", _kick_fire, "deg", "none", (">=", 0.3), "a rifle's recoil turns the view; under 0.3 degrees the player does not see it (estimate)", True),
    "feel.kick_recover_s": ("fire_wall", _kick_back, "s", "lower", ("<=", 0.6), "the view settles within about a cycle of a rifle's rhythm of fire (estimate)", True),
    "feel.shot_shake_deg": ("fire_wall", _shake_fire, "deg", "none", (">=", 0.02), SHAKE + "; any shake at all on a shot (estimate of what is seen)", True),
    "feel.shell_share": ("fire_wall", lambda tl: M.per_cause(tl, "shot", None, "fx", "shell", window_s=1.0, once=True), "share", "higher", ("==", 1.0), "every round fired ejects a case (by hand on a pump or bolt gun: within a second)", False),
    "feel.impact_fx_share": ("fire_wall", lambda tl: M.per_cause(tl, "impact", None, "fx", "impact"), "share", "higher", ("==", 1.0), "a round striking a wall throws dust, chips or sparks", False),
    "feel.impact_sound_share": ("fire_wall", lambda tl: M.per_cause(tl, "impact", None, "sound", "impact"), "share", "higher", ("==", 1.0), "a round striking a wall is heard", False),
    "feel.decal_share": ("fire_wall", lambda tl: M.per_cause(tl, "impact", None, "decal", None), "share", "higher", ("==", 1.0), "a round leaves a hole or a mark", False),
    "feel.debug_draws": (("fire_wall", "fire_zombie"), lambda tls: sum(M.count(t, "debug") for t in tls.values()), "count", "lower", ("==", 0), "developer drawing is not feedback", False),
    "feel.marker_ms": ("fire_zombie", lambda tl: M.latency(tl, "damage_dealt", None, "marker", None), "ms", "lower", ("<=", 50.0), SWINK + "; a marker within a few frames of the hit", True),
    "feel.kill_marker": ("fire_zombie", lambda tl: M.count(tl, "marker", "kill"), "count", "higher", (">=", 1), "a kill is confirmed apart from a hit", True),
    "feel.blood_share": ("fire_zombie", lambda tl: M.per_cause(tl, "impact", "flesh", "fx", "blood"), "share", "higher", ("==", 1.0), "a round striking flesh is seen", False),
    "feel.flinch_deg": ("hurt_front", _flinch, "deg", "none", (">=", 0.5), "a blow moves the head (estimate of a visible jerk)", True),
    "feel.hurt_indicator": (("hurt_front", "hurt_left", "hurt_back"), lambda tls: min(M.count(t, "ui", None) for t in tls.values()), "count", "higher", (">=", 1),
                            "the player sees where a hit came from", True),
    "feel.hurt_sound": ("hurt_front", lambda tl: M.count(tl, "sound", "hurt"), "count", "higher", (">=", 1), "a hit taken is heard", True),
    "feel.blast_shake_5_deg": ("blast_5", _shake_scene, "deg", "none", (">=", 0.05), SHAKE + "; a blast 5 m away shakes the view: at least 0.05 degrees of frame to frame zig-zag (estimate)", True),
    "feel.blast_falloff": (("blast_5", "blast_50"), lambda tls: (round((_shake_scene(tls["blast_5"]) or 0) / max(_shake_scene(tls["blast_50"]) or 0, 1e-3), 2)),
                           "ratio", "higher", (">=", 3.0), "a blast's shove falls with distance: one 10 times farther shakes far less (estimate of a 3x floor)", True),
    "feel.footstep_rate": ("walk", lambda tl: M.rate(tl, "sound", "footstep"), "per s", "higher", (">=", 1.2), CADENCE + "; at least most steps heard", False),
    "feel.headbob_cm": ("walk", M.bob, "cm", "none", (">=", 0.5), GAIT_Z + " (estimate: at least a little of it)", True),
    "feel.dry_click": ("dry_fire", lambda tl: M.count(tl, "sound", "dry"), "count", "higher", (">=", 1), "an empty chamber clicks", False),
    "feel.reload_sounds": ("reload", lambda tl: M.count(tl, "sound", "reload"), "count", "higher", (">=", 2), "a magazine change is heard: out and in", False),
    "feel.hitch_fire": ("fire_wall", lambda tl: M.hitch(tl, "shot"), "x median", "lower", ("<=", 2.0), "a frame twice the usual length is a visible stutter (estimate)", True),
    "feel.hitch_blast": ("blast_5", lambda tl: M.hitch(tl, "fx"), "x median", "lower", ("<=", 2.0), "a frame twice the usual length is a visible stutter (estimate)", True),
}


def scenes_of(name):
    s = METRICS[name][0]
    return s if isinstance(s, tuple) else (s,)


def value(name, timelines):
    """A metric from the scenes' timelines ({scene: timeline}); None when a scene it needs is missing."""
    scene, fn = METRICS[name][0], METRICS[name][1]
    if isinstance(scene, tuple):
        if not all(s in timelines for s in scene):
            return None
        return fn({s: timelines[s] for s in scene})
    if scene not in timelines:
        return None
    return fn(timelines[scene])


def holds(name, v):
    op, ref = METRICS[name][4]
    if v is None:
        return None
    return {"<=": v <= ref, ">=": v >= ref, "==": v == ref, "<": v < ref, ">": v > ref}[op]
