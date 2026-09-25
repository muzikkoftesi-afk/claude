"""
Video senaryosu (konuşma metni) üretir.
- GROQ_API_KEY tanımlıysa: Groq'un ücretsiz katmanındaki bir LLM ile her seferinde
  özgün, farklı bir senaryo üretilir (gerçekten "hep farklı video" için önerilir).
- Tanımlı değilse: config/topics_bank.json içindeki gerçek/bilgi havuzundan
  DAHA ÖNCE KULLANILMAMIŞ bir konu seçilir (bkz. src/history.py), her video için
  özgün bir başlık üretir. Havuz tükenince otomatik sıfırlanır.
"""
import json
import random
import requests

from . import config
from . import history


INTROS_SHORT = [
    "Bunu biliyor muydun?",
    "İşte seni şaşırtacak bir gerçek.",
    "Az kişinin bildiği bir bilgi geliyor.",
    "Şimdi öğrendiğine sevineceksin.",
]

OUTROS_SHORT = [
    "Beğendiysen takip etmeyi unutma!",
    "Daha fazlası için takipte kal.",
    "Sen bunu biliyor muydun, yorumlarda söyle!",
]


def _load_bank():
    with open(config.TOPICS_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_bank(bank):
    entries = []
    for category, items in bank.items():
        for item in items:
            entries.append({"category": category, "title": item["title"], "fact": item["fact"]})
    return entries


def _pick_unused_entry(entries):
    used = history.load_used()
    unused = [e for e in entries if e["title"] not in used]
    if not unused:
        print("[script_writer] Havuzdaki tüm konular en az bir kez kullanıldı, "
              "geçmiş sıfırlanıp yeniden başlanıyor.", flush=True)
        history.save_used(set())
        unused = entries
    chosen = random.choice(unused)
    history.mark_used(chosen["title"])
    return chosen


def _pick_primary(bank, entries, topic_category):
    if topic_category and topic_category in bank:
        cat_entries = [e for e in entries if e["category"] == topic_category]
        return _pick_unused_entry(cat_entries or entries)
    return _pick_unused_entry(entries)


def _offline_short_script(topic_category: str | None, lang: str, audience: str) -> tuple[str, str]:
    bank = _load_bank()
    entries = _flatten_bank(bank)
    primary = _pick_primary(bank, entries, topic_category)

    same_category_facts = [it["fact"] for it in bank[primary["category"]] if it["fact"] != primary["fact"]]
    supporting = random.sample(same_category_facts, k=min(2, len(same_category_facts)))

    intro = random.choice(INTROS_SHORT)
    outro = random.choice(OUTROS_SHORT)
    body = " ".join([primary["fact"]] + supporting)
    script = f"{intro} {body} {outro}"

    if audience == "kids":
        script = script.replace(".", "!")

    title = primary["title"]
    if lang == "en":
        script = _translate(script, "tr", "en")
        title = _translate(title, "tr", "en")
    return title, script


def _offline_long_script(topic_category: str | None, lang: str) -> tuple[str, str]:
    bank = _load_bank()
    entries = _flatten_bank(bank)
    primary = _pick_primary(bank, entries, topic_category)

    category = primary["category"]
    facts = [it["fact"] for it in bank[category]]
    random.shuffle(facts)
    facts = [primary["fact"]] + [f for f in facts if f != primary["fact"]]

    chunks = []
    for i, fact in enumerate(facts):
        chunks.append(f"Şimdi {i+1}. bilgimize geçiyoruz. {fact} Bunun ne kadar ilginç olduğunu düşünsene!")
    script = " ".join(chunks)
    while len(script.split()) < config.LONG_TARGET_SEC * config.WORDS_PER_SECOND:
        extra = random.choice(facts)
        script += f" Bir bilgi daha: {extra} Harika değil mi?"

    title = primary["title"]
    if lang == "en":
        script = _translate(script, "tr", "en")
        title = _translate(title, "tr", "en")
    return title, script


def _translate(text: str, src: str, dst: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source=src, target=dst).translate(text)
    except Exception:
        return text  # çeviri başarısız olursa orijinali döndür


def _groq_script(topic: str, lang: str, audience: str, video_type: str) -> tuple[str, str]:
    target_words = int((config.SHORT_MAX_SEC if video_type == "short" else config.LONG_TARGET_SEC)
                        * config.WORDS_PER_SECOND)
    audience_note = "5-9 yaş arası çocuklar için çok basit, eğlenceli ve öğretici" if audience == "kids" \
        else "genel bir YouTube kitlesi için ilgi çekici"
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"

    prompt = (
        f"'{topic}' konusu hakkında {lang_name} dilinde, {audience_note} bir YouTube "
        f"{'Shorts' if video_type=='short' else 'uzun video'} anlatım metni yaz. "
        f"Sadece anlatıcının sesli okuyacağı düz metni ver, başlık, yönerge, emoji veya "
        f"parantez içi açıklama ekleme. Yaklaşık {target_words} kelime uzunluğunda olsun. "
        f"Metin akıcı, meraklı bir ton ile başlasın ve izleyiciyi harekete geçiren kısa bir "
        f"kapanışla bitsin."
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
            },
            timeout=60,
        )
        if not resp.ok:
            print(f"[script_writer] Groq hata gövdesi: {resp.status_code} {resp.text[:500]}", flush=True)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return topic, text
    except Exception as e:
        print(f"[script_writer] Groq isteği başarısız, offline moda düşülüyor: {e}")
        return None


def generate_script(topic: str | None, lang: str, audience: str, video_type: str) -> tuple[str, str]:
    """
    Returns (title, script_text)
    topic: kullanıcının verdiği serbest konu metni ya da None (rastgele, geçmişte
           kullanılmamış bir konu otomatik seçilir) ya da topics_bank.json
           içindeki bir kategori adı (örn. 'uzay')
    lang: 'tr' | 'en'
    audience: 'general' | 'kids'
    video_type: 'short' | 'long'
    """
    if config.GROQ_API_KEY and topic:
        result = _groq_script(topic, lang, audience, video_type)
        if result:
            return result

    if video_type == "short":
        return _offline_short_script(topic, lang, audience)
    return _offline_long_script(topic, lang)
