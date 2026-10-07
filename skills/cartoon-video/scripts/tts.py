"""Arabic text-to-speech with several interchangeable providers.

Every provider writes a mono 24 kHz WAV.  `pick_provider` tests the providers in
order and returns the first one that works, so a whole video uses one engine
(mixing engines inside one video sounds uneven).

Providers (best first):
  files       - the line already has "audio": "path/to/recording.mp3"
  elevenlabs  - needs ELEVENLABS_API_KEY (+ voice ids in the story or ELEVENLABS_VOICE_ID)
  openai      - needs OPENAI_API_KEY
  edge        - free Microsoft neural voices, `pip install edge-tts`, needs internet
  gtts        - Google Translate voice, `pip install gTTS`, needs internet (one voice only)
  espeak      - offline, robotic; `espeak-ng` binary
  silent      - no audio; durations estimated from text (lip-sync is simulated)
"""
import asyncio, hashlib, json, os, shutil, subprocess, sys, urllib.request

ORDER = ["elevenlabs", "openai", "edge", "gtts", "espeak", "silent"]

# Default Microsoft (edge-tts) Arabic voices.  Children are made from adult voices
# with a raised pitch, which is the usual trick for cartoon voices.
EDGE_DEFAULTS = {
    ("male", "adult"):   {"voice": "ar-SA-HamedNeural",   "rate": "+0%",  "pitch": "+0Hz"},
    ("female", "adult"): {"voice": "ar-SA-ZariyahNeural", "rate": "+0%",  "pitch": "+0Hz"},
    ("male", "child"):   {"voice": "ar-SA-ZariyahNeural", "rate": "+6%",  "pitch": "+18Hz"},
    ("female", "child"): {"voice": "ar-SA-ZariyahNeural", "rate": "+8%",  "pitch": "+30Hz"},
    ("male", "old"):     {"voice": "ar-SA-HamedNeural",   "rate": "-10%", "pitch": "-8Hz"},
    ("female", "old"):   {"voice": "ar-EG-SalmaNeural",   "rate": "-8%",  "pitch": "-4Hz"},
}
OPENAI_DEFAULTS = {("male", "adult"): "onyx", ("female", "adult"): "nova", ("male", "child"): "fable",
                   ("female", "child"): "shimmer", ("male", "old"): "ash", ("female", "old"): "sage"}


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def to_wav(src, dst):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "24000", dst])


def voice_key(v):
    return (v.get("gender", "male"), v.get("age", "adult"))


def _edge(text, v, out):
    import edge_tts  # noqa
    d = EDGE_DEFAULTS.get(voice_key(v), EDGE_DEFAULTS[("male", "adult")])
    voice, rate, pitch = v.get("edge", d["voice"]), v.get("rate", d["rate"]), v.get("pitch", d["pitch"])
    tmp = out + ".mp3"
    async def go():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(tmp)
    asyncio.run(go())
    to_wav(tmp, out); os.remove(tmp)


def _http(url, headers, body, out):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r, open(out + ".mp3", "wb") as f:
        f.write(r.read())
    to_wav(out + ".mp3", out); os.remove(out + ".mp3")


def _elevenlabs(text, v, out):
    key = os.environ["ELEVENLABS_API_KEY"]
    vid = v.get("elevenlabs") or os.environ.get("ELEVENLABS_VOICE_ID")
    if not vid:
        raise RuntimeError("no ElevenLabs voice id (set voice.elevenlabs or ELEVENLABS_VOICE_ID)")
    _http(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
          {"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
          {"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
           "voice_settings": {"stability": v.get("stability", 0.45), "similarity_boost": 0.8, "style": v.get("style", 0.3)}}, out)


def _openai(text, v, out):
    key = os.environ["OPENAI_API_KEY"]
    body = {"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            "voice": v.get("openai", OPENAI_DEFAULTS.get(voice_key(v), "alloy")), "input": text, "response_format": "mp3"}
    if v.get("instructions"):
        body["instructions"] = v["instructions"]
    _http("https://api.openai.com/v1/audio/speech",
          {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, body, out)


def _gtts(text, v, out):
    from gtts import gTTS
    gTTS(text, lang="ar").save(out + ".mp3")
    to_wav(out + ".mp3", out); os.remove(out + ".mp3")


def _espeak(text, v, out):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("espeak-ng not installed")
    pitch = {"child": "75", "old": "35"}.get(v.get("age"), "50")
    variant = "+f3" if v.get("gender") == "female" else "+m3"
    run([exe, "-v", "ar" + variant, "-p", pitch, "-s", "150", "-w", out + ".tmp.wav", text])
    to_wav(out + ".tmp.wav", out); os.remove(out + ".tmp.wav")


PROVIDERS = {"edge": _edge, "elevenlabs": _elevenlabs, "openai": _openai, "gtts": _gtts, "espeak": _espeak}


def available(name):
    if name == "elevenlabs": return bool(os.environ.get("ELEVENLABS_API_KEY"))
    if name == "openai": return bool(os.environ.get("OPENAI_API_KEY"))
    if name == "edge":
        try: import edge_tts  # noqa
        except ImportError: return False
        return True
    if name == "gtts":
        try: import gtts  # noqa
        except ImportError: return False
        return True
    if name == "espeak": return bool(shutil.which("espeak-ng") or shutil.which("espeak"))
    return name == "silent"


def pick_provider(requested, sample_text, sample_voice, cache_dir):
    """Return the first provider that actually produces audio."""
    order = ORDER if requested in (None, "auto") else [requested]
    errors = {}
    for name in order:
        if name == "silent":
            return "silent", errors
        if not available(name):
            errors[name] = "not installed / no key"; continue
        try:
            out = os.path.join(cache_dir, f"_probe_{name}.wav")
            PROVIDERS[name](sample_text, sample_voice, out)
            if os.path.getsize(out) > 1000:
                return name, errors
        except Exception as e:  # network blocked, bad key, ...
            errors[name] = str(e)[:160]
    if requested not in (None, "auto"):
        print(f"[tts] requested provider '{requested}' failed: {errors}", file=sys.stderr)
    return "silent", errors


def synth(provider, text, voice, cache_dir):
    """Synthesize (with caching) and return the wav path, or None for silent."""
    if provider == "silent":
        return None
    key = hashlib.sha1(json.dumps([provider, text, voice], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    out = os.path.join(cache_dir, f"{key}.wav")
    if not os.path.exists(out):
        PROVIDERS[provider](text, voice, out)
    return out
