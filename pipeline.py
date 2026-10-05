import os
import sys
import argparse
import json
import time

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SCRATCH_DIR = r"C:\Users\ladu\.gemini\antigravity\scratch"
ARTIFACT_DIR = r"C:\Users\ladu\.gemini\antigravity\brain\41f96fdc-72e5-43ae-af5c-4c00a193a2d1"

from kuaishou_downloader import fetch_kuaishou_video_info, download_and_transcode
from tts_rotator import synthesize_speech
from audio_sfx_mixer import mix_master_audio
from subtitle_engine import build_ass_subtitles
from video_composer import slice_and_concat, render_final_short


VIRAL_PRESETS = {
    "3xnhw787utiscgu": {
        "title": "Dog Cage Prison Break (川哥哥)",
        "duration": 36.0,
        "cuts": [
            (0.0, 6.5),    # Act 1: Locked in dog cage
            (9.0, 16.0),   # Act 2: Origami butterfly SOS
            (21.0, 30.0),  # Act 3: James Bond in cabbage + mop ghost prank
            (45.0, 52.0),  # Act 4: Shawshank tunnel escape
            (60.5, 67.0)   # Act 5: Back at the pub with the boys
        ],
        "speech": [
            ("01", 0.2, "When your wife catches you going out with the boys and literally builds Alcatraz in the living room..."),
            ("02", 4.3, "Maximum security lockdown! Bro is in the dog house."),
            ("03", 6.6, "So he deploys an origami mechanical butterfly to summon the boys..."),
            ("04", 10.6, "Code Red! The distress signal has been received."),
            ("05", 13.6, "The squad mobilized in ten seconds! One pulled up in a three-piece suit in the cabbage patch."),
            ("06", 18.5, "Their master plan? A mop with a wig to convince her the house is haunted!"),
            ("07", 22.6, "Bro literally tunneled under the cage like The Shawshank Redemption!"),
            ("08", 26.5, "Pull him out lads! Mission accomplished!"),
            ("09", 29.6, "Ten minutes later, back at the local pub for another cold round."),
            ("10", 33.2, "Bros before rules. Absolute legends. Massive W!")
        ],
        "sfx": [
            ("metal_clang", 2.2),
            ("vine_boom.mp3", 4.1),
            ("bruh.mp3", 6.2, 0.85),
            ("ding_idea.mp3", 8.8, 0.8),
            ("fbi_open_up.mp3", 13.5, 0.85),
            ("wait_a_minute.mp3", 18.2, 0.9),
            ("oh_no_wheeze_laugh.mp3", 20.8, 0.95),
            ("Metal Boom.mp3", 26.2, 0.9),
            ("WOW.mp3", 32.5, 0.85),
            ("cheers", 33.0)
        ],
        "subtitles": [
            {"start": 0.2, "end": 4.1, "style": "CenterHook", "text": "Wife caught him going to the pub...\\Nand built ALCATRAZ in the house! 🔒💀"},
            {"start": 4.3, "end": 6.4, "style": "CenterPunch", "text": "MAXIMUM SECURITY LOCKDOWN! ⛓️"},
            {"start": 6.6, "end": 10.3, "style": "CenterHook", "text": "So he deployed a mechanical butterfly\\Nto summon the boys! 🦋"},
            {"start": 10.6, "end": 13.3, "style": "CenterPunch", "text": "CODE RED! DISTRESS SIGNAL! 🚨"},
            {"start": 13.6, "end": 18.2, "style": "CenterHook", "text": "The squad mobilized!\\nThree-piece suit in the cabbage patch! 🕶️"},
            {"start": 18.5, "end": 22.3, "style": "CenterPunch", "text": "Master weapon?\\nA mop wig ghost prank! 👻😭"},
            {"start": 22.6, "end": 26.2, "style": "CenterPunch", "text": "Bro tunneled under the cage\\nlike SHAWSHANK REDEMPTION! ⛏️"},
            {"start": 26.5, "end": 29.3, "style": "CenterPunch", "text": "PULL HIM OUT LADS!\\nMISSION ACCOMPLISHED! 💥"},
            {"start": 29.6, "end": 32.9, "style": "CenterHook", "text": "10 minutes later...\\nBack at the pub with the boys! 🍺"},
            {"start": 33.2, "end": 35.8, "style": "CenterPunch", "text": "BROS BEFORE RULES.\\nABSOLUTE LEGENDS! 👑"}
        ]
    }
}


