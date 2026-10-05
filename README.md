# 🎬 AI Autonomous Viral Shorts Generator (Chinese Comedy -> UK Meme Edition)

An autonomous content engineering pipeline that takes viral Chinese comedy skits/gadget videos (e.g. from creators like `川哥哥` / `cczz666888`), automatically extracts the comedic climax, generates an ultra-viral UK/Western sarcastic meme roast commentary, adds punchy meme sound effects, burns Hormozi-style vertical subtitles, and renders ready-to-publish 9:16 Shorts.

---

## 🚀 Key Features

1. **Bypasses Chinese Anti-Crawl Firewalls**:
   - Queries Kuaishou's mobile SSR endpoints (`c.kuaishou.com/fw/photo/<id>`) using mobile emulation headers.
   - Extracts 100% unwatermarked, high-bitrate direct CDN MP4 streams (`v1.kwaicdn.com`) without captchas.

2. **HEVC to H.264 Universal Transcoder**:
   - Automatically converts raw HEVC streams to standard H.264 to eliminate Windows Media Player codec errors and enable precise, frame-accurate cutting.

3. **10-Key Auto-Rotating ElevenLabs Voice Engine**:
   - Built-in multi-key rotating pool supporting 10 active accounts (100,000 free credits/month = ~220 viral Shorts/month).
   - Seamlessly fails over from Key 1 through Key 10 on quota exhaustion.
   - Intelligent fallback to `Edge-TTS` (`en-GB-RyanNeural`) if all keys are exhausted.

4. **Procedural Comedy Meme SFX & BGM**:
   - Procedurally synthesizes high-impact meme sound effects (Vine Boom, Iron Clangs, Horns, Cork Pop, Wheeze Laugh) timed down to the millisecond.
   - Layers an energetic 128 BPM comedy groove ducked under speech dialogue.

5. **Hormozi-Style Vertical Subtitles**:
   - Compiles `.ass` subtitle events with bold fonts, bright yellow/white styling, thick black outlines, drop shadows, and high-engagement emojis.

6. **Safety First**:
   - Automated YouTube uploads are **strictly disabled by default**. All renders are saved locally or as downloadable GitHub Actions artifacts for manual preview.

---

## 🛠️ Architecture & Modules

```
ai-youtube-shorts-generator/
│
├── pipeline.py                 # Master orchestrator
├── kuaishou_downloader.py      # Mobile CDN extractor & H.264 transcoder
├── tts_rotator.py              # 10-key ElevenLabs pool rotator & fallback
├── comedy_engine.py            # AI roast scriptwriter & climax detector
├── audio_sfx_mixer.py          # Meme SFX synthesizer & master audio mixer
├── subtitle_engine.py          # Hormozi-style ASS subtitle generator
├── video_composer.py           # FFmpeg slicer, concatenator & MP4 renderer
│
├── requirements.txt            # Python dependencies
└── .github/
    └── workflows/
        └── generate_shorts.yml # Cloud runner with artifact preview
```

---

## 🔑 Multi-Key ElevenLabs Pool Management

Keys are encrypted and stored in GitHub Secrets under `ELEVENLABS_KEYS_POOL`. The vault structure:

```json
{
  "keys": [
    { "id": 1, "key": "sk_...", "status": "active", "limit": 10000, "remaining": 10000 },
    { "id": 2, "key": "sk_...", "status": "active", "limit": 10000, "remaining": 10000 },
    ...
    { "id": 10, "key": "sk_...", "status": "active", "limit": 10000, "remaining": 10000 }
  ]
}
```

---

## 💻 Local Usage

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run pipeline on any Kuaishou URL or Photo ID
python pipeline.py --url "https://www.kuaishou.com/short-video/3xnhw787utiscgu"
```

Rendered vertical shorts are saved to disk with burned subtitles and studio audio mix.
