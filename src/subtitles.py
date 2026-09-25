"""
edge-tts'den gelen kelime zamanlamalarını kullanarak alt yazı dosyası üretir.

build_srt: klasik .srt (düz, stilsiz) alt yazı üretir.
build_ass: TikTok/Shorts tarzı .ass alt yazı üretir — kelime kelime konuşulduğu
anda renk değişen karaoke efekti, ekranın alt %20'lik bandına sabit konum ve
font/renk gibi stil bilgisi dosyanın içine gömülür (burn_subtitles bu stili
olduğu gibi uygular, ekstra force_style gerekmez).

Her iki fonksiyonda da: alt yazı dili, seslendirme dilinden farklı istenirse
(ör. ses TR, alt yazı EN) metin çevrilir ve zaman damgaları (yaklaşık) korunur.
Ancak build_ass'ta çeviri yapılırsa kelime hizası bozulacağı için karaoke
vurgusu devre dışı kalır, düz (vurgusuz) metin gösterilir.
"""
from . import config


# ---------------------------------------------------------------------------
# .srt (klasik, stilsiz)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# .ass (karaoke tarzı, kelime kelime renklenen, alt %20 bantta sabit)
# ---------------------------------------------------------------------------

def _fmt_ass_time(t: float) -> str:
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:01}:{m:02}:{s:05.2f}"


def _sanitize(text: str) -> str:
    return text.replace("{", "").replace("}", "").replace("\\", "").replace("\n", " ")


def _chunk_word_groups(word_timings, words_per_line=3):
    groups = []
    for i in range(0, len(word_timings), words_per_line):
        groups.append(word_timings[i:i + words_per_line])
    return groups


def build_ass(word_timings, ass_path: str, subtitle_lang: str, audio_lang: str, size) -> str:
    if not word_timings:
        # boş olsa bile geçerli, açılabilir bir .ass dosyası üret
        word_timings = []

    groups = _chunk_word_groups(word_timings, words_per_line=3)
    karaoke_ok = (subtitle_lang == audio_lang)

    translator = None
    if not karaoke_ok:
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=audio_lang, target=subtitle_lang)
        except Exception as e:
            print(f"[subtitles] Çevirmen başlatılamadı, orijinal dil kullanılacak: {e}", flush=True)

    base = min(size)
    font_size = max(34, min(int(base * 0.062), 70))
    # Altyazı bloğu her zaman ekranın ALT %20'lik bandında kalacak şekilde
    # tabandan mesafe (MarginV) ayarlanır.
    margin_v = int(size[1] * 0.07)

    # Renkler ASS'de &HAABBGGRR biçiminde: Primary = konuşulmuş kelime (altın/vurgulu),
    # Secondary = henüz konuşulmamış kelime (beyaz).
    primary_gold = "&H0000D7FF"
    secondary_white = "&H00FFFFFF"
    outline_black = "&H00000000"
    shadow_dim = "&H64000000"

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {size[0]}\n"
        f"PlayResY: {size[1]}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,DejaVu Sans,{font_size},{primary_gold},{secondary_white},"
        f"{outline_black},{shadow_dim},1,0,0,0,100,100,0,0,1,3,1,2,60,60,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    lines = []
    for group in groups:
        if not group:
            continue
        start = group[0]["start"]
        end = group[-1]["end"]

        if karaoke_ok:
            cursor = start
            parts = []
            for w in group:
                dur_cs = max(1, round((w["end"] - cursor) * 100))
                parts.append(f"{{\\k{dur_cs}}}{_sanitize(w['text'])} ")
                cursor = w["end"]
            text_field = "".join(parts).strip()
        else:
            raw = " ".join(w["text"] for w in group)
            if translator:
                try:
                    raw = translator.translate(raw)
                except Exception:
                    pass
            text_field = _sanitize(raw)

        lines.append(
            f"Dialogue: 0,{_fmt_ass_time(start)},{_fmt_ass_time(end)},Default,,0,0,0,,{text_field}"
        )

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(lines))
        f.write("\n")

    return ass_path
