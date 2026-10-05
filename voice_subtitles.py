import asyncio
import os
import sys
import re
import edge_tts

VOICE = "hi-IN-MadhurNeural"

async def generate_voice_and_subtitles(script_text, audio_path="voice.mp3", ass_path="subtitles.ass"):
    print(f"Generating Edge-TTS Hindi Voiceover ({VOICE})...")
    comm = edge_tts.Communicate(script_text, VOICE, rate="+10%")
    sub_maker = edge_tts.SubMaker()

    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)

    raw_srt = sub_maker.get_srt()
    convert_srt_to_hormozi_ass(raw_srt, ass_path)
    print("Voiceover and Subtitles generated successfully!")
    return audio_path, ass_path

def convert_srt_to_hormozi_ass(srt_text, ass_path):
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hormozi,Arial,65,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,2,40,40,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    blocks = srt_text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = " ".join(lines[2:]).strip()
            text = re.sub(r'<[^>]+>', '', text)
            if "-->" in time_line:
                start_p, end_p = time_line.split("-->")
                start_ass = srt_time_to_ass(start_p.strip())
                end_ass = srt_time_to_ass(end_p.strip())
                events.append(f"Dialogue: 0,{start_ass},{end_ass},Hormozi,,0,0,0,,{text}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

def srt_time_to_ass(t_str):
    t_str = t_str.replace(',', '.')
    parts = t_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        s_parts = s.split('.')
        sec = s_parts[0]
        cs = s_parts[1][:2] if len(s_parts) > 1 else "00"
        return f"{int(h)}:{m}:{sec}.{cs}"
    return "0:00:00.00"
