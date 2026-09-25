"""
1-5 yaş çocuklar için 'Sunucu' ve 'Hayvan Arkadaş' adlı iki karakterin konuştuğu
eğlenceli/öğretici bölüm senaryoları üretir. Segmentler: karşılama, hayvan tanıtımı,
öğrenme (renkler/şekiller/sayılar), eğlenceli oyun, iyi geceler kapanışı.
Türkçe üretilir; İngilizce istenirse tüm satırlar çevrilir.
"""
import random

from . import config

ANIMALS = [
    ("Fil", "Pöfff pöfff", "Fillerin hortumunda 40 binden fazla kas vardır, hem yemek yer hem su içer hem de arkadaşlarını selamlar!"),
    ("Aslan", "Kükkk kükkk", "Aslanlar günde 20 saate kadar uyuyabilir, tıpkı tembel bir kedi gibi!"),
    ("Zürafa", "Mmmh mmmh", "Zürafaların dili o kadar uzundur ki kendi kulaklarını temizleyebilirler!"),
    ("Penguen", "Vak vak", "Penguenler uçamaz ama suda kuş gibi hızlı yüzebilirler!"),
    ("Tavşan", "Hop hop", "Tavşanların kulakları, onları serin tutmaya da yardımcı olur!"),
    ("Panda", "Hmm hmm", "Pandalar günde neredeyse 12 saat sadece bambu yiyerek geçirir!"),
    ("Kelebek", "Fofofo", "Kelebekler tat alma duyularını ayaklarıyla hissederler!"),
    ("Köpek", "Hav hav", "Köpekler kuyruklarını sallayarak bize ne kadar mutlu olduklarını gösterirler!"),
    ("Kedi", "Miyav miyav", "Kediler mırıldayarak hem mutlu olduklarını gösterir hem de kendilerini iyi hissettirirler!"),
    ("Ayı", "Hoop hoop", "Ayılar kış uykusuna yattıklarında aylarca hiç yemek yemezler!"),
    ("Maymun", "Ii ii aa aa", "Maymunlar ağaçtan ağaca zıplarken kuyruklarını denge için kullanır!"),
    ("Kaplumbağa", "Şşşt şşşt", "Kaplumbağalar evlerini sırtlarında taşırlar, hiç kaybolmazlar!"),
    ("Balina", "Vuuuv vuuuv", "Mavi balinalar, dünyadaki en büyük hayvanlardır, bir otobüsten bile büyüktür!"),
    ("Baykuş", "Huu huu", "Baykuşlar başlarını neredeyse tam tur döndürebilirler!"),
    ("Tilki", "Vaf vaf", "Tilkiler kar altındaki sesleri bile duyabilecek kadar keskin kulaklara sahiptir!"),
]

COLORS = [
    ("kırmızı", "elma gibi"), ("mavi", "gökyüzü gibi"), ("sarı", "güneş gibi"),
    ("yeşil", "çimen gibi"), ("turuncu", "portakal gibi"), ("mor", "üzüm gibi"),
    ("pembe", "çiçek gibi"), ("kahverengi", "toprak gibi"),
]

SHAPES = [
    ("daire", "bir top gibi yuvarlaktır"), ("kare", "dört eşit kenarı vardır"),
    ("üçgen", "üç köşesi vardır"), ("yıldız", "gökyüzünde parlar, uçları vardır"),
    ("kalp", "sevgiyi gösterir"), ("dikdörtgen", "kare gibi ama biraz uzundur"),
]

ACTIVITIES = [
    "Hadi hep birlikte üç kere zıplayalım! Bir, iki, üç, zıpla!",
    "Şimdi kollarımızı açıp kuş gibi uçalım, hazır mısınız?",
    "Haydi ellerimizi çırpalım ve gülelim, hepimiz çok mutluyuz!",
    "Şimdi yavaşça dönelim, bir, iki, üç, dur!",
    "Hadi derin bir nefes alalım ve gülümseyelim!",
    "Şimdi parmaklarımızı sayalım, bir, iki, üç, dört, beş!",
    "Haydi küçük adımlarla yürüyelim, tıpış tıpış tıpış!",
    "Şimdi kocaman bir esneme yapalım, çok yorulduk galiba!",
]

GREETINGS = [
    "Merhaba küçük dostlarım! Bugün çok eğlenceli bir günümüz var!",
    "Selam sevgili arkadaşlar! Sizi burada görmek beni çok mutlu etti!",
    "Merhaba! Bugün birlikte yeni şeyler öğreneceğiz ve çok eğleneceğiz!",
]

OUTROS = [
    "Bugün çok eğlendik değil mi? Şimdi gözlerimizi kapatıp güzel rüyalar görme zamanı. İyi geceler küçük dostum!",
    "Ne güzel bir gündü! Şimdi yorganımıza sarılıp uyuma vakti. Tatlı rüyalar, seni çok seviyoruz!",
    "Bugün öğrendiklerimizi hiç unutmayacağız! Şimdi gözlerimizi yumup dinlenelim. İyi geceler, yarın yine buradayız!",
]


JOKES = [
    "Hihihi, karnım gıdıklandı da kendimi tutamadım!",
    "Vay canına, kendi kuyruğuma bastım, ne komik değil mi?",
    "Hop, az kalsın bir havuca çarpıyordum, hihihi!",
    "Poff, o kadar çok güldüm ki topaç gibi döndüm!",
    "Hi hi hi, burnum gıdıklanıyor, çok komik!",
    "Vay be, kendi gölgemden korkup zıpladım, sonra kendime güldüm!",
    "Hihi, az önce bir kelebekle selamlaştım, o da bana gülümsedi!",
    "Poff, çok komik bir şey oldu, neredeyse kuyruğumu düğümlüyordum!",
]

