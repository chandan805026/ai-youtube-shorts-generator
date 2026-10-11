import os
import sys
import argparse

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = BASE_DIR

from kuaishou_downloader import fetch_kuaishou_video_info, download_and_transcode
from twelvelabs_engine import condense_video_with_twelvelabs, get_video_duration


def run_pipeline(url_or_id: str, output_path: str = None) -> str:
    print("=" * 70)
    print("  TWELVELABS MASTER EDITOR + FFMPEG CUT-ONLY TEST (NO GEMINI / NO TTS)")
    print("=" * 70)

    # Step 1: Download & Transcode Raw Video
    print(f"\n[Step 1/2] Downloading Kuaishou/Douyin raw video: {url_or_id}...")
    info = fetch_kuaishou_video_info(url_or_id)
    raw_video = download_and_transcode(info)
    raw_dur = get_video_duration(raw_video)
    print(f"[Step 1/2] Playable raw video ready: {raw_video} ({raw_dur:.1f}s)")

    # Step 2: TwelveLabs Pegasus analyzes video with exact Master Editor prompt & FFmpeg cuts/joins
    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"viral_short_{info['photo_id']}.mp4")

    print(f"\n[Step 2/2] Sending {raw_dur:.1f}s video to TwelveLabs Pegasus + cutting with FFmpeg ONLY...")
    final_video = condense_video_with_twelvelabs(raw_video, output_path=output_path)
    final_dur = get_video_duration(final_video)
    print(f"\n[Success] TwelveLabs + FFmpeg Cut Video Ready: {final_video} (Final Duration: {final_dur:.1f}s)")
    return final_video


def main():
    parser = argparse.ArgumentParser(description="TwelveLabs + FFmpeg Cut-Only Test Pipeline")
    parser.add_argument("--url", default="https://v.kuaishou.com/JnEKe8PN", help="Kuaishou/Douyin video URL or photo ID")
    parser.add_argument("--output", default=None, help="Output path for the cut video")
    args = parser.parse_args()

    out = run_pipeline(args.url, args.output)
    print(f"\nPipeline finished successfully! Final output file: {out}")


if __name__ == "__main__":
    main()