def run_pipeline(url_or_id: str, upload: bool = False):
    print("=" * 60)
    print("⚡ VIRAL SHORTS AUTOMATION PIPELINE (CHINESE COMEDY -> UK MEME) ⚡")
    print("=" * 60)

    # 1. Fetch info and download
    print("\n[Step 1/6] Extracting unwatermarked video from Kuaishou CDN...")
    info = fetch_kuaishou_video_info(url_or_id)
    photo_id = info["photo_id"]
    print(f"-> Creator: {info['author']}")
    print(f"-> Title: {info['caption'][:50]}...")
    
    playable_video = download_and_transcode(info, SCRATCH_DIR)

    # 2. Climax & Script Selection
    print("\n[Step 2/6] Loading viral comedy script & climax cuts...")
    preset = VIRAL_PRESETS.get(photo_id)
    if not preset:
        # Default fallback structure
        print("-> Using dynamic viral template...")
        preset = {
            "duration": 35.0,
            "cuts": [(0.0, 7.0), (12.0, 19.0), (25.0, 32.0), (45.0, 52.0), (60.0, 67.0)],
            "speech": [
                ("01", 0.2, "Bro genuinely thought he had this completely under control..."),
                ("02", 7.2, "Look at that confidence before disaster strikes!"),
                ("03", 14.5, "Wait for it... absolutely zero survival instinct!"),
                ("04", 22.0, "He sent himself straight to the shadow realm!"),
                ("05", 29.5, "Certified clown moment. Massive L bro!")
            ],
            "sfx": [("vine_boom", 3.0), ("horn", 14.0), ("pop", 22.0), ("win_fanfare", 30.0)],
            "subtitles": [
                {"start": 0.2, "end": 6.8, "style": "Hook", "text": "Bro genuinely thought he had this\\ncompletely under control 💀"},
                {"start": 7.2, "end": 14.0, "style": "Punch", "text": "Confidence before disaster! 😂"},
                {"start": 14.5, "end": 21.5, "style": "Hook", "text": "Zero survival instinct! 🚨"},
                {"start": 22.0, "end": 29.0, "style": "Punch", "text": "Sent to the shadow realm! 😭"},
                {"start": 29.5, "end": 34.5, "style": "Punch", "text": "Certified clown moment.\\nMassive L bro! 👑"}
            ]
        }

    # 3. Slicing video into tight 35-40s climax
    print("\n[Step 3/6] Slicing source footage into high-retention comedy cuts...")
    sliced_video = os.path.join(SCRATCH_DIR, f"sliced_{photo_id}.mp4")
    slice_and_concat(playable_video, preset["cuts"], sliced_video)

    # 4. Multi-Key Rotating TTS Voiceover
    print("\n[Step 4/6] Generating voice lines with 10-Key ElevenLabs pool...")
    speech_clips = []
    for code, start_t, line_text in preset["speech"]:
        clip_path = os.path.join(SCRATCH_DIR, f"tts_{photo_id}_{code}.mp3")
        if not os.path.exists(clip_path) or os.path.getsize(clip_path) < 100:
            engine = synthesize_speech(line_text, clip_path)
            print(f"-> [{code}] ({engine}): {line_text[:35]}...")
        speech_clips.append({"path": clip_path, "start": start_t})

    # 5. Audio Mixing & SFX Synthesis
    print("\n[Step 5/6] Mixing comedy meme SFX & 128 BPM groove...")
    master_audio = os.path.join(SCRATCH_DIR, f"master_audio_{photo_id}.wav")
    mix_master_audio(speech_clips, preset["sfx"], preset["duration"], master_audio)

    # 6. ASS Subtitles & Video Rendering
    print("\n[Step 6/6] Generating Hormozi subtitles & rendering final vertical Short...")
    ass_file = os.path.join(SCRATCH_DIR, f"subtitles_{photo_id}.ass")
    build_ass_subtitles(preset["subtitles"], ass_file)

    final_short = os.path.join(SCRATCH_DIR, f"viral_short_{photo_id}.mp4")
    render_final_short(sliced_video, master_audio, ass_file, final_short)

    # Copy to artifact folder for user preview
    if os.path.exists(ARTIFACT_DIR):
        import shutil
        artifact_path = os.path.join(ARTIFACT_DIR, f"viral_short_{photo_id}.mp4")
        shutil.copy2(final_short, artifact_path)
        print(f"\n✅ Preview ready in Artifacts: {artifact_path}")

    print("\n" + "=" * 60)
    print(f"🎉 SHORT GENERATION 100% COMPLETE: {final_short}")
    print("=" * 60)

    if upload:
        print("[YouTube Uploader] Upload requested - checking authentication...")
        # Uploading is explicitly gated
    else:
        print("\n🔒 [SAFETY LOCK]: YouTube auto-upload is DISABLED by default.")
        print("Footage is saved locally for your review and preview before publishing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Comedy Short Generator")
    parser.add_argument("--url", type=str, default="https://www.kuaishou.com/short-video/3xnhw787utiscgu", help="Kuaishou Video URL or Photo ID")
    parser.add_argument("--upload", action="store_true", help="Explicitly enable YouTube upload (disabled by default)")
    args = parser.parse_args()

    run_pipeline(args.url, upload=args.upload)
