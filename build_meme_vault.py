import os
import sys
import urllib.request

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "meme_sound_vault")
os.makedirs(VAULT_DIR, exist_ok=True)

SOUNDS = {
    # 1. Iconic Impact & Shock
    "vine_boom.mp3": "https://raw.githubusercontent.com/ThePrimeagen/chussy/master/docs/sounds/vine-boom.mp3",
    "bruh.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/BRUH.mp3",
    "metal_pipe.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/Metal%20Boom.mp3",
    
    # 2. Laughter & Reactions
    "oh_no_wheeze_laugh.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/OH%20NO%20NO%20NO.mp3",
    "wait_a_minute.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/Wait%20a%20minute....mp3",
    "anime_wow.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/WOW.mp3",
    "fbi_open_up.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/FBI%20OPEN%20UP.mp3",
    
    # 3. Disbelief & Fails
    "windows_error.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/WINDOWS-ERROR.mp3",
    "sad_violin.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/Sadness-1.mp3",
    "titanic_bad_recorder.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/Titanic-Paroday.mp3",
    "no_god_please_no.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/NO%20GOD%20PLEASE%20NO.mp3",
    "huh.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/HUH.mp3",
    
    # 4. Action & Comedy Beats
    "ding_idea.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/DING.mp3",
    "yeet.mp3": "https://raw.githubusercontent.com/Lexz-08/YouTube-Memes/main/YEET.mp3"
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_all():
    print(f"Downloading {len(SOUNDS)} iconic foreign meme sound effects into {VAULT_DIR}...")
    success = 0
    for filename, url in SOUNDS.items():
        dest = os.path.join(VAULT_DIR, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f"-> [Cached] {filename} ({os.path.getsize(dest)} bytes)")
            success += 1
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(dest, "wb") as f:
                        f.write(data)
                    print(f"-> [Downloaded] {filename} ({len(data)} bytes)")
                    success += 1
                else:
                    print(f"-> [Invalid size] {filename}: {len(data)} bytes")
                    if os.path.exists(dest):
                        os.remove(dest)
        except Exception as e:
            print(f"-> [Failed] {filename}: {e}")

    print(f"\nDone! Successfully saved {success} / {len(SOUNDS)} meme audios.")


def download_meme_sounds():
    return download_all()


if __name__ == "__main__":
    download_all()

