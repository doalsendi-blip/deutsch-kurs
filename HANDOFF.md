# Deutsch für den Beruf — project handoff

Live course (claude.ai artifact): https://claude.ai/artifact/SVtM8kpXZmhaBcLbqs1paa
Artifact slug: ce7cef94-2dc5-4f60-98d3-4011a87ff357

## What it is
Professional German course, A1 → A2, built on the Goethe exam framework and taught with the
transfer method (Language Transfer / Madrasa style), gamified (XP, streak, stars, games).
Learner: Zack. Native English plus Hebrew; also learning Arabic via Madrasa. Level: between beginner and A1.

## Files
- `course_data.py` — ALL content. `UNITS` (12 units; 1–4 fully built, 5–12 are outlines), `SOUNDS`,
  `LESEN` (one story per unit, merged into UNITS at the bottom of the file).
- `template.html` — the app (single page). Placeholders: `__CSS__`, `__UNITS__`, `__SOUNDS__`, `__AUD__`.
- `base.css` — base styles injected at `__CSS__`.
- `build.py` — generates backup MP3s and writes `site/index.html` + `site/audio/*.mp3`.
- `site/` — the built output that gets published.

## Unit structure (10 steps, fixed order, each with a pass mark)
Brücke 70 · Wörter 75 · Lesen 80 · Hören 70 · Denken 75 · Grammatik (read, not graded) · Üben 80 ·
Tippen 90 · Schreiben 60 (Claude grades /10) · Sprechen 60 (Claude grades /10).
A unit is passed when all steps pass, and that opens the next unit. Stars: 1 = pass, 2 = 90%, 3 = 100%.

To build a new unit, add to `UNITS` in `course_data.py`: goals, bruecke (cognates, 2–3 sound-shift
rules with examples + guesses, extra), vocab, dialog (speakers W = Herr Weber, M = Herr Miller),
hoeren (voicemail text + 3–4 questions + 4 dictation sentences), denken (8 build-up steps), grammar,
mc, gaps, builder, tippen, write, speak, and a LESEN story (sentences with EN, gloss words, 5 true/false).

## Audio — decisions made
- Primary: the device's own German voice via Web Speech (Edge "Online (Natural)" voices,
  Chrome "Google Deutsch", iPhone enhanced voices). Roles: F narrator, W Weber, M Miller, R second speaker.
- Fallback: pre-generated MP3s (Coqui Thorsten VITS, with respellings in `build.py` RESPELL).
  The learner judged these poor. The old Piper "low" voices were rejected for swallowing schwa endings.
- The Claude desktop app has no German voices, so the learner should use Edge.

## Publishing
`publish_files` takes at most 256 files per call. There are 306 files (index + audio), so publish in
two calls: the first with mode "replace", the second with mode "patch".
The audio hash prefix in build.py (currently "v5|") must change whenever audio is regenerated, to bust caches.

On a machine without Coqui TTS (e.g. the Windows PC), build.py still runs: it keeps the clips listed in the
existing `site/index.html` and skips new texts, which then play through the device voice only. Unit 4's
109 texts have no MP3 yet; regenerate on the TTS machine if a fallback is wanted. Publishing index.html alone
(mode "patch") is enough when no new audio was made.

## Learner preferences
Clear ordered tasks with explicit pass/fail and redo rules. Blunt feedback. No inventories of retired items.

## Next up
1. The learner checks audio in Edge (Info → Audio → Test).
2. Publish the Unit 4 build (index.html only, mode "patch").
3. Build Unit 5 (Zahlen & Finanzen) in the same format.
4. Optional: A2 versions of the stories (level tabs, as on learngermanwithgames.com).
