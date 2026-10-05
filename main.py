import os
import sys
import json
import time
import asyncio

from source_fetcher import get_next_video
from ai_director import generate_script_and_metadata
from voice_subtitles import generate_voice_and_subtitles
from video_renderer import render_short
from youtube_uploader import upload_short_to_youtube

def update_history(history_file, video_info, youtube_id=None):
    history = {"processed_videos": []}
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

    record = {
        "video_id": video_info.get("video_id"),
        "url": video_info.get("url"),
        "title": video_info.get("title"),
        "youtube_id": youtube_id,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    history["processed_videos"].append(record)

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"History updated with video ID: {record['video_id']}")

def run_pipeline():
    print("=" * 60)
    print("STARTING AUTOMATED CHINA GADGET YOUTUBE SHORTS PIPELINE")
    print("=" * 60)

    video_info = get_next_video()
    if not video_info or not os.path.exists(video_info.get("video_path", "")):
        print("Failed to fetch source video. Exiting.")
        sys.exit(1)

    meta = generate_script_and_metadata(video_info)
    script_text = meta.get("script")
    print(f"Generated Script: {script_text[:100]}...")

    audio_path, ass_path = asyncio.run(generate_voice_and_subtitles(script_text))

    final_video = render_short(video_info["video_path"], audio_path, ass_path, output_path="final_short.mp4")
    if not final_video or not os.path.exists(final_video):
        print("Failed to render final video. Exiting.")
        sys.exit(1)

    youtube_id = upload_short_to_youtube(final_video, meta)
    update_history("history.json", video_info, youtube_id)

    print("=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    if youtube_id:
        print(f"Published Short: https://www.youtube.com/shorts/{youtube_id}")
    else:
        print(f"Short Rendered Successfully: {final_video}")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
