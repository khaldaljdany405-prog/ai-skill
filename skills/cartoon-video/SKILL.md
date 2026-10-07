---
name: cartoon-video
description: Make finished cartoon videos (MP4) with animated characters, Arabic voice-over, lip-sync, subtitles, music and on-screen text, rendered from code. Use for kids' stories, educational explainers, animated ads and Reels/TikTok/Shorts, whenever someone wants an animated or cartoon video with voices, even if they only say "فيديو كرتوني" or "انيميشن".
---

# Cartoon video maker

You write the story as a JSON file; `scripts/make_video.py` turns it into an MP4 with
vector cartoon characters, Arabic voices, lip-sync, burned-in subtitles, music and an `.srt` file.
Your job is the part that makes it feel professional: a tight script, good staging, natural Arabic
voice lines, and checking the frames before the final render.

## Setup (once per environment)

Needs Python 3, ffmpeg, Playwright with Chromium, numpy:

```bash
pip install playwright numpy edge-tts      # edge-tts = free Arabic neural voices (needs internet)
python -m playwright install chromium      # skip if Chromium is already provided
```

Voices are chosen automatically, best available first: ElevenLabs (`ELEVENLABS_API_KEY` +
voice ids) → OpenAI (`OPENAI_API_KEY`) → edge-tts → gTTS → espeak-ng → **silent**.
If the run prints `provider: silent`, the video has no speech: tell the user plainly, and offer
the fixes (install edge-tts where internet is available, add an API key, or record the lines and
pass them as `"audio"` files). Never present a silent render as finished voiced work.

## Workflow

1. **Brief.** Settle: purpose (story / lesson / ad / social clip), audience age, length, aspect
   (16:9 YouTube, 9:16 Reels/TikTok/Shorts), characters, and any logo, product image, music or
   recordings the user has. If the request already covers this, don't re-ask; fill gaps with
   sensible defaults and say what you assumed.
2. **Script.** Write the scenes and lines in the user's language (default: Modern Standard Arabic).
   Follow the guidance for the video type below. Show the user the script before rendering
   anything longer than ~30 seconds, because changing words after rendering costs a full rerender.
3. **Story JSON.** Read `references/story-format.md` for every field, preset, action and
   background. Save the file next to the user's assets.
4. **Stills first.** `python scripts/make_video.py story.json -o out.mp4 --stills auto`
   writes PNGs (start and a mid-dialogue moment of each scene). Look at every still and fix:
   characters overlapping each other or props, texts colliding with each other or with faces,
   unreadable text over busy backgrounds, a character facing away from the person they talk to,
   empty frames. This is the cheapest place to catch problems.
5. **Preview (optional for long videos).** `--preview` renders half size at 12 fps in seconds.
6. **Final render.** `python scripts/make_video.py story.json -o out.mp4`. Rendering runs at
   roughly 2–4× real time at 1080p; tell the user it is running if it will take more than a minute.
7. **Deliver** the MP4 and the `.srt`, and say which voice engine was used.

Repeated renders are cheap for audio: voice lines are cached by text+voice in `.cartoon_cache/`,
so editing one line only re-synthesizes that line.

## Writing for each type

**Kids' story (3–6 years: 1–3 min; 7–12: 3–6 min).** One clear problem, one lesson, a happy
ending. Short sentences (≤ 12 words), repetition of a key phrase, names said often, expressive
emotions and actions on almost every line. Narrator opens and closes; characters carry the middle.
End with the moral spoken by a character, not lectured by the narrator.

**Educational explainer (1–4 min).** Hook with a question in the first 5 seconds → explain in
small steps (one idea per scene) → concrete example on screen (`classroom` board text, props,
captions) → quick recap → a question for the viewer. A teacher/owl/robot character asks, a child
character answers or gets it wrong first — dialogue teaches better than monologue.

**Ad / product (15–30 s).** Hook (problem or bold promise) in 0–3 s → product as the solution
(`box` or `image` prop with the real logo/photo) → one or two benefits → strong CTA text + spoken
CTA. Use `studio` with brand colors. One message only.

**Social clip (9:16, 15–45 s).** First frame must already be interesting (character mid-action
plus a title text). Large captions, fast scenes (3–6 s each), keep characters and text in the
middle 80% of the frame where app UI won't cover them.

## Making it look professional

- **Staging:** 2–3 characters per scene, `x` between 0.15–0.85, at least 0.2 apart. Speakers face
  each other (default `facing: auto` does this). Use `enter`/`exit` to start and end scenes with
  motion, and `others` to give listeners reactions (nod, surprised, clap) — still listeners look dead.
- **Rhythm:** vary `pause` (0.2 quick banter, 0.8 after a dramatic line). Scenes of 4–12 s.
  Change background or camera between scenes; `camera: auto` already adds a gentle push-in.
- **Text:** at most one title + one caption on screen at a time; place them so they don't cover
  faces (check the stills). Titles in the first scene, CTA in the last.
- **Color:** match character outfits to the palette of the background; keep the main character's
  color unique so kids can track them.
- **Sound:** background music at 0.12–0.2 under speech (ducking is automatic). Short `sfx` on
  key moments (door, pop, applause) add a lot if the user has sound files.

## Arabic voice quality

- Put the full-diacritized version in `say` and the clean one in `text`. TTS engines guess
  vowels badly without tashkeel, especially for names and short words (قِطَّة vs قُطَّة).
- Write numbers, dates and symbols as words in `say` ("ثَلَاثُ دَقَائِقَ" not "٣ دقائق").
- Use punctuation for breathing: commas give short pauses, full stops longer ones.
- Children: female or male voice with raised pitch (the defaults already do this). Old people:
  slower rate, lower pitch. Use different voices for every speaking character.
- If an Arabic proofreading skill is available, run the script through it before rendering.

## Troubleshooting

- `provider: silent` → no TTS reachable; see Setup.
- Arabic text shows as boxes → install an Arabic font (e.g. Noto Naskh Arabic) or set `font_file`.
- Chromium fails to launch → `python -m playwright install chromium` (add `--with-deps` on Linux).
- Render too slow → `fps: 24`, or `--preview` while iterating.
- Want a character style the presets don't cover → restyle with `colors`/properties first; new
  shapes can be added in `assets/stage.html` (functions `human`, `cat`, `owl`, `robot`, `prop`,
  `background`) — everything is plain SVG drawn per frame by `renderAt(frame)`.