TRANSITIONS = [
    "Hazır mısınız? Şimdi başka bir arkadaşımızla tanışma vakti geldi!",
    "Haydi, yeni bir maceraya doğru gidelim!",
    "Şimdi sırada çok ama çok eğlenceli bir şey var, hazır mısınız?",
    "Devam edelim mi? Bence hep birlikte edelim!",
    "Hadi bakalım, bir sonraki eğlenceye geçiyoruz!",
]


def _joke_line():
    return _friend_line(random.choice(JOKES))


def _transition_line():
    return _host_line(random.choice(TRANSITIONS))


def _host_line(text):
    return {"role": "host", "text": text}


def _friend_line(text):
    return {"role": "friend", "text": text}


def _animal_segment(animal_name, animal_sound, animal_fact):
    lines = [
        _host_line(f"Bugün size çok özel bir arkadaşımızı tanıtacağım. Merhaba {animal_name}, bize kendinden bahseder misin?"),
        _friend_line(f"Merhaba! Ben bir {animal_name.lower()}. Ben böyle ses çıkarırım: {animal_sound}!"),
        _host_line(f"Vay canına, ne güzel bir ses! Peki senin hakkında ilginç bir şey söyler misin?"),
        _friend_line(f"{animal_fact} İlginç değil mi?"),
    ]
    if random.random() < 0.6:  # eğlence için sık sık küçük bir şaka
        lines.append(_joke_line())
        lines.append(_host_line("Hahaha, çok komiksin! Hepimiz seninle gülüyoruz!"))
    lines.append(_host_line(f"Hep birlikte {animal_name.lower()} gibi ses çıkaralım hadi: {animal_sound}!"))
    return lines


def _color_segment(colors_subset):
    lines = [_host_line("Şimdi birlikte renkleri öğrenelim, hazır mısınız?")]
    for color, comparison in colors_subset:
        lines.append(_friend_line(f"Bu renk {color}, {comparison} bir renk!"))
        lines.append(_host_line(f"Harika! {color.capitalize()} rengi çevrende bulabilir misin?"))
    return lines


def _shape_segment(shapes_subset):
    lines = [_host_line("Şimdi de şekilleri keşfedelim, çok eğlenceli olacak!")]
    for shape, description in shapes_subset:
        lines.append(_friend_line(f"Bu bir {shape}. {description.capitalize()}."))
        lines.append(_host_line(f"Ne kadar güzel bir {shape}! Etrafında bir {shape} görebiliyor musun?"))
    return lines


def _counting_segment():
    lines = [_host_line("Hadi şimdi birlikte sayalım, benimle beraber söyle!")]
    numbers = ["bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on"]
    lines.append(_friend_line(", ".join(numbers) + "! Harika saydık!"))
    lines.append(_host_line("Aferin sana! Sayı saymayı çok iyi öğreniyorsun!"))
    return lines


def _activity_segment():
    activity = random.choice(ACTIVITIES)
    return [
        _host_line("Şimdi biraz hareket etme zamanı, hazır mısınız küçük dostlar?"),
        _friend_line(activity),
        _host_line("Harikaydı! Çok güzel hareket ettiniz, aferin size!"),
    ]


def build_episode(lang: str):
    """Türkçe bir bölüm senaryosu üretir; en az config.KIDS_MIN_SEC hedefine
    ulaşmak için yeterli sayıda segment ekler. lang='en' ise tüm satırlar
    İngilizceye çevrilir. Returns (title, lines) - lines: [{"role","text"}]"""
    lines = [_host_line(random.choice(GREETINGS))]

    animals_pool = random.sample(ANIMALS, k=len(ANIMALS))
    colors_pool = random.sample(COLORS, k=len(COLORS))
    shapes_pool = random.sample(SHAPES, k=len(SHAPES))

    target_words = int((config.KIDS_MIN_SEC + 90) * config.WORDS_PER_SECOND)

    def word_count():
        return sum(len(l["text"].split()) for l in lines)

    animal_i, color_i, shape_i = 0, 0, 0
    segment_cycle = 0
    while word_count() < target_words:
        # sırayla hayvan -> renk -> şekil -> sayma -> aktivite segmenti ekleyip döngüye devam
        name, sound, fact = animals_pool[animal_i % len(animals_pool)]
        lines += _animal_segment(name, sound, fact)
        animal_i += 1

        lines.append(_transition_line())
        lines += _color_segment(colors_pool[color_i % len(colors_pool): color_i % len(colors_pool) + 3] or colors_pool[:3])
        color_i += 3

        lines += _activity_segment()

        if segment_cycle % 2 == 0:
            lines.append(_transition_line())
            lines += _shape_segment(shapes_pool[shape_i % len(shapes_pool): shape_i % len(shapes_pool) + 3] or shapes_pool[:3])
            shape_i += 3
        else:
            lines.append(_transition_line())
            lines += _counting_segment()

        segment_cycle += 1
        if segment_cycle > 12:  # sonsuz döngü koruması
            break

    lines.append(_host_line(random.choice(OUTROS)))

    title_animal = animals_pool[0][0]
    title = f"{title_animal} ile Eğlenceli Öğrenme Zamanı"

    if lang == "en":
        title = _translate_bulk([title], "tr", "en")[0]
        texts = [l["text"] for l in lines]
        translated = _translate_bulk(texts, "tr", "en")
        lines = [{"role": l["role"], "text": t} for l, t in zip(lines, translated)]

    return title, lines


def _translate_bulk(texts, src, dst):
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=src, target=dst)
        return [translator.translate(t) for t in texts]
    except Exception as e:
        print(f"[kids_script] Çeviri başarısız, orijinal metin kullanılıyor: {e}", flush=True)
        return texts
