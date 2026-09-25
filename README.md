# YouTube Video Üretici (Shorts + Uzun Form) — GitHub Actions ile Tamamen Ücretsiz

Bu proje, GitHub Actions üzerinde çalışarak otomatik YouTube Shorts (45-55 sn) veya
10 dakikalık eğitici içerik (çocuklar için basitleştirilmiş anlatım dahil) üretir.
Sesler Microsoft'un ücretsiz nöral (insana yakın) sesleridir. Altyazı Türkçe/İngilizce
seçilebilir. Tek çalıştırmada birden fazla video üretebilirsiniz.

## Bu araç neyi gerçekten yapar, neyi yapamaz?

**Yapar:**
- İnsana yakın, doğal tonlamalı seslendirme (edge-tts / Microsoft nöral sesler), tamamen ücretsiz.
- Otomatik, kelime bazlı senkronize altyazı (Türkçe veya İngilizce, sesten bağımsız seçilebilir).
- 45-55 saniyelik dikey Shorts formatı, otomatik süre ayarı.
- 10 dakikalık uzun form "anlatılı eğitici video" (çocuklara uygun basit dil seçeneğiyle).
- **1-5 yaş çocuklar için özel "bölüm" modu** (`audience: kids`): "Sunucu" ve "Hayvan Arkadaş" adlı
  iki farklı sesin (edge-tts'in iki farklı nöral sesi) konuştuğu, hayvan tanıtımı + renk/şekil/sayı
  öğretimi + eğlenceli hareket oyunu + iyi geceler kapanışından oluşan, **en az 10 dakikalık**
  bölümler otomatik üretir. Süre alt sınırına ulaşılana kadar segment eklenir (üst sınır yoktur).
- Video birden fazla farklı sahneye (her biri ayrı stok görsel/video) bölünür — tek sabit resim değil.
- Farklı konu havuzundan / isteğe bağlı konudan her seferinde özgün senaryo.
- Tek çalıştırmada birden fazla video (batch) üretimi, ZIP olarak indirilebilir.

**Yapamaz / sınırlıdır (dürüst olmak isterim):**
- Bu, Pixar tarzı gerçek karakter animasyonu (ağız senkronizasyonu, çizilmiş karakterler)
  üretmez. Arka plan; ya gerçek stok video/fotoğraf (Pexels/Pixabay'dan, ücretsiz API
  anahtarıyla) ya da otomatik oluşturulan hareketli gradyan/Ken Burns efektidir.
- GitHub kendisi bu programı 7/24 "barındırmaz". Video üretimi, siz **Actions**
  sekmesinden butona bastığınızda birkaç dakika çalışır, videoyu üretir ve size
  indirilebilir bir ZIP (artifact) olarak sunar.
- GitHub Actions'ın ücretsiz süresi sınırlıdır (public repo'larda pratikte çok geniş,
  private repo'da aylık ~2000 dakika). Uzun/çok sayıda video üretimi bu süreyi tüketebilir.

## Kurulum (5 dakika)

1. Bu repoyu kendi GitHub hesabına **fork'la** ya da bu klasörü kendi yeni bir
   repona yükle.
2. (Opsiyonel ama önerilir) Ücretsiz API anahtarları al:
   - **Pexels**: https://www.pexels.com/api/ → ücretsiz hesap, anında key.
   - **Pixabay**: https://pixabay.com/api/docs/ → ücretsiz hesap, anında key.
   - **Groq** (isteğe bağlı, her videoda tamamen özgün senaryo için önerilir):
     https://console.groq.com/keys → ücretsiz katman.
   - Bu anahtarlar olmadan da sistem çalışır: dahili konu/bilgi veritabanından
     ve otomatik gradyan arka planlardan video üretir.
3. Reponda **Settings → Secrets and variables → Actions → New repository secret**
   yoluyla şu isimlerle ekle (istediğini atlayabilirsin):
   - `PEXELS_API_KEY`
   - `PIXABAY_API_KEY`
   - `GROQ_API_KEY`
4. **Actions** sekmesine git → "Video Üret" workflow'unu seç → **Run workflow**.
5. Formu doldur:
   - `topics`: örn. `uzay, antik Mısır tarihi` (boş bırakırsan rastgele konular)
   - `lang`: `tr` veya `en`
   - `subtitle_lang`: `tr` veya `en` (sesten farklı olabilir)
   - `audience`: `general` veya `kids`
   - `video_type`: `short` (45-55sn) veya `long` (10dk)
   - `count`: kaç video üretilsin
6. Çalışma bitince (Shorts için ~2-5 dk, 10 dakikalık video için daha uzun) sayfanın
   altındaki **Artifacts** bölümünden `uretilen-videolar` ZIP'ini indir.

## Yerelde (kendi bilgisayarında) çalıştırmak istersen

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg fonts-dejavu-core   # Mac: brew install ffmpeg

export PEXELS_API_KEY=...     # opsiyonel
export PIXABAY_API_KEY=...    # opsiyonel
export GROQ_API_KEY=...       # opsiyonel

python -m src.main --topics "uzay,hayvanlar" --lang tr --subtitle-lang en \
    --audience general --video-type short --count 2
```

**Çocuk bölümü üretmek için** (en az 10 dakika, iki karakterli diyalog):

```bash
python -m src.main --lang tr --subtitle-lang tr --audience kids --count 1
```

`--audience kids` seçildiğinde `--topics` ve `--video-type` yok sayılır; sistem
otomatik olarak hayvan tanıtımı + öğrenme + oyun + iyi geceler bölümlerinden oluşan
özgün bir senaryo kurar ve en az 10 dakikaya ulaşana kadar segment ekler.

Videolar `output/` klasörüne kaydedilir.

## Geliştirme fikirleri (istersen ekleyebiliriz)

- Arka plan müziği (telifsiz müzik kütüphanesi entegrasyonu).
- Çoklu sahne / kesme efektleri (her cümle için farklı görsel).
- YouTube'a otomatik yükleme (YouTube Data API ile, kendi OAuth anahtarınla).
- Gerçek 2D karakter animasyonu (Rive/Lottie tabanlı basit karakterlerle).
