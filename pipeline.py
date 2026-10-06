import os
import sys
import argparse
import subprocess
import json

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Determine base directory (works both locally and in GitHub Actions)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = BASE_DIR
VAULT_DIR = os.path.join(BASE_DIR, "meme_sound_vault")

from kuaishou_downloader import fetch_kuaishou_video_info, download_and_transcode
from tts_rotator import synthesize_speech
from audio_sfx_mixer import mix_master_audio
from subtitle_engine import build_ass_subtitles
from video_composer import render_final_short
from ai_script_generator import generate_comedy_script_with_gemini
import build_meme_vault


FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"  # Linux / GitHub Actions runner path


def get_video_duration(video_path: str) -> float:
    """Uses ffprobe / ffmpeg to get video duration in seconds."""
    cmd = [
        FFMPEG_BIN, "-i", video_path
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="ignore")
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, mn, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
        return h * 3600 + mn * 60 + s
    return 40.0


def extract_continuous_segment(src_video: str, start_sec: float, dur_sec: float, out_video: str):
    """
    Cuts ONE clean, continuous segment without choppy stitching.
    Preserves natural flow, comedic timing, and visual continuity.
    """
    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", f"{start_sec:.2f}",
        "-i", src_video,
        "-t", f"{dur_sec:.2f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-r", "60",
        "-an",
        out_video
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[Composer] Extracted continuous {dur_sec:.1f}s scene: {out_video}")


def run_pipeline(url_or_id: str, upload: bool = False):
    print("=" * 60)
    print("⚡ AUTONOMOUS VIRAL SHORTS ENGINE (CLOUD & LOCAL READY) ⚡")
    print("=" * 60)

    # 1. Ensure Meme Sound Vault is ready
    if not os.path.exists(VAULT_DIR) or len(os.listdir(VAULT_DIR)) < 10:
        print("[Meme Vault] Initializing iconic meme sound library...")
        build_meme_vault.download_all()

    # 2. Extract unwatermarked video
    print("\n[Step 1/5] Extracting video from Kuaishou CDN...")
    info = fetch_kuaishou_video_info(url_or_id)
    photo_id = info["photo_id"]
    print(f"-> Creator: {info['author']}")
    print(f"-> Caption: {info['caption'][:60]}...")

    playable_video = download_and_transcode(info, BASE_DIR)
    total_duration = get_video_duration(playable_video)
    print(f"-> Source Video Duration: {total_duration:.1f} seconds")

    # 3. AI Scene Selection & Scriptwriting
    print("\n[Step 2/5] AI analyzing scenes & generating viral comedy script...")
    if total_duration > 90:
        print(f"⚠️ Long-form compilation detected ({total_duration:.1f}s). AI selecting the single funniest story...")

    script = generate_comedy_script_with_gemini(info["caption"], info["author"], total_duration)

    cut_st = script.get("cut_start", 0.0)
    cut_dur = script.get("duration", 38.0)
    
    # 4. Extract continuous clean scene (No choppy cuts!)
    print("\n[Step 3/5] Extracting continuous high-retention scene...")
    sliced_video = os.path.join(BASE_DIR, f"clean_scene_{photo_id}.mp4")
    extract_continuous_segment(playable_video, cut_st, cut_dur, sliced_video)

    # 5. Multi-Key Voice Generation (Adam - ElevenLabs)
    print("\n[Step 4/5] Synthesizing voiceover with ElevenLabs Adam...")
    speech_clips = []
    for code, start_t, line_text in script.get("speech", []):
        clip_path = os.path.join(BASE_DIR, f"tts_{photo_id}_{code}.mp3")
        if not os.path.exists(clip_path) or os.path.getsize(clip_path) < 100:
            engine = synthesize_speech(line_text, clip_path)
            print(f"-> [{code}] ({engine}): {line_text[:40]}...")
        # Normalize timestamp to be relative to the cut (0 to cut_dur)
        rel_st = float(start_t)
        if cut_st > 0 and rel_st >= cut_st:
            rel_st = rel_st - cut_st
        rel_st = max(0.0, min(rel_st, max(0.0, cut_dur - 1.5)))
        speech_clips.append({"path": clip_path, "start": rel_st})

    # 6. Audio Mixing (Meme SFX with Silence Pockets)
    print("\n[Step 5/5] Mixing meme SFX & BGM groove (Zero sound clashing)...")
    master_audio = os.path.join(BASE_DIR, f"master_audio_{photo_id}.wav")
    norm_sfx = []
    for sf in script.get("sfx", []):
        if len(sf) >= 2:
            s_name = sf[0]
            s_t = float(sf[1])
            s_gain = float(sf[2]) if len(sf) >= 3 else 1.0
            if cut_st > 0 and s_t >= cut_st:
                s_t = s_t - cut_st
            s_t = max(0.0, min(s_t, cut_dur))
            norm_sfx.append((s_name, s_t, s_gain))
    mix_master_audio(speech_clips, norm_sfx, cut_dur, master_audio)

    # 7. Subtitles & Final Render
    norm_subs = []
    for sub in script.get("subtitles", []):
        st = float(sub.get("start", 0.0))
        et = float(sub.get("end", 0.0))
        if cut_st > 0 and st >= cut_st:
            st = st - cut_st
            et = et - cut_st
        st = max(0.0, min(st, cut_dur))
        et = max(st + 0.5, min(et, cut_dur))
        norm_subs.append({
            "start": st,
            "end": et,
            "style": sub.get("style", "CenterPunch"),
            "text": sub.get("text", "")
        })
    ass_file = os.path.join(BASE_DIR, f"subtitles_{photo_id}.ass")
    build_ass_subtitles(norm_subs, ass_file)

    final_short = os.path.join(BASE_DIR, f"viral_short_{photo_id}.mp4")
    render_final_short(sliced_video, master_audio, ass_file, final_short)

    # Also save a canonical 'viral_short.mp4' for GitHub Actions artifact collection
    canonical_output = os.path.join(BASE_DIR, "viral_short.mp4")
    import shutil
    shutil.copy2(final_short, canonical_output)

    print("\n" + "=" * 60)
    print(f"🎉 SHORT GENERATION 100% COMPLETE: {final_short}")
    print(f"📊 Final File Size: {os.path.getsize(final_short) / (1024*1024):.2f} MB")
    print("=" * 60)

    if upload:
        print("[YouTube Uploader] Upload requested - checking authentication...")
    else:
        print("\n🔒 [SAFETY LOCK]: YouTube auto-upload is DISABLED by default.")
        print("Ready for manual review and download.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Viral Short Generator")
    parser.add_argument("--url", type=str, required=True, help="Kuaishou Video URL or Photo ID")
    parser.add_argument("--upload", action="store_true", help="Explicitly enable YouTube upload")
    args = parser.parse_args()

    run_pipeline(args.url, upload=args.upload)
