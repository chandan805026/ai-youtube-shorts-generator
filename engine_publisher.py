import os
import sys
import json
import time
import argparse
import shutil
import subprocess

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(BASE_DIR, "raw_scenes")
VAULT_DIR = os.path.join(BASE_DIR, "meme_sound_vault")

from engine_harvester import harvest_next, load_state, save_state, remove_current_link, get_video_duration
from ai_script_generator import generate_comedy_script_with_gemini
from tts_rotator import synthesize_speech
from audio_sfx_mixer import mix_master_audio
from subtitle_engine import build_ass_subtitles
from video_composer import render_final_short, slice_and_concat, extract_continuous_segment
import build_meme_vault


def publish_one_short(upload: bool = False):
    print("=" * 60)
    print("⏰ ENGINE 2: SCHEDULED VIRAL SHORTS PUBLISHER ⏰")
    print("=" * 60)

    # 1. Ensure Meme Sound Vault is ready
    if not os.path.exists(VAULT_DIR) or len(os.listdir(VAULT_DIR)) < 10:
        print("[Publisher] Initializing meme sound vault...")
        build_meme_vault.download_all()

    # 2. Check if raw_scenes/ has clips; if empty, trigger Harvester to restock!
    existing_clips = sorted([f for f in os.listdir(SCENES_DIR) if f.endswith(".mp4")])
    if not existing_clips:
        print("[Publisher] Shelf is empty! Triggering Engine 1 Harvester to fetch next link...")
        stocked = harvest_next()
        if not stocked:
            print("[Publisher] No links or scenes available. Waiting for new links in links.txt.")
            return False
        existing_clips = sorted([f for f in os.listdir(SCENES_DIR) if f.endswith(".mp4")])

    if not existing_clips:
        print("[Publisher] No clips ready to process.")
        return False

    # 3. Pick the FIRST clip in queue
    target_clip_name = existing_clips[0]
    target_clip_path = os.path.join(SCENES_DIR, target_clip_name)
    clip_dur = get_video_duration(target_clip_path)

    print(f"\n[Step 1/5] Processing scene: {target_clip_name} ({clip_dur:.1f}s)")
    state = load_state()
    current_link = state.get("current_link", "Unknown Link")

    # 4. Gemini Audio-Visual Scriptwriting + Smart 1-Minute Compression
    print("\n[Step 2/5] Gemini analyzing video, cutting dead space to ~1 min, and crafting Liam roast...")
    script = generate_comedy_script_with_gemini(
        video_path=target_clip_path,
        caption="Slapstick Comedy Skit",
        author="Kuaishou Creator",
        total_duration=clip_dur
    )

    edit_segments = script.get("edit_segments", [(0.0, clip_dur)])
    edited_dur = float(script.get("edited_duration", clip_dur))

    # Smart 1-Minute Sultawo Video Preparation
    prepared_video_path = os.path.join(BASE_DIR, f"prepared_{target_clip_name}")
    is_trimmed = False

    if len(edit_segments) > 1:
        print(f"\n[Step 2.5/5] Multi-segment smart trim: stitching {len(edit_segments)} funny scenes into ~{edited_dur:.1f}s Short...")
        slice_and_concat(target_clip_path, edit_segments, prepared_video_path)
        is_trimmed = True
        active_video_path = prepared_video_path
    elif len(edit_segments) == 1:
        st, et = edit_segments[0]
        if (et - st) < (clip_dur - 2.0):
            print(f"\n[Step 2.5/5] Single-segment smart trim: extracting {st:.1f}s to {et:.1f}s ({et-st:.1f}s)...")
            extract_continuous_segment(target_clip_path, st, et - st, prepared_video_path)
            is_trimmed = True
            active_video_path = prepared_video_path
        else:
            active_video_path = target_clip_path
    else:
        active_video_path = target_clip_path

    active_clip_dur = get_video_duration(active_video_path)
    print(f"-> Active Short Video Duration: {active_clip_dur:.1f}s")

    # 5. ElevenLabs Liam Voiceover Generation
    print("\n[Step 3/5] Synthesizing voiceover with ElevenLabs Liam...")
    speech_clips = []
    speech_raw = script.get("speech", [])
    temp_tts_files = []

    for code, start_t, line_text in speech_raw:
        clip_tts_path = os.path.join(BASE_DIR, f"tts_{target_clip_name}_{code}.mp3")
        temp_tts_files.append(clip_tts_path)
        if not os.path.exists(clip_tts_path) or os.path.getsize(clip_tts_path) < 100:
            engine = synthesize_speech(line_text, clip_tts_path)
            print(f"-> [{code}] ({engine}): {line_text[:45]}...")

        rel_st = max(0.0, min(float(start_t), max(0.0, active_clip_dur - 1.5)))
        speech_clips.append({"path": clip_tts_path, "start": rel_st})

    # 6. Audio Mixing (Meme SFX with Silence Pockets)
    print("\n[Step 4/5] Mixing meme SFX & groove audio...")
    master_audio = os.path.join(BASE_DIR, f"master_audio_{target_clip_name}.wav")
    norm_sfx = []
    for sf in script.get("sfx", []):
        if len(sf) >= 2:
            s_name = sf[0]
            s_t = max(0.0, min(float(sf[1]), max(0.0, active_clip_dur - 0.5)))
            s_gain = float(sf[2]) if len(sf) >= 3 else 1.0
            norm_sfx.append((s_name, s_t, s_gain))
    mix_master_audio(speech_clips, norm_sfx, active_clip_dur, master_audio)

    # 7. Subtitles & Final Render
    norm_subs = []
    for sub in script.get("subtitles", []):
        st = max(0.0, min(float(sub.get("start", 0.0)), active_clip_dur))
        et = max(st + 0.5, min(float(sub.get("end", st + 2.0)), active_clip_dur))
        norm_subs.append({
            "start": st,
            "end": et,
            "style": sub.get("style", "CenterPunch"),
            "text": sub.get("text", "")
        })
    ass_file = os.path.join(BASE_DIR, f"subtitles_{target_clip_name}.ass")
    build_ass_subtitles(norm_subs, ass_file)

    final_short = os.path.join(BASE_DIR, "viral_short.mp4")
    render_final_short(active_video_path, master_audio, ass_file, final_short)

    print("\n" + "=" * 60)
    print(f"🎉 SHORT RENDER 100% COMPLETE: {final_short}")
    print(f"📊 Final Size: {os.path.getsize(final_short) / (1024*1024):.2f} MB")
    print("=" * 60)

    # 8. POST-UPLOAD AUTO-CLEANUP (The User's Core Plan!)
    print("\n[Step 5/5] Performing post-production cleanup...")
    # Delete processed scene clip from raw_scenes/
    if os.path.exists(target_clip_path):
        os.remove(target_clip_path)
        print(f"🗑️ Deleted processed scene from queue: {target_clip_name}")

    # Delete temporary prepared video if created
    if is_trimmed and os.path.exists(prepared_video_path):
        try:
            os.remove(prepared_video_path)
            print(f"🗑️ Cleaned up temporary trimmed video.")
        except Exception:
            pass

    for tf in temp_tts_files + [master_audio, ass_file]:
        if os.path.exists(tf):
            try:
                os.remove(tf)
            except Exception:
                pass

    # Check remaining scenes in raw_scenes/
    remaining_clips = [f for f in os.listdir(SCENES_DIR) if f.endswith(".mp4")]
    if remaining_clips:
        print(f"📦 {len(remaining_clips)} scenes still remaining in queue for current link: {remaining_clips}")
    else:
        # ALL SCENES FOR CURRENT LINK ARE DONE!
        print("\n" + "★" * 60)
        print(f"🎯 ALL SCENES COMPLETE FOR LINK: {current_link}")
        print("🗑️ Removing completed URL from links.txt...")
        remove_current_link(current_link)
        state["completed_links_count"] = state.get("completed_links_count", 0) + 1
        save_state(state)

        # IMMEDIATELY RESTOCK WITH NEXT LINK SO NEXT CRON IS READY!
        print("🔄 Immediately triggering Harvester to stock scenes from NEXT LINK...")
        harvest_next()
        print("★" * 60)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Engine 2: Scheduled Shorts Publisher")
    parser.add_argument("--upload", action="store_true", help="Enable direct YouTube upload")
    args = parser.parse_args()

    publish_one_short(upload=args.upload)
