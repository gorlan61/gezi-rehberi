"""
BIP210 - Final Projesi: YZ Destekli Gezi Rehberi
Otomasyon Motoru (otomasyon.py)

Strapi v5 uyumlu | Paralel görsel indirme | Google News RSS | Groq LLaMA zenginleştirme
"""

import requests
import os
import time
import json
import concurrent.futures
from deep_translator import GoogleTranslator
import feedparser

# ══════════════════════════════════════════════
#  BURAYA KENDİ BİLGİLERİNİ YAZ
# ══════════════════════════════════════════════
STRAPI_URL   = "http://localhost:1337"
STRAPI_TOKEN = "be35cbadfdf50593069c51bd4faa436f59ca0d33ff1a53d8899b3d48b178e3367f42bb86827bd6f06629fd2e8121c22670aa32badf479ac0632fc1d2655ddf3fcdd486d08b25bfd0ea9f3cbf400e434db38300141eaf023ae50718a54a2f75646c376c4d9fd8f5ab0d0644a20f6de5d86c4c50778c9de510699cd964d163bc74"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ══════════════════════════════════════════════

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=800&height=600&nologo=true&seed={seed}"
GORSEL_KLASOR    = "gezi_gorseller"
GROQ_MODEL       = "llama-3.3-70b-versatile"
GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"

# ──────────────────────────────────────────────
# VERİLER
# ──────────────────────────────────────────────
SEHIRLER = [
    {"ad": "Trabzon",  "ulke": "Türkiye", "kisa_bilgi": "Karadeniz'in incisi, tarihi ve doğal güzellikleriyle ünlü şehir."},
    {"ad": "İstanbul", "ulke": "Türkiye", "kisa_bilgi": "İki kıtayı birleştiren, tarihi ve kültürel zenginlikleriyle dünyaca ünlü metropol."},
]

MEKANLAR = [
    {"sehir_adi": "Trabzon",  "mekan_adi": "Ayasofya Müzesi",  "aciklama_tr": "13. yüzyılda inşa edilen, Bizans dönemine ait freskolarıyla ünlü tarihi kilise ve müze.",                       "puan": 5, "gorsel_prompt": "Trabzon Ayasofya Museum Byzantine church Turkey"},
    {"sehir_adi": "Trabzon",  "mekan_adi": "Sümela Manastırı", "aciklama_tr": "Karadeniz dağlarında kayalara oyulmuş, MS 386 yılına dayanan efsanevi Rum Ortodoks manastırı.",                  "puan": 5, "gorsel_prompt": "Sumela Monastery cliff Trabzon Turkey orthodox scenic"},
    {"sehir_adi": "Trabzon",  "mekan_adi": "Uzungöl",          "aciklama_tr": "Yeşil dağlar arasında saklı, sisli sabahlarıyla büyüleyen doğal göl ve köy.",                                    "puan": 5, "gorsel_prompt": "Uzungol lake Trabzon Turkey green mountains misty"},
    {"sehir_adi": "Trabzon",  "mekan_adi": "Atatürk Köşkü",   "aciklama_tr": "1890 yılında inşa edilmiş, Atatürk'ün ziyaret ettiği tarihi beyaz köşk ve müze.",                                 "puan": 4, "gorsel_prompt": "Ataturk Kosku Trabzon white mansion museum Turkey"},
    {"sehir_adi": "Trabzon",  "mekan_adi": "Boztepe",          "aciklama_tr": "Şehre ve Karadeniz'e hakim, gün batımı manzarasının eşsiz olduğu seyir tepesi.",                                  "puan": 5, "gorsel_prompt": "Boztepe Trabzon Black Sea sunset panoramic Turkey"},
    {"sehir_adi": "İstanbul", "mekan_adi": "Ayasofya",         "aciklama_tr": "537 yılında inşa edilmiş, dünya mimarisinin başyapıtı olan eski Bizans bazilikası.",                               "puan": 5, "gorsel_prompt": "Hagia Sophia Istanbul mosque architecture landmark"},
    {"sehir_adi": "İstanbul", "mekan_adi": "Topkapı Sarayı",   "aciklama_tr": "Osmanlı İmparatorluğu'nun yönetim merkezi, tarihi eserler ve hazinelerle dolu saray müzesi.",                     "puan": 5, "gorsel_prompt": "Topkapi Palace Istanbul Ottoman historical courtyard"},
    {"sehir_adi": "İstanbul", "mekan_adi": "Kapalıçarşı",      "aciklama_tr": "1461'de kurulan, 4.000'den fazla dükkanıyla dünyanın en eski ve en büyük kapalı çarşısı.",                        "puan": 4, "gorsel_prompt": "Grand Bazaar Istanbul historic covered market colorful"},
]

