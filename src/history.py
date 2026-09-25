"""
Hangi konu başlıklarının daha önce kullanıldığını bir JSON dosyasında takip eder.
Bu dosya GitHub Actions workflow'u tarafından her çalıştırma sonunda repoya geri
commit'lenir, böylece bir sonraki çalıştırma nelerin zaten üretildiğini bilir ve
havuz tükenene kadar tekrar üretmez. Havuz tükenince otomatik olarak sıfırlanır.
"""
import json
import os

HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "used_history.json")


def load_used() -> set:
    if not os.path.exists(HISTORY_PATH):
        return set()
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("used_titles", []))
    except Exception as e:
        print(f"[history] Geçmiş dosyası okunamadı, boş başlanıyor: {e}", flush=True)
        return set()


def save_used(used: set):
    try:
        os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"used_titles": sorted(used)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[history] Geçmiş dosyası kaydedilemedi: {e}", flush=True)


def mark_used(title: str):
    used = load_used()
    used.add(title)
    save_used(used)
