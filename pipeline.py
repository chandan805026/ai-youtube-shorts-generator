import os
import sys
import argparse
import subprocess
import json

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = BASE_DIR
VAULT_DIR = os.path.join(BASE_DIR, "meme_sound_vault")

from kuaishou_downloader import fetch_kuaishou_video_info, download_and_transcode
from twelvelabs_engine import analyze_video_and_generate_script
from video_composer import compose_final_short
import build_meme_vault


def run_pipeline(url_or_id: str, output_path: str = None) -> str:
    print("=" * 70)
    print("  AUTONOMOUS AI SHORTS ENGINE: TWELVELABS + ELEVENLABS PIPELINE")
    print("=" * 70)

    # 0. Ensure Meme Sound Vault is populated
    if hasattr(build_meme_vault, "download_meme_sounds"):
        build_meme_vault.download_meme_sounds()
    elif hasattr(build_meme_vault, "download_all"):
        build_meme_vault.download_all()

    # 1. Download & Transcode Video
    print(f"\n[Step 1/3] Downloading Kuaishou/Douyin raw video: {url_or_id}...")
    info = fetch_kuaishou_video_info(url_or_id)
    raw_video = download_and_transcode(info)
    print(f"[Step 1/3] Playable video ready: {raw_video}")

    # 2. Analyze & Generate Script directly via TwelveLabs AI
    print(f"\n[Step 2/3] Analyzing video with TwelveLabs AI (Dynamic Speeds + Comedy Script)...")
    twelvelabs_data = analyze_video_and_generate_script(raw_video)
    title = twelvelabs_data.get("title", "Viral Short")
    segments = twelvelabs_data.get("segments", [])
    speech_lines = twelvelabs_data.get("speech", [])
    
    total_timeline = sum((float(s["end"]) - float(s["start"])) / float(s.get("speed", 1.0)) for s in segments)
    print(f"[Step 2/3] Script generated: '{title}' ({len(speech_lines)} Liam speech lines)")
    print(f"[Step 2/3] Computed timeline duration: {total_timeline:.1f}s")
    for idx, sp in enumerate(speech_lines[:3]):
        print(f"  - Line {idx+1}: {sp[2] if len(sp) > 2 else sp}")

    # 3. Compose Final Video (ElevenLabs Liam Voiceover + SFX + Subtitles)
    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"viral_short_{info['photo_id']}.mp4")

    print(f"\n[Step 3/3] Composing speed-ramped video, Liam voice, and subtitles...")
    final_video = compose_final_short(raw_video, twelvelabs_data, twelvelabs_data, output_path)

    print("=" * 70)
    print(f"  SUCCESS! Final Short created: {final_video}")
    print(f"  Duration: ~{total_timeline:.1f}s | Size: {os.path.getsize(final_video) / (1024*1024):.1f} MB")
    print("=" * 70)
    return final_video


def get_first_link_from_queue() -> str:
    queue_file = os.path.join(BASE_DIR, "links.txt")
    if not os.path.exists(queue_file):
        return ""
    with open(queue_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Shorts Production Engine")
    parser.add_argument("--url", type=str, default="", help="Video link")
    parser.add_argument("--out", type=str, default="", help="Output path")
    args = parser.parse_args()

    target_url = args.url
    if not target_url:
        target_url = get_first_link_from_queue()

    if not target_url:
        target_url = "https://c.kuaishou.com/fw/photo/3xhpefxgm7t4c7k"

    run_pipeline(target_url, args.out or None)