# ──────────────────────────────────────────────
# YARDIMCI
# ──────────────────────────────────────────────
def auth_headers():
    return {"Authorization": f"Bearer {STRAPI_TOKEN}", "Content-Type": "application/json"}

def metni_ingilizceye_cevir(metin_tr):
    try:
        return GoogleTranslator(source="tr", target="en").translate(metin_tr)
    except Exception as e:
        print(f"  ⚠️  Çeviri hatası: {e}")
        return metin_tr

# ──────────────────────────────────────────────
# YENİ ADIM A: GOOGLE NEWS RSS
# ──────────────────────────────────────────────
def google_news_al(sehir_adi, mekan_adi, max_haber=3):
    """
    Google News RSS üzerinden şehir ve mekanla ilgili
    güncel haber başlıklarını çeker.
    """
    query = f"{sehir_adi} {mekan_adi} turizm"
    url   = (
        f"https://news.google.com/rss/search"
        f"?q={requests.utils.quote(query)}"
        f"&hl=tr&gl=TR&ceid=TR:tr"
    )
    try:
        feed    = feedparser.parse(url)
        basliklar = []
        for entry in feed.entries[:max_haber]:
            baslik = entry.get("title", "").split(" - ")[0].strip()  # Kaynak adını kaldır
            if baslik:
                basliklar.append(baslik)
        if basliklar:
            print(f"  📰 {len(basliklar)} güncel haber bulundu.")
        else:
            print(f"  📰 Haber bulunamadı, standart açıklama kullanılacak.")
        return basliklar
    except Exception as e:
        print(f"  ⚠️  Google News hatası: {e}")
        return []

