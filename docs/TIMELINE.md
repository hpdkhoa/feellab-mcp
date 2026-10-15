# The timeline contract (feellab-timeline/1)

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
Positions in cm, the world's axes; time in seconds from the scene's start.

## Files

One file a scene: `<subject>_<scene>_timeline.json`. `feellab check <file>` checks one. `src/feellab/data/scenes.json` lists the standard scenes and what each asks the probe to do.
