"""
edge-tts'den gelen kelime zamanlamalarını kullanarak SRT alt yazı dosyası üretir.
Alt yazı dili, seslendirme dilinden farklı istenirse (ör. ses TR, alt yazı EN)
her yazı bloğu çevrilip zaman damgaları (yaklaşık) korunur.
"""
from . import config


def _fmt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _chunk_words(word_timings, words_per_line=5):
    chunks = []
    for i in range(0, len(word_timings), words_per_line):
        group = word_timings[i:i + words_per_line]
        text = " ".join(w["text"] for w in group)
        chunks.append({"text": text, "start": group[0]["start"], "end": group[-1]["end"]})
    return chunks


def build_srt(word_timings, srt_path: str, subtitle_lang: str, audio_lang: str):
    chunks = _chunk_words(word_timings)

    if subtitle_lang != audio_lang:
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=audio_lang, target=subtitle_lang)
            for c in chunks:
                c["text"] = translator.translate(c["text"])
        except Exception as e:
            print(f"[subtitles] Çeviri başarısız, orijinal dil kullanılıyor: {e}")

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, c in enumerate(chunks, start=1):
            f.write(f"{i}\n")
            f.write(f"{_fmt_time(c['start'])} --> {_fmt_time(c['end'])}\n")
            f.write(f"{c['text']}\n\n")
    return srt_path