# ──────────────────────────────────────────────
# YENİ ADIM B: GROQ LLaMA ZENGİNLEŞTİRME
# ──────────────────────────────────────────────
def groq_ile_zenginlestir(mekan_adi, sehir_adi, aciklama_tr, haber_basliklar):
    """
    Mevcut açıklama + Google News başlıklarını Groq LLaMA'ya göndererek
    zenginleştirilmiş, güncel ve bilgilendirici bir Türkçe açıklama üretir.
    """
    if not haber_basliklar:
        # Haber yoksa sadece mevcut açıklamayı düzelt/güzelleştir
        prompt = f"""
Sen bir gezi rehberi içerik yazarısın. Aşağıdaki mekan açıklamasını daha akıcı, 
bilgilendirici ve ziyaretçileri cezbedici hale getir.

Mekan: {mekan_adi} ({sehir_adi})
Mevcut açıklama: {aciklama_tr}

Kurallar:
- Maksimum 3 cümle yaz
- Türkçe yaz
- Sadece açıklamayı yaz, başka hiçbir şey ekleme
"""
    else:
        haberler_str = "\n".join([f"- {h}" for h in haber_basliklar])
        prompt = f"""
Sen bir gezi rehberi içerik yazarısın. Aşağıdaki mekan açıklamasını, 
güncel haberlerden elde ettiğin bilgileri de harmanlayarak zenginleştir.

Mekan: {mekan_adi} ({sehir_adi})
Mevcut açıklama: {aciklama_tr}

Güncel Google News başlıkları:
{haberler_str}

Kurallar:
- Maksimum 3-4 cümle yaz
- Güncel haberlerdeki önemli bilgileri doğal bir şekilde entegre et
- Türkçe yaz, turistik ve bilgilendirici bir ton kullan
- Sadece açıklamayı yaz, başka hiçbir şey ekleme
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        zengin_aciklama = r.json()["choices"][0]["message"]["content"].strip()
        print(f"  🤖 Groq zenginleştirme ✅ ({len(zengin_aciklama)} karakter)")
        return zengin_aciklama
    except Exception as e:
        print(f"  ⚠️  Groq hatası: {e}. Orijinal açıklama kullanılıyor.")
        return aciklama_tr

# ──────────────────────────────────────────────
# ADIM 1: GÖRSELLER — paralel indir
# ──────────────────────────────────────────────
def gorsel_indir_tek(args):
    idx, mekan = args
    os.makedirs(GORSEL_KLASOR, exist_ok=True)
    dosya_adi  = f"mekan_{idx}_{mekan['mekan_adi'].replace(' ', '_').lower()}.jpg"
    dosya_yolu = os.path.join(GORSEL_KLASOR, dosya_adi)

    if os.path.exists(dosya_yolu) and os.path.getsize(dosya_yolu) > 1000:
        print(f"  ♻️  [{idx}] Görsel önbellekten: {dosya_adi}")
        return idx, dosya_yolu

    try:
        seed = abs(hash(mekan["gorsel_prompt"])) % 9999
        url  = POLLINATIONS_URL.format(
            prompt=requests.utils.quote(mekan["gorsel_prompt"]), seed=seed)
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(dosya_yolu, "wb") as f:
                f.write(r.content)
            print(f"  🎨 [{idx}] Pollinations ✅ {mekan['mekan_adi']}")
            return idx, dosya_yolu
        print(f"  ⚠️  [{idx}] Pollinations {r.status_code}, fallback...")
    except Exception as e:
        print(f"  ⚠️  [{idx}] Pollinations hata ({type(e).__name__}), fallback...")

    try:
        seed2 = abs(hash(mekan["gorsel_prompt"])) % 1000
        r2 = requests.get(f"https://picsum.photos/seed/{seed2}/800/600",
                          timeout=20, allow_redirects=True)
        r2.raise_for_status()
        with open(dosya_yolu, "wb") as f:
            f.write(r2.content)
        print(f"  🔄 [{idx}] Picsum fallback ✅ {mekan['mekan_adi']}")
        return idx, dosya_yolu
    except Exception as e2:
        print(f"  ❌ [{idx}] Görsel tamamen başarısız: {e2}")
        return idx, None

def tum_gorselleri_paralel_indir(mekanlar):
    print("\n🖼️  Görseller paralel indiriliyor...")
    gorsel_haritasi = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        sonuclar = executor.map(gorsel_indir_tek, enumerate(mekanlar, 1))
        for idx, yol in sonuclar:
            gorsel_haritasi[idx] = yol
    print("✅ Tüm görsel indirmeleri tamamlandı.\n")
    return gorsel_haritasi

# ──────────────────────────────────────────────
# ADIM 2: GÖRSEL YÜKLE
# ──────────────────────────────────────────────
def gorsel_yukle(dosya_yolu):
    headers = {"Authorization": f"Bearer {STRAPI_TOKEN}"}
    try:
        with open(dosya_yolu, "rb") as f:
            files    = {"files": (os.path.basename(dosya_yolu), f, "image/jpeg")}
            response = requests.post(f"{STRAPI_URL}/api/upload",
                                     headers=headers, files=files, timeout=30)
            response.raise_for_status()
            gorsel_id = response.json()[0]["id"]
            print(f"  📤 Görsel yüklendi. ID: {gorsel_id}")
            return gorsel_id
    except Exception as e:
        print(f"  ⚠️  Görsel yükleme hatası: {e}")
        return None

# ──────────────────────────────────────────────
# ADIM 3: ŞEHİR
# ──────────────────────────────────────────────
def sehir_olustur_veya_bul(sehir):
    try:
        r = requests.get(
            f"{STRAPI_URL}/api/cities?filters[ad][$eq]={requests.utils.quote(sehir['ad'])}",
            headers=auth_headers(), timeout=10)
        r.raise_for_status()
        mevcut = r.json().get("data", [])
        if mevcut:
            sid    = mevcut[0]["id"]
            doc_id = mevcut[0].get("documentId", str(sid))
            print(f"  ℹ️  Şehir mevcut: {sehir['ad']} (ID: {sid})")
            return sid, doc_id
    except Exception as e:
        print(f"  ⚠️  Şehir sorgu hatası: {e}")

    payload = {"data": {"ad": sehir["ad"], "ulke": sehir["ulke"],
                        "kisa_bilgi": sehir["kisa_bilgi"], "locale": "tr"}}
    try:
        r = requests.post(f"{STRAPI_URL}/api/cities",
                          headers=auth_headers(), json=payload, timeout=10)
        r.raise_for_status()
        data   = r.json()["data"]
        sid    = data["id"]
        doc_id = data.get("documentId", str(sid))
        print(f"  ✅ Şehir oluşturuldu: {sehir['ad']} (ID: {sid})")

        aciklama_en = metni_ingilizceye_cevir(sehir["kisa_bilgi"])
        lok_payload = {"data": {"ad": sehir["ad"], "ulke": sehir["ulke"],
                                "kisa_bilgi": aciklama_en}}
        lok_r = requests.put(
            f"{STRAPI_URL}/api/cities/{doc_id}?locale=en",
            headers=auth_headers(), json=lok_payload, timeout=10)
        if lok_r.status_code in [200, 201]:
            print(f"  🌐 Şehir EN lokalizasyon eklendi.")
        return sid, doc_id
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ Şehir oluşturma hatası: {e}\n     {e.response.text[:200]}")
        return None, None

# ──────────────────────────────────────────────
# ADIM 4: MEKAN (zenginleştirilmiş açıklama ile)
# ──────────────────────────────────────────────
def mekan_olustur(mekan, sehir_id, gorsel_id, aciklama_tr_zengin, aciklama_en):
    # Mükerrer kontrol
    try:
        r = requests.get(
            f"{STRAPI_URL}/api/places"
            f"?filters[mekan_adi][$eq]={requests.utils.quote(mekan['mekan_adi'])}&locale=tr",
            headers=auth_headers(), timeout=10)
        if r.json().get("data"):
            print(f"  ℹ️  Mekan mevcut, atlanıyor: {mekan['mekan_adi']}")
            return True
    except Exception:
        pass

    puan_int = int(round(mekan["puan"]))
    payload  = {
        "data": {
            "mekan_adi": mekan["mekan_adi"],
            "aciklama":  aciklama_tr_zengin,   # ← Groq zenginleştirmeli açıklama
            "puan":      puan_int,
            "city":      sehir_id,
            "locale":    "tr"
        }
    }
    if gorsel_id:
        payload["data"]["kapak_resmi"] = gorsel_id

    try:
        r = requests.post(f"{STRAPI_URL}/api/places",
                          headers=auth_headers(), json=payload, timeout=15)
        r.raise_for_status()
        data   = r.json()["data"]
        mid    = data["id"]
        doc_id = data.get("documentId", str(mid))
        print(f"  ✅ Mekan oluşturuldu: {mekan['mekan_adi']} (ID: {mid})")

        # EN lokalizasyon
        lok_payload = {
            "data": {
                "mekan_adi": mekan["mekan_adi"],
                "aciklama":  aciklama_en,
                "puan":      puan_int,
                "city":      sehir_id
            }
        }
        if gorsel_id:
            lok_payload["data"]["kapak_resmi"] = gorsel_id

        lok_r = requests.put(
            f"{STRAPI_URL}/api/places/{doc_id}?locale=en",
            headers=auth_headers(), json=lok_payload, timeout=10)
        if lok_r.status_code in [200, 201]:
            print(f"  🌐 Mekan EN lokalizasyon eklendi.")
        else:
            print(f"  ⚠️  Mekan EN lok. yanıtı: {lok_r.status_code} {lok_r.text[:120]}")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"  ❌ Mekan oluşturma hatası: {e}\n     {e.response.text[:300]}")
        return False

# ──────────────────────────────────────────────
# ANA DÖNGÜ
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  BIP210 | YZ Destekli Gezi Rehberi - Otomasyon")
    print("  Google News RSS + Groq LLaMA Zenginleştirme")
    print("=" * 60)

    # Bağlantı kontrolü
    print("\n🔐 Token kontrol ediliyor...")
    try:
        test = requests.get(f"{STRAPI_URL}/api/cities",
                            headers=auth_headers(), timeout=10)
        test.raise_for_status()
        print("✅ Strapi bağlantısı başarılı.")
    except requests.exceptions.ConnectionError:
        raise SystemExit("❌ Strapi'ye ulaşılamıyor.")
    except requests.exceptions.HTTPError as e:
        raise SystemExit(f"❌ Token geçersiz ({e.response.status_code}).")

    # Groq kontrolü
    print("🤖 Groq API kontrol ediliyor...")
    try:
        test_r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": [{"role": "user", "content": "merhaba"}], "max_tokens": 5},
            timeout=10
        )
        test_r.raise_for_status()
        print("✅ Groq API bağlantısı başarılı.")
    except Exception as e:
        print(f"⚠️  Groq API erişilemiyor: {e}. Zenginleştirme olmadan devam edilecek.")

    # Görselleri paralel indir
    gorsel_haritasi = tum_gorselleri_paralel_indir(MEKANLAR)

    # Şehirleri oluştur
    print("📍 Şehirler işleniyor...")
    sehir_id_haritasi = {}
    for sehir in SEHIRLER:
        sid, _ = sehir_olustur_veya_bul(sehir)
        if sid:
            sehir_id_haritasi[sehir["ad"]] = sid

    # Mekanları işle
    print(f"\n🏛️  {len(MEKANLAR)} mekan işlenecek...\n")
    basarili, basarisiz = 0, 0

    for i, mekan in enumerate(MEKANLAR, 1):
        print(f"[{i}/{len(MEKANLAR)}] ⚙️  {mekan['mekan_adi']}")

        sehir_id = sehir_id_haritasi.get(mekan["sehir_adi"])
        if not sehir_id:
            print(f"  ⚠️  Şehir bulunamadı, atlanıyor.")
            basarisiz += 1
            continue

        # A) Google News'ten güncel haberler çek
        print(f"  📰 Google News taranıyor...")
        haberler = google_news_al(mekan["sehir_adi"], mekan["mekan_adi"])

        # B) Groq ile Türkçe açıklamayı zenginleştir
        print(f"  🤖 Groq ile zenginleştiriliyor...")
        aciklama_tr_zengin = groq_ile_zenginlestir(
            mekan["mekan_adi"], mekan["sehir_adi"],
            mekan["aciklama_tr"], haberler
        )

        # C) Zenginleştirilmiş Türkçeyi İngilizceye çevir
        print(f"  🌐 İngilizceye çevriliyor...")
        aciklama_en = metni_ingilizceye_cevir(aciklama_tr_zengin)

        # D) Görsel yükle
        gorsel_id  = None
        gorsel_yol = gorsel_haritasi.get(i)
        if gorsel_yol:
            gorsel_id = gorsel_yukle(gorsel_yol)

        # E) Strapi'ye kaydet
        if mekan_olustur(mekan, sehir_id, gorsel_id, aciklama_tr_zengin, aciklama_en):
            basarili += 1
        else:
            basarisiz += 1

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"  ✅ Başarılı : {basarili} mekan")
    print(f"  ❌ Başarısız: {basarisiz} mekan")
    print(f"  📁 Görseller: ./{GORSEL_KLASOR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()