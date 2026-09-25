import argparse
import os
import random
import shutil
import subprocess
import uuid

from moviepy.editor import AudioFileClip

from . import config
from . import script_writer
from . import kids_script
from . import tts_engine
from . import subtitles
from . import visuals
from . import video_builder
from . import music


def _audio_duration(path: str) -> float:
    clip = AudioFileClip(path)
    d = clip.duration
    clip.close()
    return d


def _trim_audio(path: str, max_sec: float, out_path: str):
    cmd = ["ffmpeg", "-y", "-i", path, "-t", f"{max_sec:.2f}", "-c", "copy", out_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore")[-2500:] if e.stderr else "(stderr yok)"
        raise RuntimeError(f"ffmpeg ses kırpma hatası (exit {e.returncode}):\n{err}") from e
    return out_path


def _fit_short_duration(topic, lang, audience, work_dir):
    """45-55 saniye hedefine ulaşana kadar senaryoyu üretir/uzatır/kısaltır."""
    title, script = script_writer.generate_script(topic, lang, audience, "short")
    audio_path = os.path.join(work_dir, "speech.mp3")
    word_timings = tts_engine.synthesize_speech(script, lang, audience, audio_path)
    duration = _audio_duration(audio_path)

    attempts = 0
    while duration < config.SHORT_MIN_SEC and attempts < 2:
        script += " " + script_writer._offline_short_script(topic, lang, audience)[1]
        word_timings = tts_engine.synthesize_speech(script, lang, audience, audio_path)
        duration = _audio_duration(audio_path)
        attempts += 1

    if duration > config.SHORT_MAX_SEC:
        trimmed_path = os.path.join(work_dir, "speech_trimmed.mp3")
        _trim_audio(audio_path, config.SHORT_MAX_SEC, trimmed_path)
        audio_path = trimmed_path
        word_timings = [w for w in word_timings if w["end"] <= config.SHORT_MAX_SEC]
        duration = config.SHORT_MAX_SEC

    return title, audio_path, word_timings, duration


def _fit_long_duration(topic, lang, audience, work_dir):
    title, script = script_writer.generate_script(topic, lang, audience, "long")
    audio_path = os.path.join(work_dir, "speech.mp3")
    word_timings = tts_engine.synthesize_speech(script, lang, audience, audio_path)
    duration = _audio_duration(audio_path)

    max_allowed = config.LONG_TARGET_SEC + 60
    if duration > max_allowed:
        trimmed_path = os.path.join(work_dir, "speech_trimmed.mp3")
        _trim_audio(audio_path, max_allowed, trimmed_path)
        audio_path = trimmed_path
        word_timings = [w for w in word_timings if w["end"] <= max_allowed]
        duration = max_allowed

    return title, audio_path, word_timings, duration


def _fit_kids_episode(lang, work_dir):
    """En az config.KIDS_MIN_SEC (10 dakika) süren, iki karakterli
    (Sunucu + Hayvan Arkadaş) bir çocuk bölümü üretir. Üst sınır yoktur."""
    title, lines = kids_script.build_episode(lang)
    audio_path = os.path.join(work_dir, "speech.mp3")
    word_timings, duration = tts_engine.synthesize_dialogue(lines, lang, audio_path)

    attempts = 0
    while duration < config.KIDS_MIN_SEC and attempts < 2:
        print(f"[main] Bölüm {duration:.0f}sn, hedefin altında. Ek segmentle yeniden üretiliyor.", flush=True)
        title, lines = kids_script.build_episode(lang)
        word_timings, duration = tts_engine.synthesize_dialogue(lines, lang, audio_path)
        attempts += 1

    return title, audio_path, word_timings, duration


def generate_one(topic, lang, audience, video_type, subtitle_lang, index, out_dir):
    work_dir = os.path.join(config.OUTPUT_DIR, "_work", str(uuid.uuid4())[:8])
    os.makedirs(work_dir, exist_ok=True)

    is_kids_episode = (audience == "kids")

    if is_kids_episode:
        title, audio_path, word_timings, duration = _fit_kids_episode(lang, work_dir)
        size = config.LONG_SIZE
        video_type = "episode"
    elif video_type == "short":
        title, audio_path, word_timings, duration = _fit_short_duration(topic, lang, audience, work_dir)
        size = config.SHORT_SIZE
    else:
        title, audio_path, word_timings, duration = _fit_long_duration(topic, lang, audience, work_dir)
        size = config.LONG_SIZE

    print(f"[{index}] '{title}' -> {duration:.1f}sn ({lang}, {audience}, {video_type})")

    scene_durations = video_builder.compute_scene_durations(duration, "long" if is_kids_episode else video_type)
    print(f"[main] Video {len(scene_durations)} farklı sahneye bölünüyor "
          f"(ortalama {duration/len(scene_durations):.1f}sn/sahne)", flush=True)

    if is_kids_episode:
        backgrounds = [
            visuals.get_background(random.choice(visuals.KIDS_KEYWORDS), size, work_dir, index=i)
            for i in range(len(scene_durations))
        ]
    else:
        keyword = topic if topic else title
        if lang != "en":
            try:
                from deep_translator import GoogleTranslator
                keyword_en = GoogleTranslator(source=lang, target="en").translate(keyword)
                print(f"[main] Görsel arama kelimesi çevrildi: '{keyword}' -> '{keyword_en}'", flush=True)
                keyword = keyword_en
            except Exception as e:
                print(f"[main] Anahtar kelime çevirisi başarısız, orijinali kullanılıyor: {e}", flush=True)
        backgrounds = [
            visuals.get_background(keyword, size, work_dir, index=i)
            for i in range(len(scene_durations))
        ]

    music_path = None
    if is_kids_episode:
        music_path = os.path.join(work_dir, "bg_music.wav")
        music.generate_background_music(music_path)

    no_subs_path = video_builder.assemble_video(backgrounds, scene_durations, audio_path, title, size,
                                                  work_dir, music_path=music_path)

    # Karaoke tarzı, kelime kelime renklenen altyazı için .ass kullanılıyor.
    # Stil (renk, konum, font) subtitles.build_ass() içinde .ass dosyasına
    # gömülüyor; burn_subtitles bu stili ffmpeg/libass üzerinden olduğu gibi yakar.
    ass_path = os.path.join(work_dir, "captions.ass")
    subtitles.build_ass(word_timings, ass_path, subtitle_lang, lang, size)

    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip().replace(" ", "_")[:40]
    final_name = f"{index:02d}_{safe_title or 'video'}_{video_type}.mp4"
    final_path = os.path.join(out_dir, final_name)
    video_builder.burn_subtitles(no_subs_path, ass_path, final_path, size)

    shutil.rmtree(work_dir, ignore_errors=True)
    return final_path


def main():
    parser = argparse.ArgumentParser(description="YouTube Shorts / eğitici video üretici")
    parser.add_argument("--topics", type=str, default="",
                         help="Virgülle ayrılmış konu listesi. Boşsa rastgele konular kullanılır.")
    parser.add_argument("--lang", choices=["tr", "en"], default="tr", help="Seslendirme dili")
    parser.add_argument("--subtitle-lang", choices=["tr", "en"], default=None,
