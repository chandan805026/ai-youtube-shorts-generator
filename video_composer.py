import os
import sys
import subprocess
import json
import re
import tts_rotator
import audio_sfx_mixer
import subtitle_engine


def sanitize_speech_text(text: str) -> str:
    if not text:
        return ""
    # 1. Remove file extensions .mp3, .wav, .ogg
    text = re.sub(r'\b[\w\-]+(?:\.mp3|\.wav|\.ogg)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\.(?:mp3|wav|ogg)\b', '', text, flags=re.IGNORECASE)

    # 2. Remove bracketed/parenthesized tags like [vine_boom], (sfx), [sound]
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\*.*?\*', '', text)

    # 3. Remove SFX / Sound labels
    text = re.sub(r'\b(?:SFX|SOUND EFFECT|FX|MEME)\s*:?\b', '', text, flags=re.I)

    # 4. Remove standalone meme sound names if present
    sfx_patterns = [
        r'\bvine[\s_\-]*boom\b', r'\bwindows[\s_\-]*error\b', r'\bmetal[\s_\-]*pipe\b',
        r'\bsad[\s_\-]*violin\b', r'\btitanic[\s_\-]*bad[\s_\-]*recorder\b',
        r'\bno[\s_\-]*god[\s_\-]*please[\s_\-]*no\b', r'\bincorrect[\s_\-]*buzzer\b',
        r'\boh[\s_\-]*no[\s_\-]*wheeze[\s_\-]*laugh\b', r'\bsuspense[\s_\-]*sting\b',
        r'\bfbi[\s_\-]*open[\s_\-]*up\b', r'\bding[\s_\-]*idea\b', r'\bwait[\s_\-]*a[\s_\-]*minute\b',
        r'\banime[\s_\-]*wow\b', r'\bbruh\b', r'\byeet\b', r'\brizz\b'
    ]
    for pat in sfx_patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)

    # 5. Clean up extra punctuation and spaces
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^[\s\-_:,\.]+|[\s\-_:,\.]+$', '', text).strip()
    return text


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
    prev_end_time = 0.0

    print(f"[Composer] Synthesizing speech lines with Zero-Drift Scene Anchoring...")
    for idx, item in enumerate(speech_lines):
        line_id = item[0] if len(item) > 2 else f"line_{idx:02d}"
        target_t = float(item[1]) if len(item) > 2 else 0.5
        raw_text = str(item[2]) if len(item) > 2 else str(item[0])

        # 1. Sanitize text: Completely remove meme names, .mp3, brackets, sound tags
        text = sanitize_speech_text(raw_text)
        words = text.split()
        if len(words) < 2:
            print(f"[Composer] Skipping non-dialogue line {idx}: '{raw_text}'")
            continue

        mp3_out = os.path.join(SCRATCH_DIR, f"tts_{line_id}.mp3")
        tts_rotator.synthesize_speech(text, mp3_out)
        clip_dur = get_audio_duration(mp3_out)

        # Look ahead to find next speech line's visual timestamp
        next_target_t = None
        for nxt in speech_lines[idx + 1:]:
            nxt_txt = sanitize_speech_text(str(nxt[2]) if len(nxt) > 2 else str(nxt[0]))
            if len(nxt_txt.split()) >= 2:
                next_target_t = float(nxt[1]) if len(nxt) > 2 else float(nxt[1]) + 5.0
                break

        # If this line would overlap into the next scene, gently fit its tempo (1.02x - 1.25x)
        if next_target_t is not None and (target_t + clip_dur) > (next_target_t - 0.2) and (next_target_t > target_t):
            avail_window = max(1.2, next_target_t - target_t - 0.2)
            needed_rate = clip_dur / avail_window
            speed_rate = min(1.25, max(1.02, needed_rate))
            faster_mp3 = os.path.join(SCRATCH_DIR, f"tts_{line_id}_fit.mp3")
            try:
                cmd_speed = [
                    FFMPEG_BIN, "-y",
                    "-i", mp3_out,
                    "-filter:a", f"atempo={speed_rate:.3f}",
                    "-vn",
                    faster_mp3
                ]
                subprocess.run(cmd_speed, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                mp3_out = faster_mp3
                clip_dur = get_audio_duration(mp3_out)
            except Exception:
                pass

        # Scene-Anchor: Always anchor firmly at the true visual timestamp target_t!
        # If previous line ran slightly over, shift ONLY by the tiny overlap, but never cascade!
        actual_st = max(target_t, prev_end_time + 0.1)
        prev_end_time = actual_st + clip_dur

        speech_clips.append({"path": mp3_out, "start": actual_st, "dur": clip_dur})

        # 2. Build 100% word-accurate subtitles matching what is SPOKEN
        clean_ascii = re.sub(r'[^\x20-\x7E]+', ' ', text).strip()
        sub_words = clean_ascii.split()
        if sub_words:
            n_w = len(sub_words)
            if n_w <= 7:
                chunks = [" ".join(sub_words)]
            elif n_w <= 13:
                mid = (n_w + 1) // 2
                chunks = [" ".join(sub_words[:mid]), " ".join(sub_words[mid:])]
            else:
                t1 = (n_w + 2) // 3
                t2 = (2 * n_w + 1) // 3
                chunks = [
                    " ".join(sub_words[:t1]),
                    " ".join(sub_words[t1:t2]),
                    " ".join(sub_words[t2:])
                ]

            dur_per_chunk = clip_dur / len(chunks)
            for c_i, ch in enumerate(chunks):
                ch_st = actual_st + (c_i * dur_per_chunk)
                ch_et = actual_st + ((c_i + 1) * dur_per_chunk)
                sub_items.append({
                    "start": round(ch_st / speed_factor, 2),
                    "end": round(ch_et / speed_factor, 2),
                    "text": ch.upper(),
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
