import os
import subprocess

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, concatenate_videoclips, vfx, afx
)

from . import config

SCENE_CROSSFADE = 0.4  # saniye, sahneler arası yumuşak geçiş süresi


def _ken_burns_clip(image_path, size, duration):
    clip = ImageClip(image_path).set_duration(duration)
    clip = clip.resize(height=size[1] * 1.15)  # biraz büyük başla, zoom için pay bırak
    if clip.w < size[0]:
        clip = clip.resize(width=size[0] * 1.15)
    clip = clip.fx(vfx.resize, lambda t: 1 + 0.04 * (t / duration))  # yavaş zoom-in
    clip = clip.set_position(("center", "center"))
    return CompositeVideoClip([clip], size=size).set_duration(duration)


def _video_bg_clip(video_path, size, duration):
    clip = VideoFileClip(video_path)
    if clip.duration < duration:
        clip = clip.fx(vfx.loop, duration=duration)
    else:
        clip = clip.subclip(0, duration)
    clip = clip.resize(height=size[1])
    if clip.w < size[0]:
        clip = clip.resize(width=size[0])
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=size[0], height=size[1])
    return clip.set_duration(duration)


def _scene_clip(background: dict, size, duration: float):
    if background["type"] == "video":
        return _video_bg_clip(background["path"], size, duration)
    return _ken_burns_clip(background["path"], size, duration)


def compute_scene_durations(total_duration: float, video_type: str) -> list:
    """Videoyu birden fazla farklı görsel/video sahnesine böler.
    short: ~7 sn'lik sahneler (canlı, hızlı tempolu Shorts hissi).
    long: ~20 sn'lik sahneler, en fazla 30 sahne (API/işlem süresi dengesi için)."""
    target = 7.0 if video_type == "short" else 20.0
    count = max(3, round(total_duration / target))
    count = min(count, 30)
    base = total_duration / count
    durations = [base] * count
    # yuvarlama farkını son sahneye ekleyerek toplamı tam tutuyoruz
    durations[-1] += total_duration - sum(durations)
    return durations


def _make_title_overlay(title: str, size, out_path: str):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = int(size[0] * 0.065)
    max_width = size[0] * 0.80

    def wrap(font):
        words = title.split()
        lines, current = [], ""
        for w in words:
            test = (current + " " + w).strip()
            if draw.textlength(test, font=font) > max_width:
                if current:
                    lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    font = ImageFont.truetype(config.FONT_PATH, size=font_size) if os.path.exists(config.FONT_PATH) \
        else ImageFont.load_default()
    lines = wrap(font)

    tries = 0
    while len(lines) > 2 and tries < 3:
        font_size = int(font_size * 0.8)
        font = ImageFont.truetype(config.FONT_PATH, size=font_size) if os.path.exists(config.FONT_PATH) \
            else ImageFont.load_default()
        lines = wrap(font)
        tries += 1
    lines = lines[:2]

    line_height = int(font_size * 1.25)
    y0 = int(size[1] * 0.16)

    # Okunabilirlik için yazının arkasına hafif yarı saydam, yuvarlak köşeli bir zemin
    block_h = line_height * len(lines) + int(font_size * 0.4)
    max_line_w = max((draw.textlength(l, font=font) for l in lines), default=0)
    pad_x = int(font_size * 0.6)
    bx0 = (size[0] - max_line_w) / 2 - pad_x
    bx1 = (size[0] + max_line_w) / 2 + pad_x
    by0 = y0 - int(font_size * 0.25)
    by1 = y0 + block_h
    radius = int(font_size * 0.35)
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=radius, fill=(0, 0, 0, 110))

    y = y0
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (size[0] - w) / 2
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    img.save(out_path)
    return out_path


def _build_scene_track(backgrounds: list, scene_durations: list, size):
    """Sahneleri, aralarında yumuşak geçiş (crossfade) olacak şekilde birleştirir.
    Toplam süre, geçiş örtüşmesi telafi edilerek tam olarak scene_durations
    toplamına eşit tutulur."""
    n = len(scene_durations)
    if n == 1:
        clips = [_scene_clip(backgrounds[0], size, scene_durations[0])]
        return clips, concatenate_videoclips(clips, method="compose")

    overlap = min(SCENE_CROSSFADE, min(scene_durations) * 0.3)
    extra_each = (overlap * (n - 1)) / n
    padded_durations = [d + extra_each for d in scene_durations]

    clips = [_scene_clip(bg, size, dur) for bg, dur in zip(backgrounds, padded_durations)]
    clips = [clips[0]] + [c.crossfadein(overlap) for c in clips[1:]]

    bg_track = concatenate_videoclips(clips, method="compose", padding=-overlap)
    return clips, bg_track


def assemble_video(backgrounds: list, scene_durations: list, audio_path: str, title: str,
                    size, work_dir: str, music_path: str = None) -> str:
    os.makedirs(work_dir, exist_ok=True)
    total_duration = sum(scene_durations)

    scene_clips, bg_track = _build_scene_track(backgrounds, scene_durations, size)

    title_png = os.path.join(work_dir, "title_overlay.png")
    _make_title_overlay(title, size, title_png)
    title_clip = (ImageClip(title_png)
                  .set_duration(min(4, total_duration))
                  .set_start(0)
                  .crossfadeout(0.5))

    narration = AudioFileClip(audio_path).subclip(0, total_duration)

    music_clip = None
    if music_path and os.path.exists(music_path):
        music_clip = AudioFileClip(music_path)
        if music_clip.duration < total_duration:
            music_clip = afx.audio_loop(music_clip, duration=total_duration)
        else:
            music_clip = music_clip.subclip(0, total_duration)
        music_clip = music_clip.fx(afx.volumex, 0.12)
        final_audio = CompositeAudioClip([music_clip, narration])
    else:
        final_audio = narration

    final = CompositeVideoClip([bg_track, title_clip], size=size).set_audio(final_audio)
    no_subs_path = os.path.join(work_dir, "video_no_subs.mp4")
    final.write_videofile(no_subs_path, fps=30, codec="libx264", audio_codec="aac",
                           threads=4, preset="veryfast", logger=None)

    clips_to_close = [*scene_clips, bg_track, title_clip, narration, final]
    if music_clip is not None:
        clips_to_close.append(music_clip)
    for c in clips_to_close:
        try:
            c.close()
        except Exception:
            pass

    return no_subs_path


def burn_subtitles(video_path: str, caption_path: str, out_path: str, size=None):
    # caption_path artık bir .ass dosyası: font, renk, konum (alt %20 bandı) ve
    # kelime-kelime karaoke vurgusu dosyanın kendi Style/Events bölümünde tanımlı,
    # bu yüzden burada ayrıca force_style uygulamaya gerek yok.
    abs_caption_path = os.path.abspath(caption_path)
    if not os.path.isfile(abs_caption_path):
        raise RuntimeError(f"Altyazı dosyası bulunamadı: {abs_caption_path}")

    cap_dir = os.path.dirname(abs_caption_path)
    cap_name = os.path.basename(abs_caption_path)
    cmd = [
        "ffmpeg", "-y", "-i", os.path.abspath(video_path),
        "-vf", f"subtitles={cap_name}",
        "-c:a", "copy", os.path.abspath(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, cwd=cap_dir)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore")[-2500:] if e.stderr else "(stderr yok)"
        raise RuntimeError(f"ffmpeg altyazı yakma hatası (exit {e.returncode}):\n{err}") from e
    return out_path
