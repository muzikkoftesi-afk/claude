"""
edge-tts ile Microsoft'un ücretsiz nöral (insana yakın) sesleriyle seslendirme yapar.
Ayrıca alt yazı zamanlaması için kelime bazlı zaman damgaları döndürür.
"""
import asyncio
import random
import edge_tts

from . import config


async def _synthesize(text: str, voice: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice)
    word_timings = []  # [{"text": str, "start": float(sn), "end": float(sn)}]
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                f.write(chunk["data"])
            elif ctype == "WordBoundary":
                # edge-tts sürümüne göre alan adları değişebilir; esnek okuyoruz.
                offset = chunk.get("offset", chunk.get("Offset", 0))
                duration = chunk.get("duration", chunk.get("Duration", 0))
                word_text = chunk.get("text", chunk.get("Text", ""))
                start = offset / 10_000_000  # 100ns -> saniye
                dur = duration / 10_000_000
                word_timings.append({
                    "text": word_text,
                    "start": start,
                    "end": start + dur,
                })
    print(f"[tts_engine] edge-tts'den {len(word_timings)} kelime zamanlaması alındı.", flush=True)
    return word_timings


def _fallback_word_timings(text: str, audio_path: str):
    """edge-tts kelime zamanlaması vermezse, ses süresine göre kelimeleri
    yaklaşık ve eşit aralıklarla dağıtarak altyazı zamanlaması üretir."""
    from moviepy.editor import AudioFileClip
    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()

    words = text.split()
    if not words or duration <= 0:
        return []

    per_word = duration / len(words)
    timings = [
        {"text": w, "start": i * per_word, "end": (i + 1) * per_word}
        for i, w in enumerate(words)
    ]
    print(f"[tts_engine] Yedek (yaklaşık) zamanlama kullanıldı: {len(timings)} kelime, "
          f"toplam süre {duration:.1f}sn", flush=True)
    return timings


def synthesize_speech(text: str, lang: str, audience: str, out_path: str):
    voice_entry = config.VOICES[lang][audience]
    voice = random.choice(voice_entry) if isinstance(voice_entry, list) else voice_entry
    print(f"[tts_engine] Seçilen ses: {voice}", flush=True)
    word_timings = asyncio.run(_synthesize(text, voice, out_path))
    if not word_timings:
        word_timings = _fallback_word_timings(text, out_path)
    return word_timings


def synthesize_dialogue(lines: list, lang: str, out_path: str):
    """İki karakterli diyalog satırlarını (her biri kendi sesiyle) ayrı ayrı
    seslendirip tek bir ses dosyasında birleştirir, satırlar arasına doğal bir
    duraklama ekler. Global (tüm ses boyunca geçerli) kelime zamanlaması ve
    toplam süreyi döndürür: (word_timings, total_duration)."""
    from pydub import AudioSegment
    import os

    gap_ms = 350
    combined = AudioSegment.silent(duration=0)
    global_timings = []
    cumulative_sec = 0.0
    tmp_dir = os.path.dirname(out_path) or "."

    for i, line in enumerate(lines):
        voice = config.VOICES_DIALOGUE[lang][line["role"]]
        tmp_path = os.path.join(tmp_dir, f"_dlg_line_{i}.mp3")
        line_timings = asyncio.run(_synthesize(line["text"], voice, tmp_path))
        if not line_timings:
            line_timings = _fallback_word_timings(line["text"], tmp_path)

        for w in line_timings:
            global_timings.append({
                "text": w["text"],
                "start": w["start"] + cumulative_sec,
                "end": w["end"] + cumulative_sec,
            })

        seg = AudioSegment.from_file(tmp_path)
        seg_duration = len(seg) / 1000.0
        combined += seg
        combined += AudioSegment.silent(duration=gap_ms)
        cumulative_sec += seg_duration + (gap_ms / 1000.0)

        try:
            os.remove(tmp_path)
        except OSError:
            pass

    combined.export(out_path, format="mp3")
    print(f"[tts_engine] Diyalog seslendirmesi tamamlandı: {len(lines)} satır, "
          f"toplam süre {cumulative_sec:.1f}sn", flush=True)
    return global_timings, cumulative_sec
