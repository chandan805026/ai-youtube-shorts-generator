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
from ai_script_generator import generate_comedy_script_with_gemini
from video_composer import compose_final_short, get_video_duration
import build_meme_vault


def run_pipeline(url_or_id: str, output_path: str = None) -> str:
    print("=" * 70)
    print("  AUTONOMOUS AI SHORTS ENGINE: GEMINI 1:1 STORY + 1.15X LOCKED SYNC")
    print("=" * 70)

    # 0. Ensure Meme Sound Vault is populated
    if hasattr(build_meme_vault, "download_meme_sounds"):
        build_meme_vault.download_meme_sounds()
    elif hasattr(build_meme_vault, "download_all"):
        build_meme_vault.download_all()

    # 1. Download & Transcode Video (Natural 1.0x flow)
    print(f"\n[Step 1/3] Downloading Kuaishou/Douyin raw video: {url_or_id}...")
    info = fetch_kuaishou_video_info(url_or_id)
    raw_video = download_and_transcode(info)
    total_dur = get_video_duration(raw_video)
    print(f"[Step 1/3] Playable video ready: {raw_video} ({total_dur:.1f}s)")

    # 2. Google Gemini watches natural video (compressed 480p low-res copy)
    print(f"\n[Step 2/3] Google Gemini watching natural video ({total_dur:.1f}s) for 100% matched story...")
    script_data = generate_comedy_script_with_gemini(raw_video)
    speech_lines = script_data.get("speech", [])
    print(f"[Step 2/3] Script generated: '{script_data.get('title')}' ({len(speech_lines)} Liam speech lines)")

    # 3. Compose Final Video (1.15x Locked Sync: Liam voice + SFX + Subtitles + Video)
    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"viral_short_{info['photo_id']}.mp4")

    print(f"\n[Step 3/3] Rendering final Short with 1.15x Video & Audio Speed Lock...")
    final_video = compose_final_short(raw_video, script_data, output_path, speed_factor=1.15)
    print(f"\n[Success] Short completely rendered: {final_video}")
    return final_video


def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Pipeline (Gemini 1:1 Story + 1.15x Sync)")
    parser.add_argument("--url", default="https://c.kuaishou.com/fw/photo/3xhpefxgm7t4c7k", help="Kuaishou/Douyin video URL or photo ID")
    parser.add_argument("--output", default=None, help="Output path for the generated Short video")
    args = parser.parse_args()

    out = run_pipeline(args.url, args.output)
    print(f"\nPipeline finished successfully! Final output file: {out}")


if __name__ == "__main__":
    main()
