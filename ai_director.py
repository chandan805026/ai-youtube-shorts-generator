import os
import sys
import json
import requests

def generate_script_and_metadata(video_info):
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    raw_title = video_info.get("title", "China Crazy Gadget Invention")

    default_script = (
        "भाईसाहब! चीन के इस अतरंगी बंदे ने बना दिया दुनिया का सबसे अनोखा गैजेट! "
        "ये देखो, इन्होंने ऐसा जुगाड़ू फिशिंग रॉड बनाया है, जिसमें मछली फंसते ही मंदिर का घंटा बजने लगता है! "
        "ताकि मछली पकड़ने के साथ-साथ थोड़ा पुण्य भी मिल जाए! "
        "चीन वालों का ये खतरनाक दिमाग आपको कैसा लगा, कमेंट में जरूर बताओ और सब्सक्राइब कर लो!"
    )
    default_meta = {
        "title": "China Ka Sabse Khatarnak Gadget 😱 #shorts #gadgets #viral",
        "script": default_script,
        "description": "China Ka Sabse Khatarnak Funny Gadget Invention! #shorts #gadgets #viral #trending #funny #shortsfeed",
        "tags": ["shorts", "gadgets", "funny", "china gadget", "invention", "viral shorts", "trending"]
    }

    if not gemini_key:
        print("Using default viral gadget script.")
        return default_meta

    prompt = f"""
    You are an expert YouTube Shorts creator for an Indian audience.
    A viral Chinese inventor made this crazy gadget video:
    Context/Title: "{raw_title}"

    Write a 20-second HIGH-ENERGY, FUNNY, SUSPENSEFUL Hindi commentary script for this Short.
    Rules:
    1. Hook the viewer in the first 2 seconds (e.g. 'भाईसाहब! चीन के इस बंदे ने क्या बना दिया...', 'दोस्तों आज चीन का ये अजीबोगरीब गैजेट देखकर आपके होश उड़ जाएंगे...').
    2. Speak in simple, spoken Hinglish/Hindi that Indian viewers love.
    3. Keep it punchy, funny, and end with a quick call-to-action to comment and subscribe.
    4. Length: 50-70 words (perfect for 18-24 seconds voiceover).
    5. Return ONLY a valid JSON object with keys: "title" (under 90 chars including #shorts), "script" (pure spoken Hindi without emojis for TTS), "description", "tags" (list of strings).
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text_out)
            print(f"Generated Script via Gemini: {parsed.get('title')}")
            return parsed
    except Exception as e:
        print(f"Gemini API fallback notice: {e}")

    return default_meta
