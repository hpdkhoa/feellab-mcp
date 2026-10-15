"""Writes example timelines for two made-up games, to see the format and Feel Lab's verdicts without a game:
"Juicy" gets every answer (a flash and a sound on the shot's frame, kick, shake, cases, impacts with a sound and a
hole, blood, markers, a flinch and an indicator, blasts that shake less with distance, footsteps, head bob); "Bare"
gets what many early prototypes have (a debug dot where a round lands, no shake, no impact, silent steps).

    python -m feellab demo <folder>        (or examples/demo_timelines.py)"""
import json
import math
import sys
from pathlib import Path


def frames(seconds, cam_fn, fps=60):
    out = []
    n = int(seconds * fps)
    for i in range(n + 1):
        t = i / fps
        out.append({"t": round(t, 4), "dt": round(1000.0 / fps, 2), "cam": cam_fn(t)})
    return out


def write(folder, subject, scene, frs, events):
    Path(folder).mkdir(parents=True, exist_ok=True)
    tl = {"contract": "feellab-timeline/1", "scene": scene, "subject": subject, "params": {}, "frames": frs,
          "events": sorted(events, key=lambda e: e["t"])}
    (Path(folder) / ("%s_%s_timeline.json" % (subject, scene))).write_text(json.dumps(tl), encoding="utf-8")


def still(t):
    return [0.0, 0.0, 170.0, 0.0, 0.0, 0.0, 90.0]


def game(folder, subject, juicy):
    shots = [0.1 + i * 0.1 for i in range(10)]

    def fire_cam(t):
        if not juicy:
            return still(t)
        k = sum(1.2 * math.exp(-(t - s) / 0.08) for s in shots if t >= s)          # each shot kicks, then settles
        sh = 0.15 * math.sin(t * 90.0) * sum(math.exp(-(t - s) / 0.05) for s in shots if t >= s)
        return [0.0, 0.0, 170.0, -min(k, 3.0) + sh, sh * 0.5, 0.0, 90.0]
    ev = [{"t": 0.1 - 0.01, "kind": "input", "name": "fire"}]
    for s in shots:
        ev += [{"t": s, "kind": "shot", "value": 1}, {"t": s, "kind": "fx", "name": "FX_MuzzleFlash", "tags": ["muzzle"]},
               {"t": s, "kind": "sound", "name": "sfx_rifle_fire", "tags": ["shot"]}, {"t": s + 0.02, "kind": "impact", "tags": ["concrete"], "at": [500, 0, 150]}]
        if juicy:
            ev += [{"t": s + 0.01, "kind": "fx", "name": "FX_Shell_556", "tags": ["shell"]}, {"t": s + 0.02, "kind": "fx", "name": "FX_Impact_Concrete"},
                   {"t": s + 0.02, "kind": "sound", "name": "sfx_impact_concrete"}, {"t": s + 0.02, "kind": "decal", "name": "D_BulletHole", "tags": ["concrete"]}]
        else:
            ev += [{"t": s + 0.02, "kind": "debug", "name": "impact point"}]
    write(folder, subject, "fire_wall", frames(2.0, fire_cam), ev)
    # a zombie shot until it dies
    ev = []
    for i, s in enumerate([0.1, 0.2, 0.3]):
        ev += [{"t": s, "kind": "shot"}, {"t": s + 0.02, "kind": "impact", "tags": ["flesh"]}, {"t": s + 0.03, "kind": "damage_dealt", "value": 35}]
        if juicy:
            ev += [{"t": s + 0.03, "kind": "fx", "name": "FX_Blood_Spray"}, {"t": s + 0.04, "kind": "marker", "tags": ["kill"] if i == 2 else ["hit"]}]
        else:
            ev += [{"t": s + 0.2, "kind": "marker", "tags": ["hit"]}]
    write(folder, subject, "fire_zombie", frames(1.5, still), ev)
    # hurt
    for scene, yaw in (("hurt_front", 0), ("hurt_left", -90), ("hurt_back", 180)):
        def hurt_cam(t, j=juicy):
            return [0.0, 0.0, 170.0, (-2.0 * math.exp(-(t - 0.2) / 0.1) if (j and t >= 0.2) else 0.0), 0.0, 0.0, 90.0]
        ev = [{"t": 0.2, "kind": "damage_taken", "value": 20, "at": [math.cos(math.radians(yaw)) * 300, math.sin(math.radians(yaw)) * 300, 150]}]
        if juicy:
            ev += [{"t": 0.2, "kind": "ui", "name": "damage_indicator"}, {"t": 0.21, "kind": "sound", "name": "sfx_player_hurt"},
                   {"t": 0.2, "kind": "camera", "name": "flinch", "value": 2.0}]
        else:
            ev += [{"t": 0.2, "kind": "ui", "name": "blood_overlay"}]
        write(folder, subject, scene, frames(1.0, hurt_cam), ev)
    # blasts
    for d in (5, 15, 50):
        amp = (1.5 / (d / 5.0) ** 1.5) if juicy else 0.0

        def blast_cam(t, a=amp):
            e = math.exp(-(t - 0.2) / 0.25) if t >= 0.2 else 0.0
            return [0.0, 0.0, 170.0, a * e * math.sin(t * 70), a * e * math.cos(t * 55), 0.0, 90.0]
        ev = [{"t": 0.2, "kind": "fx", "name": "FX_Grenade_Explosion"}, {"t": 0.2 + d / 343.0, "kind": "sound", "name": "sfx_explosion"}]
        write(folder, subject, "blast_%d" % d, frames(1.2, blast_cam), ev)
    # walking
    def walk_cam(t, j=juicy):
        return [t * 140.0, 0.0, 170.0 + (1.5 * math.sin(t * 2 * math.pi * 1.8) if j else 0.0), 0.0, 0.0, 0.0, 90.0]
    ev = [{"t": round(0.28 * i, 3), "kind": "sound", "name": "sfx_footstep_concrete"} for i in range(1, 11)] if juicy else []
    write(folder, subject, "walk", frames(3.0, walk_cam), ev)
    write(folder, subject, "dry_fire", frames(0.8, still), [{"t": 0.1, "kind": "input", "name": "fire"}] +
          ([{"t": 0.1, "kind": "sound", "name": "sfx_dry_click"}] if juicy else []))
    write(folder, subject, "reload", frames(2.5, still), [{"t": 0.3, "kind": "sound", "name": "sfx_mag_out"}, {"t": 1.4, "kind": "sound", "name": "sfx_mag_in"}]
          if juicy else [{"t": 1.4, "kind": "sound", "name": "sfx_mag_in"}])


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_timelines"
    game(out, "Juicy", True)
    game(out, "Bare", False)
    print("written to", out)
