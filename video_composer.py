import os
import sys
import subprocess
import json
import tts_rotator
import audio_sfx_mixer
import subtitle_engine

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"


def get_video_duration(video_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", video_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 95.0


def get_audio_duration(audio_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", audio_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 3.0


def compose_final_short(video_input: str, script_data: dict, out_video: str = None, speed_factor: float = 1.15) -> str:
    """
    Main Assembly Pipeline:
    1. Synthesizes Liam speech lines at natural timeline timestamps.
    2. Mixes master audio (Speech + SFX) across the full natural timeline.
    3. Burns video with locked 1.15x synchronization:
       - Video: setpts = (1/1.15)*PTS (smooth, high-energy pace)
       - Audio: atempo = 1.15 (crisp, natural Liam comedy tempo)
       - Subtitles: timestamps scaled by 1.15
       Ensures 100% millisecond-accurate sync where audio and video finish together!
    """
    total_timeline = get_video_duration(video_input)
    if out_video is None:
        out_video = os.path.join(SCRATCH_DIR, "viral_short_output.mp4")

    # 1. Synthesize Liam speech lines
    speech_lines = script_data.get("speech", [])
    speech_clips = []
    sub_items = []
    sub_cues = script_data.get("subtitles", [])
    next_avail = 0.0

    print(f"[Composer] Synthesizing {len(speech_lines)} Liam speech lines at natural timeline...")
    for idx, item in enumerate(speech_lines):
        line_id = item[0] if len(item) > 2 else f"line_{idx:02d}"
        st = float(item[1]) if len(item) > 2 else 0.5
        text = str(item[2]) if len(item) > 2 else str(item[0])

        # Prevent dialogue collision
        if st < next_avail:
            st = next_avail

        mp3_out = os.path.join(SCRATCH_DIR, f"tts_{line_id}.mp3")
        tts_rotator.synthesize_speech(text, mp3_out)
        clip_dur = get_audio_duration(mp3_out)

        speech_clips.append({"path": mp3_out, "start": st})
        next_avail = st + clip_dur + 0.3

        # Match subtitle display to spoken duration
        sub_text = ""
        if idx < len(sub_cues) and "text" in sub_cues[idx]:
            sub_text = sub_cues[idx]["text"]
        else:
            words = text.split()
            sub_text = " ".join(words[:4]).upper() + " 💥"

        # Scale subtitle timestamps by 1.15x for the final video
        sub_items.append({
            "start": round(st / speed_factor, 2),
            "end": round((st + clip_dur) / speed_factor, 2),
            "text": sub_text,
            "style": "CenterPunch"
        })

    # 2. Mix master audio at natural timeline
    sfx_events = script_data.get("sfx", [])
    master_wav = os.path.join(SCRATCH_DIR, "temp_master_audio.wav")
    print(f"[Composer] Mixing audio track (Speech + {len(sfx_events)} SFX events)...")
    audio_sfx_mixer.mix_master_audio(speech_clips, sfx_events, total_timeline, master_wav)

    # 3. Build Subtitles
    ass_path = os.path.join(SCRATCH_DIR, "temp_subtitles.ass")
    subtitle_engine.build_ass_subtitles(sub_items, ass_path)

    # 4. Final Burn: 1.15x on BOTH Video & Audio together
    try:
        safe_ass = os.path.relpath(ass_path).replace("\\", "/")
    except Exception:
        safe_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    pts_factor = 1.0 / speed_factor
    final_timeline = total_timeline / speed_factor
    print(f"[Composer] Rendering final Short with locked 1.15x sync ({total_timeline:.1f}s -> {final_timeline:.1f}s)...")

    cmd_burn = [
        FFMPEG_BIN, "-y",
        "-i", video_input,
        "-i", master_wav,
        "-filter_complex", f"[0:v]setpts={pts_factor:.4f}*PTS,subtitles='{safe_ass}'[v];[1:a]atempo={speed_factor:.3f}[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-crf", "20",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        out_video
    ]
    subprocess.run(cmd_burn, check=True)
    print(f"[Composer] Final 1.15x Short successfully generated: {out_video} ({final_timeline:.1f}s)")

    # Cleanup temporary wav
    if os.path.exists(master_wav):
        try: os.remove(master_wav)
        except Exception: pass

    return out_video
