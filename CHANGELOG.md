# Changelog

## 0.1.1

* **Shell ejection** pairs each shot with its own case, within a second. A pump or bolt gun throws its case on the
  hand stroke, after the old 0.3 s window, and one case no longer counts for a whole burst.
* **The reload scene** records until the gun is loaded, a tube gun one round at a time.

## 0.1.0

The first release, built for ToangTown (2026-10-15).

* **The checklist:** 82 interactions of a first-person shooter in ten groups (shooting, hitting, getting hit,
  movement, the world, enemies, explosions, the sound mix, the screen, smoothness), each with what the player should
  get; 23 measured from a timeline, the rest left for a person with what to look for.
* **The timeline contract** (`feellab-timeline/1`, docs/TIMELINE.md): the camera every frame and every event (input,
  shot, sound, effect, decal, impact, marker, damage dealt and taken, camera, screen, debug) with its time.
* **26 metrics** over 11 standard scenes: latency, sound-to-picture sync, kick and its recovery, shake and its fall
  with distance, presence of every answer, footstep cadence, head bob, frame hitches. Each rule names its source or
  is marked an estimate.
* **Verdicts, a report and gate rows** in Weapon Lab's row format.
* **An example:** timelines of two made-up games, one with every answer and one bare prototype.
