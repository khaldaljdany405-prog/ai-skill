# Story JSON format

One file describes the whole video. Paths (audio, images, music, fonts) are relative to the JSON file.

## Contents
1. Top-level fields
2. Characters and voices
3. Scenes
4. Lines (dialogue + acting)
5. On-screen texts
6. Props
7. Backgrounds
8. Full example

## 1. Top-level fields

| field | default | notes |
|---|---|---|
| `aspect` | `"16:9"` | `"16:9"` (YouTube), `"9:16"` (Reels/TikTok/Shorts), `"1:1"`, `"4:5"` |
| `fps` | `30` | 24 is fine for cartoons and renders 20% faster |
| `characters` | — | map of id → character (see §2). Include `"narrator"` if there is narration |
| `scenes` | — | list of scenes, played in order |
| `tts` | `"auto"` | `auto` · `elevenlabs` · `openai` · `edge` · `gtts` · `espeak` · `silent` |
| `music` | none | background music file; looped, faded, auto-ducked under speech |
| `music_volume` | `0.18` | 0–1 |
| `subtitles` | `true` | burned-in subtitles of the current line |
| `subtitle_names` | `true` | show "سامي:" before the line |
| `subtitle_tashkeel` | `true` | `false` removes diacritics from the on-screen subtitle only (voice still uses them) |
| `subtitle_size` | `46` | px at 1080p |
| `font` | `"Cairo"` | font family; loaded from Google Fonts when reachable, otherwise system Arabic font |
| `font_file` | none | local .ttf/.otf to use instead (use with `font` as its family name) |
| `accent` | `"#ef4444"` | default CTA button color |
| `char_scale` / `ground` | auto | character size multiplier / ground line as fraction of height |

## 2. Characters and voices

```json
"characters": {
  "narrator": {"name": "الراوي", "voice": {"gender": "male", "age": "adult", "rate": "-5%"}},
  "sami":  {"preset": "boy", "name": "سامي", "colors": {"shirt": "#ef4444"}},
  "jad":   {"preset": "grandpa", "name": "الجد"},
  "huda":  {"preset": "woman", "name": "هدى", "voice": {"edge": "ar-EG-SalmaNeural"}}
}
```

**Presets** (each can be restyled with `colors`, or have any property overridden):

| preset | look | default voice |
|---|---|---|
| `boy` | child, shirt + trousers, short hair | male child |
| `boy_thobe` | child, white thobe + ghutra | male child |
| `girl` | child, dress, long hair | female child |
| `girl_hijab` | child, dress, hijab | female child |
| `man` | adult, thobe, white ghutra + igal, beard | male adult |
| `man_shemagh` | adult, thobe, red shemagh, beard | male adult |
| `man_casual` | adult, shirt + trousers | male adult |
| `teacher` | adult, shirt, tie, glasses | male adult |
| `woman` | adult, long dress, hijab | female adult |
| `woman_hair` | adult, dress, long hair | female adult |
| `grandpa` | old, thobe, ghutra, white beard, glasses | male old |
| `grandma` | old, dress, grey hijab, glasses | female old |
| `cat`, `owl`, `robot` | animals / robot | child / old / adult |

Human properties you can override: `age` (`child`|`adult`), `outfit` (`shirt`|`thobe`|`dress`), `hair` (`short`|`long`|`curly`|`bun`|`none`), `headwear` (`none`|`ghutra`|`hijab`|`cap`), `beard`, `glasses`, `scale`.
Color keys: `skin hair shirt pants dress thobe ghutra hijab shoes beard tie cap` (cat: `fur belly stripe`; owl: `fur belly beak`; robot: `metal dark glow`).
`color` sets the speaker-name color in subtitles.

**Voice** (`voice` object, all optional): `gender` (`male`|`female`), `age` (`child`|`adult`|`old`), and per-provider fields:
- edge: `edge` (voice name, e.g. `ar-SA-HamedNeural`, `ar-SA-ZariyahNeural`, `ar-EG-SalmaNeural`, `ar-EG-ShakirNeural`, `ar-AE-FatimaNeural`, `ar-AE-HamdanNeural`, `ar-KW-FahedNeural`, `ar-KW-NouraNeural`), `rate` (`"+10%"`), `pitch` (`"+20Hz"`)
- openai: `openai` (voice name), `instructions` (style, e.g. "تحدّث بصوت طفل مرح ومتحمس")
- elevenlabs: `elevenlabs` (voice id), `stability`, `style`

## 3. Scenes

```json
{
  "background": "park",
  "bg": {"trees": false},
  "transition": "fade",
  "camera": "auto",
  "duration": 6,
  "lead": 0,
  "cast": [
    {"id": "sami", "x": 0.3, "enter": "left", "facing": "auto", "emotion": "happy"},
    {"id": "jad",  "x": 0.7, "exit": "right", "scale": 1.1, "z": 1}
  ],
  "props": [{"type": "tree", "x": 0.9}],
  "texts": [{"text": "الفصل الأول", "style": "title"}],
  "sfx": [{"file": "sfx/door.mp3", "at": 1.2, "volume": 0.7}],
  "lines": [ ... ]
}
```

