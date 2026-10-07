#!/usr/bin/env python3
"""Render a cartoon video (MP4 + SRT) from a story JSON file.

  python make_video.py story.json -o out.mp4              # final render
  python make_video.py story.json -o out.mp4 --preview    # fast, small, low fps
  python make_video.py story.json --stills auto           # PNG stills to check the look
  python make_video.py story.json -o out.mp4 --tts edge   # force a voice provider

Pipeline: voices (tts.py) -> timeline -> lip-sync envelopes -> browser renders
every frame from assets/stage.html -> ffmpeg muxes frames, voices, sfx, music.
See references/story-format.md for the JSON format.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, time
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tts  # noqa: E402

SR = 24000
STAGE = os.path.join(HERE, "..", "assets", "stage.html")
TASHKEEL = re.compile(r"[ؗ-ًؚ-ْٰ]")
NAME_COLORS = ["#fde047", "#7dd3fc", "#f9a8d4", "#86efac", "#fdba74", "#c4b5fd"]
PRESET_VOICE = {
    "boy": ("male", "child"), "boy_thobe": ("male", "child"), "girl": ("female", "child"), "girl_hijab": ("female", "child"),
    "man": ("male", "adult"), "man_shemagh": ("male", "adult"), "man_casual": ("male", "adult"), "teacher": ("male", "adult"),
    "woman": ("female", "adult"), "woman_hair": ("female", "adult"), "grandpa": ("male", "old"), "grandma": ("female", "old"),
    "cat": ("female", "child"), "owl": ("male", "old"), "robot": ("male", "adult"),
}


def die(msg):
    print("ERROR:", msg, file=sys.stderr); sys.exit(1)


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def decode(path):
    """Any audio file -> mono float32 at SR."""
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       stdout=subprocess.PIPE, check=True)
    return np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768


def trim_silence(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a
    s, e = max(0, idx[0] - int(0.03 * SR)), min(len(a), idx[-1] + int(0.08 * SR))
    return a[s:e]


def voice_for(story, cid):
    c = story.get("characters", {}).get(cid, {})
    v = dict(c.get("voice", {}))
    g, a = PRESET_VOICE.get(c.get("preset", ""), ("male", "adult"))
    v.setdefault("gender", g); v.setdefault("age", a)
    if cid == "narrator" and not c.get("voice"):
        v.setdefault("rate", "-4%")
    return v


def resolve(base, p):
    if not p or re.match(r"^(https?|data|file):", p): return p
    q = p if os.path.isabs(p) else os.path.join(base, p)
    return os.path.abspath(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--preview", action="store_true", help="half size, 12 fps")
    ap.add_argument("--stills", default=None, help="'auto' or comma-separated seconds; writes PNGs and exits")
    ap.add_argument("--tts", default=None, help="auto|elevenlabs|openai|edge|gtts|espeak|silent")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool): die(f"{tool} is not installed")
    story_path = os.path.abspath(args.story)
    base = os.path.dirname(story_path)
    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)
    work = args.workdir or os.path.join(base, ".cartoon_cache")
    os.makedirs(work, exist_ok=True)
    out = os.path.abspath(args.out or os.path.splitext(story_path)[0] + ".mp4")

    # ---------- format ----------
    aspect = story.get("aspect", "16:9")
    W, H = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}.get(aspect, (1920, 1080))
    fps = int(story.get("fps", 30))
    if args.preview: W, H, fps = W // 2, H // 2, 12
    portrait = H > W
    char_scale = story.get("char_scale", 3.0 if portrait else (2.6 if W == H else 2.4))
    ground = story.get("ground", 0.72 if portrait else (0.8 if W == H else 0.82))

    # ---------- voices ----------
    scenes = story.get("scenes") or die("story has no scenes")
    spoken = [(si, li, l) for si, s in enumerate(scenes) for li, l in enumerate(s.get("lines", [])) if (l.get("say") or l.get("text")) and not l.get("audio")]
    provider = "silent"
    if spoken:
        si, li, l0 = spoken[0]
        provider, errs = tts.pick_provider(args.tts or story.get("tts", "auto"), l0.get("say") or l0["text"], voice_for(story, l0.get("speaker", "narrator")), work)
        print(f"[tts] provider: {provider}" + (f"  (skipped: {errs})" if errs else ""))
        if provider == "silent":
            print("[tts] WARNING: no voice engine worked -> video will have no speech. "
                  "Install edge-tts (pip install edge-tts) or set ELEVENLABS_API_KEY / OPENAI_API_KEY.")

    # ---------- timeline ----------
    chars = story.get("characters", {})
    for i, (cid, c) in enumerate(chars.items()):
        c.setdefault("color", NAME_COLORS[i % len(NAME_COLORS)])
    strip = story.get("subtitle_tashkeel", True) is False
    clips, plan_scenes, t, text_of = [], [], 0.0, {}
    for si, s in enumerate(scenes):
        sc = {k: v for k, v in s.items() if k not in ("lines", "texts", "sfx")}
        sc["start"] = t
        cast = s.get("cast", [])
        enters = any(c.get("enter") in ("left", "right") for c in cast)
        cur = t + (1.0 if enters else 0.6 if s.get("transition", "fade") == "fade" else 0.3)
        cur += s.get("lead", 0)
        lines = []
        for li, l in enumerate(s.get("lines", [])):
            cur += l.get("delay", 0)
            spk = l.get("speaker", "narrator")
            audio, dur = None, l.get("duration")
            text = l.get("text", "")
            if l.get("audio"):
                audio = trim_silence(decode(resolve(base, l["audio"])))
            elif (l.get("say") or text) and provider != "silent":
                try:
                    wav = tts.synth(provider, l.get("say") or text, voice_for(story, spk), work)
                    audio = trim_silence(read_wav(wav))
                except Exception as e:
                    print(f"[tts] line failed ({e}); using silence", file=sys.stderr)
            if audio is not None:
                dur = max(dur or 0, len(audio) / SR)
            if dur is None:
                n = len(TASHKEEL.sub("", text).split())
                dur = max(1.2, 0.42 * n + 0.5) if text else 1.5
            ln = {k: v for k, v in l.items() if k not in ("audio", "say")}
            ln.update(speaker=spk, start=cur, end=cur + dur)
            if strip and text: ln["sub"] = TASHKEEL.sub("", text)
            lines.append(ln)
            clips.append((cur, audio, spk, cur + dur))
            text_of[(cur, spk)] = bool(text)
            cur += dur + l.get("pause", 0.35)
        end = cur + 0.7 + (0.9 if any(c.get("exit") for c in cast) else 0)
        end = max(end, t + s.get("duration", 0))
        sc["lines"], sc["end"] = lines, end
        texts = []
        for x in s.get("texts", []):
            x = dict(x)
            st = lines[x["line"]]["start"] if "line" in x and x["line"] < len(lines) else t + x.get("at", 0.25)
            x["start"], x["end"] = st, (st + x["dur"]) if "dur" in x else end - 0.05
            texts.append(x)
        sc["texts"] = texts
        for x in s.get("sfx", []):
            clips.append((t + x.get("at", 0), decode(resolve(base, x["file"])) * x.get("volume", 0.8), None, None))
        if sc.get("bg", {}).get("src"): sc["bg"]["src"] = "file://" + resolve(base, sc["bg"]["src"])
        for p in sc.get("props", []):
            if p.get("src"): p["src"] = "file://" + resolve(base, p["src"])
        plan_scenes.append(sc)
        t = end
    total = t
    nframes = int(math.ceil(total * fps))

    # ---------- voice track + lip-sync ----------
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    mouth = {}
    for start, audio, spk, end in clips:
        if spk is not None and spk in chars:
            m = mouth.setdefault(spk, [0.0] * nframes)
            f0, f1 = int(start * fps), min(nframes, int(math.ceil(end * fps)))
            if audio is not None:
                hop = SR / fps
                rms = np.array([np.sqrt(np.mean(audio[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-9) for i in range(f1 - f0)])
                ref = np.percentile(rms, 90) or 1
                vals = np.clip((rms / ref) ** 0.8, 0, 1)
                vals[vals < 0.12] = 0
                for i, v in enumerate(vals):
                    if f0 + i < nframes: m[f0 + i] = round(float(v), 3)
            elif text_of.get((start, spk)):  # simulated syllables (no audio available)
                for f in range(f0, f1):
                    lt = f / fps - start
                    v = max(0.0, math.sin(2 * math.pi * 4.3 * lt)) ** 0.7 * (0.6 + 0.4 * math.sin(lt * 7.1) ** 2)
                    m[f] = round(v if end - f / fps > 0.12 else 0, 3)
        if audio is not None:
            i0 = int(start * SR); i1 = min(len(track), i0 + len(audio))
            track[i0:i1] += audio[: i1 - i0]
    peak = np.max(np.abs(track)) or 1
    if peak > 0.98: track *= 0.98 / peak
    voice_wav = os.path.join(work, "voice_track.wav")
    with wave.open(voice_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((track * 32767).astype(np.int16).tobytes())

    # ---------- subtitles file ----------
    def ts(x):
        h, r = divmod(x, 3600); m_, s_ = divmod(r, 60)
        return f"{int(h):02}:{int(m_):02}:{int(s_):02},{int((s_ % 1) * 1000):03}"
    srt, n = [], 1
    for sc in plan_scenes:
        for l in sc["lines"]:
            if l.get("text"):
                who = chars.get(l["speaker"], {}).get("name")
                srt.append(f"{n}\n{ts(l['start'])} --> {ts(l['end'])}\n{(who + ': ') if who else ''}{l.get('sub', l['text'])}\n"); n += 1

    font_stack = ", ".join(f'"{f}"' for f in [story.get("font", "Cairo"), "Tajawal", "Noto Naskh Arabic", "Noto Sans Arabic",
                                               "Segoe UI", "Tahoma", "Arial", "DejaVu Sans"]) + ", sans-serif"
    plan = dict(width=W, height=H, fps=fps, ground=ground, charScale=char_scale, portrait=portrait,
                characters=chars, scenes=plan_scenes, mouth=mouth, fontStack=font_stack,
                subtitles=story.get("subtitles", True), subtitle_names=story.get("subtitle_names", True),
                subtitle_size=story.get("subtitle_size", 46), accent=story.get("accent", "#ef4444"))
    print(f"[plan] {len(plan_scenes)} scenes, {total:.1f}s, {nframes} frames @ {fps}fps, {W}x{H}")

    # ---------- render ----------
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            exe = next((x for x in ["/opt/pw-browsers/chromium", shutil.which("chromium"), shutil.which("chromium-browser"),
                                    shutil.which("google-chrome")] if x and os.path.exists(x)), None)
            if not exe: raise
            browser = p.chromium.launch(executable_path=exe)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto("file://" + os.path.abspath(STAGE))
        if story.get("font_file"):
            ff = resolve(base, story["font_file"])
            page.add_style_tag(content=f'@font-face{{font-family:"{story.get("font", "Custom")}";src:url("file://{ff}");}}')
        elif story.get("google_font", True):
            try:
                fam = story.get("font", "Cairo").replace(" ", "+")
                page.add_style_tag(url=f"https://fonts.googleapis.com/css2?family={fam}:wght@400;600;800&display=block")
            except Exception:
                print("[font] Google Fonts unreachable; using system Arabic font")
        page.evaluate("plan => init(plan)", plan)
        # make sure the web font is actually loaded before the first frame
        page.evaluate("""async () => { try { await document.fonts.load('800 40px ' + getComputedStyle(document.documentElement).getPropertyValue('--font')); } catch(e){} }""")

        if args.stills:
            outdir = os.path.splitext(out)[0] + "_stills"
            os.makedirs(outdir, exist_ok=True)
            if args.stills == "auto":
                times = []
                for sc in plan_scenes:
                    times.append(sc["start"] + 1.1)
                    if sc["lines"]: times.append((sc["lines"][-1]["start"] + sc["lines"][-1]["end"]) / 2)
            else:
                times = [float(x) for x in args.stills.split(",")]
            for tt in times:
                f = min(nframes - 1, int(tt * fps))
                page.evaluate(f"renderAt({f})")
                pth = os.path.join(outdir, f"still_{tt:06.2f}s.png")
                page.screenshot(path=pth)
                print("[still]", pth)
            browser.close()
            return

        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
               "-i", voice_wav]
        music = story.get("music")
        if music:
            cmd += ["-stream_loop", "-1", "-i", resolve(base, music)]
            mv = story.get("music_volume", 0.18)
            fo = max(0, total - 2)
            fc = (f"[2:a]volume={mv},afade=t=in:d=1.5,afade=t=out:st={fo}:d=2,aformat=channel_layouts=stereo[m];"
                  f"[1:a]aformat=channel_layouts=stereo,asplit=2[v1][v2];"
                  f"[m][v1]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350[md];"
                  f"[v2][md]amix=inputs=2:duration=first:normalize=0[a]")
            cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a"]
        cmd += ["-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium" if not args.preview else "veryfast",
                "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t0, last = time.time(), -1
        for f in range(nframes):
            page.evaluate(f"renderAt({f})")
            ff.stdin.write(page.screenshot(type="jpeg", quality=92))
            pct = int(100 * f / nframes)
            if pct // 10 != last:
                last = pct // 10
                print(f"[render] {pct}%  ({time.time() - t0:.0f}s)", flush=True)
        ff.stdin.close()
        rc = ff.wait()
        browser.close()
        if rc != 0: die("ffmpeg failed")

    with open(os.path.splitext(out)[0] + ".srt", "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    print(f"[done] {out}  ({total:.1f}s, voices: {provider})")


if __name__ == "__main__":
    main()
