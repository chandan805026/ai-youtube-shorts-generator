# Autonomous AI YouTube Shorts Generator (TwelveLabs + Gemini)

Autonomous AI pipeline that transforms raw comedy skits into high-converting, viral YouTube Shorts tailored for global and Western audiences with British deadpan narration.

---

## 🚀 Architecture Overview

```
[1. Kuaishou/Douyin Raw Video]
              │
              ▼
[2. TwelveLabs AI (The Eye & Director)]
   • Analyzes visual actions, dialogue & on-screen text
   • Extracts complete chronological story facts
   • Recommends dynamic speed ramping for pacing
              │
              ▼
[3. Gemini AI (The Comedy Scriptwriter)]
   • Translates real story into grounded, British deadpan narration (Liam)
   • Calculates exact meme SFX triggers & eye-level safe zone subtitles
              │
              ▼
[4. ElevenLabs + FFmpeg (The Studio)]
   • Records Liam voiceover
   • Synthesizes meme sound effects
   • Renders final polished Short
```

---

## 🛠️ Required GitHub Secrets

| Secret Name | Purpose |
| :--- | :--- |
| `TWELVELABS_API_KEY` | TwelveLabs Video Intelligence API |
| `GEMINI_API_KEY` | Google Gemini 2.5 Flash Scriptwriter |
| `ELEVENLABS_API_KEY` | ElevenLabs Liam Voiceover |
| `ELEVENLABS_KEYS_POOL` | *(Optional)* Multi-key failover pool |

---

## 📦 How to Run

### Via GitHub Actions (1-Click Cloud)
1. Go to **Actions** tab in this repository.
2. Select **Generate Viral Comedy Short**.
3. Enter video link and click **Run workflow**.
4. Download the ready video from the workflow artifacts!

### Locally via Command Line
```bash
pip install -r requirements.txt
python pipeline.py --url "https://c.kuaishou.com/fw/photo/3xhpefxgm7t4c7k"
```
