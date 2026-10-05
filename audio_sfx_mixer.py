import os
import subprocess
import numpy as np
from scipy.io import wavfile

FFMPEG_BIN = r"C:\Users\ladu\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
SCRATCH_DIR = r"C:\Users\ladu\.gemini\antigravity\scratch"
VAULT_DIR = os.path.join(SCRATCH_DIR, "meme_sound_vault")
SAMPLE_RATE = 44100


def load_vault_audio(filename: str, sr=SAMPLE_RATE) -> np.ndarray:
    """Loads an MP3/WAV from meme_sound_vault converted to float32 mono."""
    path = os.path.join(VAULT_DIR, filename)
    if not os.path.exists(path):
        # Try without extension
        if os.path.exists(path + ".mp3"):
            path = path + ".mp3"
        elif os.path.exists(path + ".wav"):
            path = path + ".wav"
        else:
            return None

    temp_wav = os.path.join(SCRATCH_DIR, f"temp_{os.path.basename(path)}.wav")
    try:
        subprocess.run(
            [FFMPEG_BIN, "-y", "-i", path, "-ar", str(sr), "-ac", "1", temp_wav],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        _, data = wavfile.read(temp_wav)
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        return data.astype(np.float32) / 32768.0
    except Exception as e:
        print(f"[Mixer] Error loading vault sound {filename}: {e}")
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        return None


def create_sfx_library(sr=SAMPLE_RATE):
    """Procedurally synthesizes standard meme SFX with high punch as fallbacks."""
    sfx = {}
    
    # 1. Vine Boom (Sub-bass drop + distortion punch)
    t_vb = np.linspace(0, 0.85, int(sr * 0.85), endpoint=False)
    freq_sweep = 68 * np.exp(-4.2 * t_vb)
    vb = (np.sin(2 * np.pi * freq_sweep * t_vb) * 0.85 + np.sin(2 * np.pi * 34 * t_vb) * 0.5) * np.exp(-3.2 * t_vb)
    sfx["vine_boom_synth"] = vb * 0.95

    # 2. Metal Clang / Padlock (Iron snap + bell harmonic)
    t_c = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
    metal = (np.sin(2 * np.pi * 740 * t_c) + np.sin(2 * np.pi * 1440 * t_c) * 0.6) * np.exp(-11 * t_c)
    sfx["metal_clang"] = metal * 0.75

    # 3. Comic Whistle / Flutter (Magic summon)
    t_fl = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    flutter = np.sin(2 * np.pi * (820 + 380 * np.sin(2 * np.pi * 16 * t_fl)) * t_fl) * np.exp(-3.2 * t_fl)
    sfx["flutter"] = flutter * 0.4

    # 4. Action Horn / Brass Blast (James Bond sting)
    t_hn = np.linspace(0, 0.65, int(sr * 0.65), endpoint=False)
    horn = (np.sin(2 * np.pi * 220 * t_hn) + np.sin(2 * np.pi * 440 * t_hn) * 0.8 + np.sin(2 * np.pi * 660 * t_hn) * 0.4) * np.exp(-2.4 * t_hn)
    sfx["horn"] = horn * 0.65

    # 5. Spooky Ghost Slide
    t_gh = np.linspace(0, 0.8, int(sr * 0.8), endpoint=False)
    ghost = np.sin(2 * np.pi * (480 + 220 * np.sin(2 * np.pi * 4.5 * t_gh)) * t_gh) * np.sin(np.pi * t_gh / 0.8)
    sfx["ghost"] = ghost * 0.45

    # 6. Dirt Digging Thud / Pop Escape
    t_pop = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
    pop = np.sin(2 * np.pi * (180 + 650 * np.exp(-22 * t_pop)) * t_pop) * np.exp(-12 * t_pop)
    sfx["pop"] = pop * 0.85

    # 7. Beer Glass Cheers (Local pub victory)
    t_gl = np.linspace(0, 0.55, int(sr * 0.55), endpoint=False)
    glass = (np.sin(2 * np.pi * 2750 * t_gl) + np.sin(2 * np.pi * 4150 * t_gl) * 0.7) * np.exp(-7.5 * t_gl)
    sfx["cheers"] = glass * 0.55

    # 8. Fanfare & Wheeze Laugh
    t_fn = np.linspace(0, 2.4, int(sr * 2.4), endpoint=False)
    fanfare = (np.sin(2 * np.pi * 440 * t_fn) + np.sin(2 * np.pi * 554.37 * t_fn) + np.sin(2 * np.pi * 659.25 * t_fn)) * 0.22 * np.exp(-0.75 * t_fn)
    wheeze = np.random.uniform(-1, 1, len(t_fn)) * (np.sin(2 * np.pi * 5 * t_fn) ** 2) * 0.12 * np.exp(-t_fn * 0.6)
    sfx["win_fanfare"] = fanfare + wheeze

    return sfx


def build_bgm_track(total_len_sec: float, sr=SAMPLE_RATE) -> np.ndarray:
    """Generates an energetic 128 BPM comedy groove."""
    total_samples = int(total_len_sec * sr)
    bgm = np.zeros(total_samples, dtype=np.float32)
    beat_dur = 0.46875  # 128 BPM
    
    total_beats = int(total_len_sec / beat_dur)
    for b in range(total_beats):
        t_b = b * beat_dur
        idx = int(t_b * sr)
        dur = int(0.22 * sr)
        t_p = np.linspace(0, 0.22, dur, endpoint=False)
        
        freq = 98.0 if (b % 4 < 2) else 130.81
        bass = (np.sin(2 * np.pi * freq * t_p) + np.sin(4 * np.pi * freq * t_p) * 0.4) * np.exp(-14 * t_p) * 0.20
        snap = np.random.uniform(-1, 1, dur) * np.exp(-35 * t_p) * 0.04
        
        if idx + dur < total_samples:
            bgm[idx:idx+dur] += bass + snap
            
    return bgm * 0.35


def mix_master_audio(speech_clips: list, sfx_events: list, total_len_sec: float, out_wav_path: str):
    """
    speech_clips: list of dicts [{'path': '...mp3', 'start': float}]
    sfx_events: list of tuples [('vine_boom.mp3', 4.0), ('bruh.mp3', 6.5), ...]
    """
    sr = SAMPLE_RATE
    total_samples = int(total_len_sec * sr)
    
    dialogue = np.zeros(total_samples, dtype=np.float32)
    sfx_layer = np.zeros(total_samples, dtype=np.float32)
    
    # 1. Overlay speech clips
    temp_wav = out_wav_path.replace(".wav", "_temp_speech.wav")
    for clip in speech_clips:
        mp3 = clip["path"]
        st = clip["start"]
        subprocess.run([FFMPEG_BIN, "-y", "-i", mp3, "-ar", str(sr), "-ac", "1", temp_wav],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _, data = wavfile.read(temp_wav)
        data = data.astype(np.float32) / 32768.0
        
        idx = int(st * sr)
        end_idx = min(idx + len(data), total_samples)
        dialogue[idx:end_idx] += data[:end_idx - idx]
        
    if os.path.exists(temp_wav):
        os.remove(temp_wav)

    # 2. Overlay SFX from meme vault or synth library
    synth_lib = create_sfx_library(sr)
    for sfx_item in sfx_events:
        # Format can be (name, time) or (name, time, gain)
        if len(sfx_item) == 2:
            sfx_name, t_sec = sfx_item
            gain = 1.0
        else:
            sfx_name, t_sec, gain = sfx_item

        wave = None
        # Check vault first
        wave = load_vault_audio(sfx_name, sr)
        if wave is None and sfx_name in synth_lib:
            wave = synth_lib[sfx_name]

        if wave is not None:
            wave = wave * gain
            idx = int(t_sec * sr)
            end_idx = min(idx + len(wave), total_samples)
            sfx_layer[idx:end_idx] += wave[:end_idx - idx]
            print(f"[Mixer] Mixed meme SFX '{sfx_name}' at {t_sec:.2f}s (gain={gain})")

    # 3. Add BGM groove
    bgm = build_bgm_track(total_len_sec, sr)

    # 4. Master Gain & Limiter
    dialogue = dialogue * 1.40
    sfx_layer = sfx_layer * 0.90
    master = dialogue + sfx_layer + bgm
    
    peak = np.max(np.abs(master))
    if peak > 0.98:
        master = master / peak * 0.96

    wavfile.write(out_wav_path, sr, (master * 32767).astype(np.int16))
    print(f"[Mixer] Master audio rendered: {out_wav_path} ({os.path.getsize(out_wav_path) / (1024*1024):.2f} MB)")
