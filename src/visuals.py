"""
Video arka planı için görsel kaynağı sağlar:
1) Pexels/Pixabay API anahtarı tanımlıysa, konuyla ilgili gerçek stok video/foto indirir.
   Tam konu bulunamazsa, genel/nötr yedek terimlerle (nature, abstract, city vb.) tekrar
   dener, böylece neredeyse her zaman gerçek bir görsel/video bulunur.
2) Hiçbiri bulunamazsa, basit renkli gradyan + yumuşak hareket (Ken Burns efekti) ile
   otomatik üretilmiş arka plan kullanılır. Bu tamamen offline ve ücretsiz çalışır.
"""
import os
import random
import requests
from PIL import Image, ImageDraw, ImageFilter

from . import config

GRADIENT_PALETTES = [
    [(255, 94, 98), (255, 195, 113)],
    [(30, 60, 114), (42, 82, 152)],
    [(69, 179, 157), (63, 55, 201)],
    [(247, 151, 30), (255, 210, 0)],
    [(131, 58, 180), (253, 29, 129)],
    [(17, 153, 142), (56, 239, 125)],
]

# Tam konu için sonuç bulunamazsa denenecek genel/nötr yedek terimler.
# Stok kütüphanelerinde her zaman bol miktarda sonuç veren, güvenli kelimeler.
FALLBACK_KEYWORDS = [
    "abstract background", "nature", "technology", "city lights",
    "ocean waves", "forest", "sky clouds", "galaxy stars",
]

# Çocuk bölümleri için canlı, renkli, çocuk dostu görsel arama terimleri.
KIDS_KEYWORDS = [
    "cute cartoon animals", "colorful kids background", "children learning shapes",
    "cartoon jungle animals", "happy kids playing", "colorful balloons",
    "friendly cartoon animals", "kids bedtime stars", "rainbow colors kids",
    "cartoon farm animals", "playful puppy cartoon", "cute baby animals",
]


def _make_gradient_image(size, path):
    w, h = size
    top, bottom = random.choice(GRADIENT_PALETTES)
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / h
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    img = img.filter(ImageFilter.GaussianBlur(2))
    img.save(path)
    return path


def _search_pexels_video(query: str, out_path: str) -> str | None:
    if not config.PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": config.PEXELS_API_KEY},
            params={"query": query, "orientation": "portrait", "per_page": 25},
            timeout=20,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            print(f"[visuals] Pexels video: '{query}' için sonuç bulunamadı.", flush=True)
            return None
        video = random.choice(videos)
        files = sorted(video["video_files"], key=lambda f: f.get("width", 0))
        # çok büyük dosyaları indirmemek için orta-alt kaliteyi tercih et
        link = files[max(0, len(files) // 3)]["link"]
        data = requests.get(link, timeout=60)
        with open(out_path, "wb") as f:
            f.write(data.content)
        print(f"[visuals] Pexels video bulundu: '{query}' ({len(videos)} sonuçtan biri seçildi)", flush=True)
        return out_path
    except Exception as e:
        print(f"[visuals] Pexels video araması başarısız: {e}", flush=True)
        return None


def _search_pexels_photo(query: str, out_path: str) -> str | None:
    if not config.PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": config.PEXELS_API_KEY},
            params={"query": query, "orientation": "portrait", "per_page": 25},
            timeout=20,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            print(f"[visuals] Pexels foto: '{query}' için sonuç bulunamadı.", flush=True)
            return None
        photo = random.choice(photos)
        link = photo["src"]["large2x"]
        data = requests.get(link, timeout=60)
        with open(out_path, "wb") as f:
            f.write(data.content)
        print(f"[visuals] Pexels foto bulundu: '{query}' ({len(photos)} sonuçtan biri seçildi)", flush=True)
        return out_path
    except Exception as e:
        print(f"[visuals] Pexels foto araması başarısız: {e}", flush=True)
        return None


def _search_pixabay_video(query: str, out_path: str) -> str | None:
    if not config.PIXABAY_API_KEY:
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": config.PIXABAY_API_KEY, "q": query, "per_page": 25},
            timeout=20,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits)
        link = hit["videos"]["medium"]["url"]
        data = requests.get(link, timeout=60)
        with open(out_path, "wb") as f:
            f.write(data.content)
        print(f"[visuals] Pixabay video bulundu: '{query}'", flush=True)
        return out_path
    except Exception as e:
        print(f"[visuals] Pixabay video araması başarısız: {e}", flush=True)
        return None


def _search_pixabay_image(query: str, out_path: str) -> str | None:
    if not config.PIXABAY_API_KEY:
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={"key": config.PIXABAY_API_KEY, "q": query, "image_type": "photo", "per_page": 25},
            timeout=20,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits)
        data = requests.get(hit["largeImageURL"], timeout=60)
        with open(out_path, "wb") as f:
            f.write(data.content)
        print(f"[visuals] Pixabay foto bulundu: '{query}'", flush=True)
        return out_path
    except Exception as e:
        print(f"[visuals] Pixabay foto araması başarısız: {e}", flush=True)
        return None


def _try_all_sources(query: str, work_dir: str, index: int) -> dict | None:
    video_path = os.path.join(work_dir, f"bg_video_{index}.mp4")
    if _search_pexels_video(query, video_path):
        return {"type": "video", "path": video_path}
    if _search_pixabay_video(query, video_path):
        return {"type": "video", "path": video_path}

    image_path = os.path.join(work_dir, f"bg_image_{index}.jpg")
    if _search_pexels_photo(query, image_path):
        return {"type": "image", "path": image_path}
    if _search_pixabay_image(query, image_path):
        return {"type": "image", "path": image_path}

    return None


def get_background(topic_keyword: str, size, work_dir: str, index: int = 0) -> dict:
    """
    Returns {"type": "video"|"image", "path": str}
    Önce tam konuyu dener, bulamazsa genel/nötr yedek terimlerle rastgele
    sırayla dener, o da olmazsa otomatik gradyan üretir.
    `index`, aynı klasörde birden fazla sahne indirilirken dosya adlarının
    çakışmaması için kullanılır.
    """
    os.makedirs(work_dir, exist_ok=True)

    result = _try_all_sources(topic_keyword, work_dir, index)
    if result:
        return result

    fallback_terms = FALLBACK_KEYWORDS.copy()
    random.shuffle(fallback_terms)
    for term in fallback_terms:
        result = _try_all_sources(term, work_dir, index)
        if result:
            return result

    print(f"[visuals] Sahne {index}: hiçbir stok kaynaktan sonuç bulunamadı, otomatik gradyan kullanılıyor.", flush=True)
    gradient_path = os.path.join(work_dir, f"bg_gradient_{index}.jpg")
    _make_gradient_image(size, gradient_path)
    return {"type": "image", "path": gradient_path}
