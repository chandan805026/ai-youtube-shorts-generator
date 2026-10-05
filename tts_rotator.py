import os
import json
import asyncio
import urllib.request
import urllib.error
import edge_tts

SCRATCH_DIR = r"C:\Users\ladu\.gemini\antigravity\scratch"
LOCAL_VAULT_PATH = os.path.join(SCRATCH_DIR, "eleven_keys_vault.json")
ELEVEN_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - The #1 Viral YouTuber / TikTok Meme Voice
EDGE_FALLBACK_VOICE = "en-US-ChristopherNeural"   # Expressive American Male Fallback


def load_vault():
    # 1. Check environment variable (for GitHub Actions)
    pool_env = os.environ.get("ELEVENLABS_KEYS_POOL")
    if pool_env:
        try:
            return json.loads(pool_env)
        except Exception:
            pass

    # 2. Check local vault file
    if os.path.exists(LOCAL_VAULT_PATH):
        with open(LOCAL_VAULT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # 3. Fallback to single ELEVENLABS_API_KEY
    single_key = os.environ.get("ELEVENLABS_API_KEY")
    if single_key:
        return {
            "keys": [
                {"id": 1, "key": single_key, "status": "active", "limit": 10000, "remaining": 10000}
            ]
        }

    return {"keys": []}


def save_vault(vault_data):
    if os.path.exists(LOCAL_VAULT_PATH):
        try:
            with open(LOCAL_VAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(vault_data, f, indent=2)
        except Exception as e:
            print(f"[Vault] Warning: Could not save local vault: {e}")


def generate_with_elevenlabs(text: str, api_key: str, out_path: str, voice_id: str = ELEVEN_VOICE_ID) -> bool:
    """Generate speech using ElevenLabs REST API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.38,
            "similarity_boost": 0.82,
            "style": 0.55,
            "use_speaker_boost": True
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                with open(out_path, "wb") as f:
                    f.write(resp.read())
                return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"[ElevenLabs API Error {e.code}]: {body[:200]}")
        return False
    except Exception as e:
        print(f"[ElevenLabs Network Error]: {e}")
        return False


async def generate_with_edge_tts(text: str, out_path: str, voice: str = EDGE_FALLBACK_VOICE):
    """Fallback generator using edge-tts."""
    comm = edge_tts.Communicate(text, voice, rate="+14%")
    await comm.save(out_path)
    print(f"[Edge-TTS] Generated fallback speech: {out_path}")


def synthesize_speech(text: str, out_path: str) -> str:
    """
    Main TTS entry point:
    1. Iterates through the 10-key ElevenLabs pool.
    2. Switches to next key if quota exhausted or rate limit hit.
    3. Falls back to edge-tts if all keys exhausted.
    """
    vault = load_vault()
    keys = vault.get("keys", [])
    
    char_len = len(text)
    used_engine = None

    for k in keys:
        if k.get("status") == "active" and k.get("remaining", 0) >= char_len:
            print(f"[TTS Rotator] Attempting Key {k['id']} (Remaining: {k['remaining']} chars)...")
            success = generate_with_elevenlabs(text, k["key"], out_path)
            if success:
                k["remaining"] = max(0, k["remaining"] - char_len)
                save_vault(vault)
                used_engine = f"ElevenLabs (Key {k['id']})"
                print(f"[TTS Rotator] Success with Key {k['id']}! Deducted {char_len} chars. Remaining: {k['remaining']}")
                break
            else:
                print(f"[TTS Rotator] Key {k['id']} failed or quota exceeded. Marking inactive for current session.")
                k["status"] = "exhausted"

    if not used_engine or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        print("[TTS Rotator] All ElevenLabs keys exhausted or failed. Falling back to Edge-TTS...")
        asyncio.run(generate_with_edge_tts(text, out_path))
        used_engine = f"Edge-TTS ({EDGE_FALLBACK_VOICE})"

    return used_engine


if __name__ == "__main__":
    test_out = os.path.join(SCRATCH_DIR, "test_rotator_voice.mp3")
    engine = synthesize_speech("Bro really thought he was going to sneak out unnoticed! Massive L!", test_out)
    print(f"Test completed using: {engine}, file size: {os.path.getsize(test_out)} bytes")
