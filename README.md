# AI Skills

A collection of skills (instruction packs) for Claude and ChatGPT.
مجموعة مهارات جاهزة للاستخدام مع Claude وChatGPT.

| Skill | What it does | Language |
|---|---|---|
| [arabic-language](skills/arabic-language/SKILL.md) | Arabic proofreading, Arabicization of terms (based on Arabic language academies), writing correct Fusha, and إعراب — التدقيق اللغوي والتعريب والإعراب | Arabic |
| [cartoon-video](skills/cartoon-video/SKILL.md) | Renders cartoon videos (MP4) from a story file: animated characters, Arabic voice-over, lip-sync, subtitles, music — إنتاج فيديو كرتوني بالأصوات | English (instructions) |
| [matlab-numerics](skills/matlab-numerics/SKILL.md) | MATLAB numerical modeling: ODEs, numerical methods, PDEs, model fitting, with verification and convergence studies | English |
| [academic-research-writing](skills/academic-research-writing/SKILL.md) | Academic writing with research ethics, quoting/paraphrasing, and APA 7, IEEE, MLA, Chicago, Harvard, Vancouver citation | English |

## Structure

```
skills/                    full skills (folder per skill, SKILL.md + supporting files)
chatgpt/matlab-numerics/   single-file version of matlab-numerics (all references inlined)
```

## Use with Claude

Zip a skill folder (e.g. `skills/matlab-numerics/`) and upload it in the Skills section of Claude's settings,
or place the folder in `~/.claude/skills/` for Claude Code.

## Use with ChatGPT

Upload the skill's `SKILL.md` (or the zipped skill folder) where ChatGPT accepts skills, or to a
Custom GPT as a knowledge file with the instruction: *"Follow the instructions in SKILL.md."*
For `matlab-numerics` use the single-file version in `chatgpt/`.

## Notes

- **cartoon-video** needs Python 3, ffmpeg, Playwright + Chromium and (for voices) internet access
  with `edge-tts` or an ElevenLabs/OpenAI API key. It runs where code can execute (Claude with a
  code environment, or your own computer), not inside ChatGPT.
- **matlab-numerics** writes MATLAB code; run it in MATLAB (or GNU Octave for most base functions).
  The helper `.m` files have not yet been run in MATLAB; test them before relying on them.
- **academic-research-writing** never invents references or data; always check citations against
  your institution's or journal's style guide.
