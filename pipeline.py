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
from twelvelabs_engine import analyze_video_and_get_speeds
from ai_script_generator import generate_comedy_script_with_gemini
from video_composer import build_speed_ramped_base_video, compose_final_short
import build_meme_vault


def run_pipeline(url_or_id: str, output_path: str = None) -> str:
    print("=" * 70)
    print("  AUTONOMOUS AI SHORTS ENGINE: TWELVELABS SPEEDS + GEMINI ACCURACY")
    print("=" * 70)

    # 0. Ensure Meme Sound Vault is populated
    if hasattr(build_meme_vault, "download_meme_sounds"):
        build_meme_vault.download_meme_sounds()
    elif hasattr(build_meme_vault, "download_all"):
        build_meme_vault.download_all()

    # 1. Download & Transcode Video
    print(f"\n[Step 1/4] Downloading Kuaishou/Douyin raw video: {url_or_id}...")
    info = fetch_kuaishou_video_info(url_or_id)
    raw_video = download_and_transcode(info)
    print(f"[Step 1/4] Playable video ready: {raw_video}")

    # 2. TwelveLabs Speed Ramping (Without cutting scenes)
    print(f"\n[Step 2/4] TwelveLabs analyzing video speeds (compressing timeline without cutting)...")
    segments = analyze_video_and_get_speeds(raw_video)
    ramped_base = os.path.join(SCRATCH_DIR, f"ramped_base_{info['photo_id']}.mp4")
    total_timeline = build_speed_ramped_base_video(raw_video, segments, ramped_base)
    print(f"[Step 2/4] Speed-ramped base video ready: {ramped_base} ({total_timeline:.1f}s)")

    # 3. Google Gemini Accurate Story & Comedy Script (Low-Res Upload)
    print(f"\n[Step 3/4] Google Gemini watching low-res speed-ramped video (100% Accurate Story & Sync)...")
    script_data = generate_comedy_script_with_gemini(ramped_base)
    speech_lines = script_data.get("speech", [])
    print(f"[Step 3/4] Script generated: '{script_data.get('title')}' ({len(speech_lines)} Liam speech lines)")

    # 4. Compose Final Video (ElevenLabs Liam + SFX + Subtitles + High-Quality Burn)
    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"viral_short_{info['photo_id']}.mp4")

    print(f"\n[Step 4/4] Composing ElevenLabs Liam voiceover, meme SFX, and safe-zone subtitles...")
    twelvelabs_data = {"segments": segments}
    final_video = compose_final_short(raw_video, twelvelabs_data, script_data, output_path)

    # Cleanup intermediate ramped base
    if os.path.exists(ramped_base):
        try: os.remove(ramped_base)
        except Exception: pass

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
