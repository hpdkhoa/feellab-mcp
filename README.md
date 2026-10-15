<h1 align="center">Feel Lab</h1>

<!-- mcp-name: io.github.hpdkhoa/feellab-mcp -->

<p align="center"><strong>An FPS feel checklist, measured: every interaction a player has, checked from what the game really did.</strong></p>

<p align="center">
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <a href="pyproject.toml"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white"></a>
  <a href="https://pypi.org/project/feellab-mcp/"><img alt="PyPI: feellab-mcp" src="https://img.shields.io/pypi/v/feellab-mcp?label=PyPI&logo=pypi&logoColor=white&color=3775a9"></a>
  <a href="https://registry.modelcontextprotocol.io/v0/servers?search=feellab-mcp"><img alt="MCP Registry: feellab-mcp" src="https://img.shields.io/badge/MCP%20Registry-feellab--mcp-6f42c1"></a>
  <a href="#the-checklist"><img alt="checklist: 82 interactions" src="https://img.shields.io/badge/checklist-82%20interactions-orange"></a>
  <a href="#tools"><img alt="tools: 6" src="https://img.shields.io/badge/tools-6-orange"></a>
  <a href="docs/TIMELINE.md"><img alt="timeline contract: v1" src="https://img.shields.io/badge/timeline%20contract-v1-orange"></a>
</p>

Game feel is what a player feels between pressing a key and seeing the world answer. A shot should flash, sound and
kick on the same frame; a round striking a wall should throw dust, make a sound and leave a hole; a hit taken should
jerk the view and show where it came from; a blast nearby should shake the screen more than one far away. When one
answer is missing or late, the game feels floaty or cheap, and nobody can say why.

Feel Lab turns that into checks. Your game's probe plays standard scenes and writes a **timeline**: the camera every
frame, and every sound, effect, mark and damage event with its time. Feel Lab measures latency, kick, shake,
presence, match and smoothness from it, and judges each item of an 82-item checklist. It never runs your game: any
engine can write the timeline ([docs/TIMELINE.md](docs/TIMELINE.md)).

## The checklist

| Group | Items | Measured from a timeline |
|---|---|---|
| A. Shooting (your own gun) | 19 | 9 |
| B. Hitting (your bullets land) | 15 | 6 |
| C. Getting hit (damage taken) | 9 | 4 |
| D. Movement and the body | 11 | 2 |
| E. Interacting with the world | 7 | 0 |
| F. Enemies (zombies) | 5 | 0 |
| G. Explosions, fire and the world | 5 | 1 |
| H. Sound mix | 4 | 0 |
| I. Screen and comfort | 4 | 0 |
| J. Smoothness (feel breaks when the frame does) | 3 | 1 |

Items no timeline can show (a colour-blind option, a reload cancel's timing) are left for a person, with what to
look for. `feellab checklist` prints them all.

## What it measures

| Measure | Example |
|---|---|
| Latency | the shot's flash and sound on the shot's frame; the hit marker within 50 ms of the hit |
| Sync | the shot's sound within 45 ms of its flash (ITU-R BT.1359) |
| Kick | the camera turns at least 0.3 degrees on a burst and settles within 0.6 s |
| Shake | a blast 5 m away shakes the view; one 50 m away at least 3 times less |
| Presence | every impact has an effect, a sound and a mark; every round fired ejects a case |
| Rhythm | footsteps at walking cadence (about 100 steps a minute and up); the head bobs |
| Smoothness | no frame twice the median length round a shot or a blast |

Every rule names its source. A range from game practice rather than evidence is marked as an estimate.

## Try it

```bash
pip install feellab-mcp
feellab demo demo
feellab judge demo
```

The demo writes timelines for two made-up games: "Juicy" passes every measured item; "Bare" (a debug dot where a
round lands, no shake, silent steps) fails 17.

## Use it in your game

1. Have your probe play the scenes in `src/feellab/data/scenes.json` and write one timeline each
   ([docs/TIMELINE.md](docs/TIMELINE.md)). Wrap the calls that start sounds and effects so each is recorded with its
   time; note the moments with no sound or effect of their own (a shot, an impact, a hit marker, damage, a flinch).
2. Record a camera frame before the scene's cause (a shot, a hit, a blast): kick and flinch are measured from it.
3. Tag what you can (`"tags": ["muzzle"]`). Where your asset names do not say what a sound or effect is for, put a
   `feel_rules.json` beside the timelines: `{"dry": "slidelock"}` tells Feel Lab that a sound named after a slide lock
   is the click of an empty gun.
4. `feellab judge <folder>`, or `gate_rows` for a gate.

The first game to use it (ToangTown) found 52 failing cases on four guns: a debug dot where a round lands, no shake
anywhere, no blood, no footsteps, a climb that never comes back, a stall on the first shot.

## Tools

| Tool | What it does |
|---|---|
| `list_checklist` | The checklist by group: what the player should get, measured or for a person. |
| `list_scenes` | The standard scenes a probe plays. |
| `list_metrics` | Every metric: scene, unit, rule and source. |
| `check_timeline` | A timeline file against the contract. |
| `judge_folder` | A folder of timelines judged: each item's values and verdict, and a Markdown report. |
| `gate_rows` | The metrics as rows for a gate (Weapon Lab's row format). |

```json
{"mcpServers": {"feellab": {"command": "feellab-mcp"}}}
```

`FEELLAB_OUT` is the only folder Feel Lab writes to (its reports); `~/.feellab` by default.

## Where it came from

Feel Lab was built for ToangTown, an Unreal 5.8 co-op zombie FPS, next to Weapon Lab
([weaponlab-mcp](https://github.com/hpdkhoa/weaponlab-mcp)), whose Gate can judge Feel Lab's rows as cases.

## License

MIT
