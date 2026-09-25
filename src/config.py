import os

# --- Ses (TTS) ayarları ---
# 'general' için birden fazla ses verilirse her videoda rastgele biri seçilir
# (kadın/erkek karışık, doğal çeşitlilik için).
VOICES = {
    "tr": {"general": ["tr-TR-EmelNeural", "tr-TR-AhmetNeural"], "kids": "tr-TR-EmelNeural"},
    "en": {"general": ["en-US-AriaNeural", "en-US-GuyNeural"], "kids": "en-US-AnaNeural"},
}

# --- Çocuk bölümü diyalog sesleri (Sunucu + Hayvan Arkadaş, iki farklı ses) ---
VOICES_DIALOGUE = {
    "tr": {"host": "tr-TR-EmelNeural", "friend": "tr-TR-AhmetNeural"},
    "en": {"host": "en-US-AnaNeural", "friend": "en-US-GuyNeural"},
}

# --- Video boyutları ---
SHORT_SIZE = (1080, 1920)   # dikey - Shorts
LONG_SIZE = (1920, 1080)    # yatay - uzun form içerik

# --- Süre hedefleri ---
SHORT_MIN_SEC, SHORT_MAX_SEC = 45, 55
LONG_TARGET_SEC = 10 * 60
KIDS_MIN_SEC = 10 * 60  # çocuk bölümleri en az 10 dakika olmalı (üst sınır yok)

# Ortalama konuşma hızı (kelime/saniye) - edge-tts normal hız için kaba tahmin
WORDS_PER_SECOND = 2.4

# --- API anahtarları (GitHub Secrets üzerinden environment variable olarak gelir) ---
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
TOPICS_BANK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "topics_bank.json")

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
