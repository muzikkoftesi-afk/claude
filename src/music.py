"""
Çocuk bölümleri için, tamamen kod ile (hiçbir dış kaynak/lisans olmadan) üretilen
neşeli, basit bir döngü melodisi oluşturur. Bu gerçek bir stüdyo müziği değildir;
telif hakkı riski taşımayan, nazikçe çalan bir arka plan sesi hedefler.
"""
import math
import wave
import struct

SAMPLE_RATE = 22050

# Pentatonik gam (C majör pentatonik), her zaman hoş ve çocuksu bir ton verir
NOTE_FREQS = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.00, "A4": 440.00,
    "C5": 523.25, "D5": 587.33, "E5": 659.25,
}

MELODY_PATTERN = [
    "C4", "E4", "G4", "E4", "D4", "G4", "C5", "G4",
    "A4", "G4", "E4", "D4", "C4", "D4", "E4", "C4",
]

NOTE_DURATION = 0.4  # saniye


def _envelope(n_samples):
    """Tık sesini önlemek için yumuşak giriş/çıkış (kısa fade in/out)."""
    fade = max(1, int(n_samples * 0.15))
    env = [1.0] * n_samples
    for i in range(fade):
        v = i / fade
        env[i] = v
        env[-(i + 1)] = v
    return env


def _generate_samples():
    samples = []
    for note in MELODY_PATTERN:
        freq = NOTE_FREQS[note]
        n = int(SAMPLE_RATE * NOTE_DURATION)
        env = _envelope(n)
        for i in range(n):
            t = i / SAMPLE_RATE
            # ana ton + hafif üst harmonik (daha sıcak/oyuncak bir ses için)
            value = 0.6 * math.sin(2 * math.pi * freq * t)
            value += 0.15 * math.sin(2 * math.pi * freq * 2 * t)
            samples.append(value * env[i] * 0.18)  # düşük genlik: kısık, rahatsız etmeyen seviye
    return samples


def generate_background_music(out_path: str) -> str:
    """Birkaç saniyelik bir döngü üretir; video_builder bunu gerekli süreye
    kadar otomatik olarak tekrarlar (loop)."""
    samples = _generate_samples()
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        frames = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * 32767)))) for s in samples)
        wf.writeframes(frames)
    return out_path
