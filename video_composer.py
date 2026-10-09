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


def apply_audio_tempo(in_path: str, out_path: str, speed: float) -> str:
    """Matches the audio playback tempo to the video segment speed."""
    if abs(speed - 1.0) < 0.05:
        return in_path
    if speed <= 2.0:
        filter_str = f"atempo={speed:.3f}"
    else:
        s2 = speed / 2.0
        filter_str = f"atempo=2.0,atempo={s2:.3f}"
    cmd = [FFMPEG_BIN, "-y", "-i", in_path, "-filter:a", filter_str, out_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_path


def get_audio_duration(audio_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", audio_path]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 3.0


def compose_final_short(video_input: str, twelvelabs_or_script: dict, script_data: dict = None, out_video: str = None) -> str:
    """
    Main Assembly Pipeline:
    Overlays synthesized Liam voice, SFX, and safe-zone subtitles onto the speed-ramped video.
    Synchronizes audio tempo to match video speed ramping (1.5x on normal, 2.3x on fast-forward).
    """
    if script_data is None:
        # Pre-ramped video passed directly: compose_final_short(ramped_video, script_data, out_video)
        script_data = twelvelabs_or_script
        ramped_base = video_input
        total_timeline = get_video_duration(ramped_base)
        cleanup_ramped = False
        segments = []
    else:
        # Raw video passed: compose_final_short(raw_video, twelvelabs_data, script_data, out_video)
        segments = twelvelabs_or_script.get("segments", [])
        ramped_base = os.path.join(SCRATCH_DIR, "temp_ramped_base.mp4")
        total_timeline = build_speed_ramped_base_video(video_input, segments, ramped_base)
        cleanup_ramped = True

    if out_video is None:
        out_video = os.path.join(SCRATCH_DIR, "viral_short_output.mp4")

    # Build timeline segment speed map
    intervals = []
    curr_t = 0.0
    for seg in segments:
        spd = float(seg.get("speed", 1.5))
        dur = (float(seg["end"]) - float(seg["start"])) / spd
        intervals.append({"start": curr_t, "end": curr_t + dur, "speed": spd})
        curr_t += dur

    # 1. Synthesize Liam speech lines with video-matched speed tempo
    speech_lines = script_data.get("speech", [])
    speech_clips = []
    speed_matched_subtitles = []
    sub_cues = script_data.get("subtitles", [])
    next_avail = 0.0

    print(f"[Composer] Synthesizing {len(speech_lines)} Liam speech lines with dynamic video-speed tempo matching...")
    for idx, item in enumerate(speech_lines):
        line_id = item[0] if len(item) > 2 else f"line_{idx:02d}"
        st = float(item[1]) if len(item) > 2 else 0.5
        text = str(item[2]) if len(item) > 2 else str(item[0])

        # Prevent dialogue collision/overlap
        if st < next_avail:
            st = next_avail

        # Find the video speed at this exact timestamp
        seg_speed = 1.35  # default comedy base speed
        for inter in intervals:
            if inter["start"] <= st < inter["end"]:
                seg_speed = inter["speed"]
                break

        raw_mp3 = os.path.join(SCRATCH_DIR, f"tts_raw_{line_id}.mp3")
        sped_mp3 = os.path.join(SCRATCH_DIR, f"tts_sped_{line_id}.mp3")

        tts_rotator.synthesize_speech(text, raw_mp3)
        final_mp3 = apply_audio_tempo(raw_mp3, sped_mp3, seg_speed)
        sped_dur = get_audio_duration(final_mp3)

        print(f"[Composer] Line {line_id} at {st:.1f}s -> tempo matched to {seg_speed:.1f}x (duration: {sped_dur:.2f}s)")
        speech_clips.append({"path": final_mp3, "start": st})
        next_avail = st + sped_dur + 0.2

        # Match subtitle display to the exact spoken duration of this line
        sub_text = ""
        if idx < len(sub_cues) and "text" in sub_cues[idx]:
            sub_text = sub_cues[idx]["text"]
        else:
            words = text.split()
            sub_text = " ".join(words[:4]).upper() + " 💥"

        speed_matched_subtitles.append({
            "start": round(st, 2),
            "end": round(st + sped_dur, 2),
            "text": sub_text,
            "style": "CenterPunch"
        })

    # 2. Mix master audio
    sfx_events = script_data.get("sfx", [])
    master_wav = os.path.join(SCRATCH_DIR, "temp_master_audio.wav")
    print(f"[Composer] Mixing audio track (Speech + {len(sfx_events)} SFX events)...")
    audio_sfx_mixer.mix_master_audio(speech_clips, sfx_events, total_timeline, master_wav)

    # 3. Build Subtitles
    ass_path = os.path.join(SCRATCH_DIR, "temp_subtitles.ass")
    subtitle_engine.build_ass_subtitles(speed_matched_subtitles, ass_path)

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
