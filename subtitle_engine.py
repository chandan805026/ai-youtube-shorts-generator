import os

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CenterHook,Arial,44,&H0000FFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,5.5,2.5,2,30,30,420,1
Style: CenterPunch,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,6.5,3.0,2,30,30,420,1
Style: CenterWhite,Arial,44,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,5.5,2.5,2,30,30,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def to_ass_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass_subtitles(subtitle_items: list, out_path: str):
    """
    subtitle_items: list of dicts [{'start': 0.2, 'end': 4.1, 'text': '...', 'style': 'CenterPunch'}]
    """
    events = []
    for item in subtitle_items:
        st = to_ass_timestamp(item["start"])
        et = to_ass_timestamp(item["end"])
        style = item.get("style", "CenterPunch")
        text = item["text"].replace("\n", r"\N")
        events.append(f"Dialogue: 0,{st},{et},{style},,0,0,0,,{text}")

    full_content = ASS_HEADER + "\n".join(events) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"[Subtitles] Written {len(subtitle_items)} cues to {out_path} (Center Eye-Level Safe Zone)")