- `cast[].x` — horizontal position 0 (left) → 1 (right). Keep characters between 0.15 and 0.85 and at least 0.2 apart.
- `enter`: `left` | `right` (walks in) | `pop` (bounces in). `exit`: `left` | `right` (walks out at the end).
- `facing`: `auto` (default — looks at whoever is talking), `left`, `right`.
- `emotion` (default for this scene): `happy` `neutral` `sad` `angry` `surprised` `thinking` `excited`.
- `camera`: `auto` (slow push-in that drifts toward the speaker), `static`, or `{"zoom":[1,1.25],"from":[0.5,0.5],"to":[0.3,0.6]}`.
- `transition`: `fade` (default) or `cut`.
- `duration`: minimum scene length (seconds); scenes otherwise last as long as their lines.
- `y` on a cast member lifts it off the ground (fraction of height), e.g. an owl on a branch.

## 4. Lines

```json
{"speaker": "sami", "text": "يا جدّي، انظرْ!", "say": "يا جَدِّي، انْظُرْ!",
 "action": "point", "emotion": "surprised", "look": "jad",
 "others": [{"who": "jad", "action": "nod", "emotion": "happy"}],
 "pause": 0.4, "delay": 0}
```

- `text` — shown in subtitles (and spoken unless `say` exists).
- `say` — what the voice engine reads. Put full tashkeel here and write numbers as words.
- `audio` — use a real recording for this line instead of TTS.
- `action` (speaker) / `others[]` (other characters during this line): `wave` `point` `nod` `shake` `jump` `celebrate` `think` `shrug` `present` `clap` `walk` (needs `"to": 0.6`).
- `emotion` — face for this line.
- `pause` — silence after the line (default 0.35s). `delay` — silence before it.
- `duration` — for a line without text (pure action beat), e.g. `{"speaker":"sami","action":"walk","to":0.8,"duration":1.5}`.
- `nosub: true` hides this line's subtitle.

## 5. On-screen texts

```json
{"text": "حمّل التطبيق الآن", "style": "cta", "pos": "bottom", "line": 1, "dur": 3, "anim": "pop", "color": "#16a34a", "size": 60}
```
- `style`: `title` (big outlined), `caption` (white card), `cta` (colored button), `badge` (small yellow pill).
- `pos`: `top` `upper` `center` `bottom` or a CSS percentage like `"55%"` (distance from top).
- Timing: `at` (seconds from scene start) **or** `line` (appear with that line index); `dur` (default: until scene end).
- `anim`: `pop` `slide` `fade`.

## 6. Props

`{"type": "...", "x": 0.8, "y": 0.2, "scale": 1, "layer": "back"|"front", "float": true}` — without `y` a prop stands on the ground; with `y` it is placed at that height (fraction from the top).

Types: `tree` `palm` `bush` `flower` (`color`) `cloud` (`drift`) `sun` `moon` `star` `house` (`color`,`roof`) `book` `ball` (`bounce`) `balloon` `box` (product box: `color`, `label`) `board` (sign: `label`, `w`, `h`, `size`) `image` (`src`, `w` as fraction of width, `ratio` = h/w) — use `image` for logos and product photos (PNG with transparency looks best).

## 7. Backgrounds

`park` (`bg.trees:false` to remove trees) · `room` (`bg.wall`, `bg.floor`, `bg.rug`) · `classroom` (`bg.board` = text on the chalkboard, `bg.boardSize`) · `night` · `desert` (`bg.palms:false`) · `city` · `sea` · `space` · `studio` (`bg.color1`, `bg.color2` gradient — best for ads and intros/outros) · `image` (`bg.src` = your own picture).

## 8. Full example (kids story, 16:9)

```json
{
  "aspect": "16:9",
  "music": "music/calm.mp3",
  "characters": {
    "narrator": {"name": "الراوي"},
    "sami": {"preset": "boy", "name": "سامي"},
    "mishmish": {"preset": "cat", "name": "مشمش"}
  },
  "scenes": [
    {"background": "park",
     "cast": [{"id": "sami", "x": 0.33, "enter": "left"}, {"id": "mishmish", "x": 0.7, "enter": "pop"}],
     "texts": [{"text": "سامي والقطة", "style": "title", "dur": 3}],
     "lines": [
       {"speaker": "narrator", "text": "في صباحٍ مشمس، خرج سامي إلى الحديقة.", "say": "فِي صَبَاحٍ مُشْمِسٍ، خَرَجَ سَامِي إِلَى الحَدِيقَةِ."},
       {"speaker": "sami", "text": "مرحبًا أيتها القطة!", "say": "مَرْحَبًا أَيَّتُهَا القِطَّةُ!", "action": "wave", "emotion": "excited"},
       {"speaker": "mishmish", "text": "أنا جائعة جدًّا.", "say": "أَنَا جَائِعَةٌ جِدًّا.", "emotion": "sad"}
     ]}
  ]
}
```
