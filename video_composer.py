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


def build_speed_ramped_base_video(source_video: str, segments: list, out_video: str) -> float:
    """
    Renders the continuous speed-ramped video without cutting any scenes,
    applying speeds recommended by TwelveLabs.
    """
    filter_parts = []
    concat_v = []
    concat_a = []
    total_timeline = 0.0

    for i, seg in enumerate(segments):
        st = float(seg["start"])
        et = float(seg["end"])
        spd = float(seg.get("speed", 1.0))
        dur = max(0.1, et - st)
        timeline_dur = dur / spd
        total_timeline += timeline_dur

        v_tag = f"v{i}"
        a_tag = f"a{i}"
        pts_factor = 1.0 / spd

        filter_parts.append(f"[0:v]trim=start={st}:end={et},setpts=PTS-STARTPTS,setpts={pts_factor}*PTS[{v_tag}]")

        if spd <= 1.05:
            filter_parts.append(f"[0:a]atrim=start={st}:end={et},asetpts=PTS-STARTPTS[{a_tag}]")
        elif spd <= 1.3:
            filter_parts.append(f"[0:a]atrim=start={st}:end={et},asetpts=PTS-STARTPTS,atempo={spd:.3f}[{a_tag}]")
        elif spd <= 2.0:
            filter_parts.append(f"[0:a]atrim=start={st}:end={et},asetpts=PTS-STARTPTS,atempo={spd:.3f}[{a_tag}]")
        elif spd <= 4.0:
            s2 = spd / 2.0
            filter_parts.append(f"[0:a]atrim=start={st}:end={et},asetpts=PTS-STARTPTS,atempo=2.0,atempo={s2:.3f}[{a_tag}]")
        else:
            s_rem = spd / 4.0
            filter_parts.append(f"[0:a]atrim=start={st}:end={et},asetpts=PTS-STARTPTS,atempo=2.0,atempo=2.0,atempo={s_rem:.3f}[{a_tag}]")

        concat_v.append(f"[{v_tag}]")
        concat_a.append(f"[{a_tag}]")

    n = len(segments)
    filter_parts.append(f"{''.join(concat_v)}concat=n={n}:v=1:a=0[vout]")
    filter_parts.append(f"{''.join(concat_a)}concat=n={n}:v=0:a=1[aout]")

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", source_video,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        out_video
    ]
    print(f"[Composer] Speed-ramping {len(segments)} segments to {total_timeline:.1f}s timeline...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return total_timeline


def get_video_duration(video_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", video_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 95.0


def compose_final_short(video_input: str, twelvelabs_or_script: dict, script_data: dict = None, out_video: str = None) -> str:
    """
    Main Assembly Pipeline:
    Overlays synthesized Liam voice, SFX, and safe-zone subtitles onto the speed-ramped video.
    """
    if script_data is None:
        # Pre-ramped video passed directly: compose_final_short(ramped_video, script_data, out_video)
        script_data = twelvelabs_or_script
        ramped_base = video_input
        total_timeline = get_video_duration(ramped_base)
        cleanup_ramped = False
    else:
        # Raw video passed: compose_final_short(raw_video, twelvelabs_data, script_data, out_video)
        segments = twelvelabs_or_script.get("segments", [])
        ramped_base = os.path.join(SCRATCH_DIR, "temp_ramped_base.mp4")
        total_timeline = build_speed_ramped_base_video(video_input, segments, ramped_base)
        cleanup_ramped = True

    if out_video is None:
        out_video = os.path.join(SCRATCH_DIR, "viral_short_output.mp4")

    # 1. Synthesize Liam speech lines
    speech_lines = script_data.get("speech", [])
    speech_clips = []
    print(f"[Composer] Synthesizing {len(speech_lines)} Liam speech lines...")
    for idx, item in enumerate(speech_lines):
        line_id = item[0] if len(item) > 2 else f"line_{idx:02d}"
        st = float(item[1]) if len(item) > 2 else 0.5
        text = str(item[2]) if len(item) > 2 else str(item[0])
        mp3_out = os.path.join(SCRATCH_DIR, f"tts_{line_id}.mp3")
        tts_rotator.synthesize_speech(text, mp3_out)
        speech_clips.append({"path": mp3_out, "start": st})

    # 2. Mix master audio
    sfx_events = script_data.get("sfx", [])
    master_wav = os.path.join(SCRATCH_DIR, "temp_master_audio.wav")
    print(f"[Composer] Mixing audio track (Speech + {len(sfx_events)} SFX events)...")
    audio_sfx_mixer.mix_master_audio(speech_clips, sfx_events, total_timeline, master_wav)

    # 3. Build Subtitles
    ass_path = os.path.join(SCRATCH_DIR, "temp_subtitles.ass")
    sub_cues = script_data.get("subtitles", [])
    subtitle_engine.build_ass_subtitles(sub_cues, ass_path)

    # 4. Final Burn
    safe_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd_burn = [
        FFMPEG_BIN, "-y",
        "-i", ramped_base,
        "-i", master_wav,
        "-filter_complex", f"[0:v]subtitles='{safe_ass}'[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-crf", "20",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        out_video
    ]
    print(f"[Composer] Rendering final Short: {out_video}...")
    subprocess.run(cmd_burn, check=True)



    # Cleanup temporary base if created internally
    if cleanup_ramped and os.path.exists(ramped_base):
        try:
            os.remove(ramped_base)
        except Exception:
            pass

    print(f"[Composer] Master Short rendered successfully ({os.path.getsize(out_video) / (1024*1024):.1f} MB)!")
    return out_video
