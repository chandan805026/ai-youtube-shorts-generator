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
from ai_script_generator import condense_video_with_gemini, generate_comedy_script_with_gemini
from video_composer import compose_final_short, get_video_duration
import build_meme_vault


def run_pipeline(url_or_id: str, output_path: str = None, start_sec: float = None, end_sec: float = None) -> str:
    print("=" * 70)
    print("  AUTONOMOUS AI SHORTS ENGINE: 2-PASS GEMINI <60S EDITOR + 1:1 SYNC")
    print("=" * 70)

    if hasattr(build_meme_vault, "download_meme_sounds"):
        build_meme_vault.download_meme_sounds()
    elif hasattr(build_meme_vault, "download_all"):
        build_meme_vault.download_all()

    # Step 1: Download & Transcode Raw Video
    print(f"\n[Step 1/4] Downloading Kuaishou/Douyin raw video: {url_or_id}...")
    info = fetch_kuaishou_video_info(url_or_id)
    raw_video = download_and_transcode(info)
    raw_dur = get_video_duration(raw_video)
    print(f"[Step 1/4] Playable raw video ready: {raw_video} ({raw_dur:.1f}s)")

    # Step 2 (Pass 1): Gemini Master Editor condenses long video to ~60s connected story chapters
    print(f"\n[Step 2/4] Pass 1: Master Editor analyzing {raw_dur:.1f}s video for smooth <60s story cut...")
    edited_video = condense_video_with_gemini(raw_video, start_sec=start_sec, end_sec=end_sec)
    edited_dur = get_video_duration(edited_video)
    print(f"[Step 2/4] Condensed story video ready: {edited_video} ({edited_dur:.1f}s -> ~{edited_dur/1.15:.1f}s at 1.15x)")

    # Step 3 (Pass 2): Gemini watches the condensed video for 100% matched 1:1 story script
    print(f"\n[Step 3/4] Pass 2: Gemini watching condensed video ({edited_dur:.1f}s) for 1:1 matched script...")
    script_data = generate_comedy_script_with_gemini(edited_video)
    speech_lines = script_data.get("speech", [])
    print(f"[Step 3/4] Script generated: '{script_data.get('title')}' ({len(speech_lines)} Liam speech lines)")
    print(f"   [Description] {script_data.get('description', '')}")
    print(f"   [Tags] {script_data.get('tags', [])}")
    for row in speech_lines:
        print(f"   [Script Line] [{row[1]}s] {row[2]}")

    # Step 4: Render Final <60s Short with 1.15x Video & Audio Speed Lock
    if not output_path:
        output_path = os.path.join(SCRATCH_DIR, f"viral_short_{info['photo_id']}.mp4")

    print(f"\n[Step 4/4] Rendering final Short with 1.15x Video & Audio Speed Lock...")
    final_video = compose_final_short(edited_video, script_data, output_path, speed_factor=1.15)
    final_dur = get_video_duration(final_video)
    print(f"\n[Success] Short completely rendered: {final_video} (Final Duration: {final_dur:.1f}s)")
    return final_video


def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Pipeline (2-Pass Gemini <60s Editor + 1:1 Sync)")
    parser.add_argument("--url", default="https://v.kuaishou.com/JnEKe8PN", help="Kuaishou/Douyin video URL or photo ID")
    parser.add_argument("--start", type=float, default=None, help="Optional start timestamp in seconds")
    parser.add_argument("--end", type=float, default=None, help="Optional end timestamp in seconds")
    parser.add_argument("--output", default=None, help="Output path for the generated Short video")
    args = parser.parse_args()

    out = run_pipeline(args.url, output_path=args.output, start_sec=args.start, end_sec=args.end)
    print(f"\nPipeline finished successfully! Final output file: {out}")


if __name__ == "__main__":
    main()
