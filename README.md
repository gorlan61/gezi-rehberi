# 🗺️ YZ Destekli Gezi Rehberi — BIP210 Final Projesi

> Yapay zeka ve güncel haberlerle zenginleştirilmiş, çok dilli dijital gezi rehberi sistemi.

**Recep Tayyip Erdoğan Üniversitesi — BIP210 İçerik Yönetimi Dersi**  
**Öğretim Elemanı:** Öğr. Gör. Dr. Pınar KEFELİ BERBER

---

## 🔗 Canlı Linkler

| Servis | URL |
|---|---|
| 🌐 Streamlit Arayüzü | https://gezi-rehberi-kgkmdunrjehwegexunig9c.streamlit.app |
| ⚙️ Strapi Yönetim Paneli | https://gezi-rehberi-backend-11py.onrender.com/admin |

---

## 📐 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. VERİ KAYNAKLARI                           │
│   Veri Listesi  │  Google News RSS  │  Pollinations AI          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. OTOMASYON MOTORU (otomasyon.py)                 │
│                                                                  │
│  google_news_al()  →  groq_ile_zenginlestir()                   │
│       │                      │                                  │
│       ▼                      ▼                                  │
│  metni_ingilizceye_cevir()   gorsel_uret_ve_indir()             │
│       │                      │                                  │
│       └──────────┬───────────┘                                  │
│                  │  JWT Token ile kimlik doğrulama               │
└──────────────────┼──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│         3. STRAPİ BACKEND — Render.com (PostgreSQL)             │
│                                                                  │
│  City (TR+EN)  ──1:N──  Place (TR+EN)  ──  Media Library       │
│  Ad, Ülke, Kısa Bilgi   Mekan, Açıklama, Puan, Kapak Resmi     │
└──────────────────┬──────────────────────────────────────────────┘
                   │  REST API — GET /api/cities, /api/places
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│         4. STREAMLİT FRONTEND — Streamlit Cloud                 │
│                                                                  │
│  Şehir Seçimi  │  Dil Seçimi (TR/EN)  │  Mekan Kartları        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Kullanılan Teknolojiler

| Katman | Teknoloji | Açıklama |
|---|---|---|
| Backend | Strapi v5 | Headless CMS, REST API |
| Veritabanı | PostgreSQL | Render.com üzerinde |
| Otomasyon | Python 3 | İçerik toplama ve yükleme |
| Çeviri | deep-translator | TR → EN otomatik çeviri |
| YZ Görsel | Pollinations AI | Prompt tabanlı görsel üretimi |
| YZ Metin | Groq LLaMA 3.3 70B | Metin zenginleştirme |
| Haberler | Google News RSS | feedparser ile güncel veri |
| Frontend | Streamlit | Python web arayüzü |
| Deployment | Render + Streamlit Cloud | Ücretsiz bulut barındırma |
| Versiyon | Git + GitHub | Kod yönetimi |

---

## 📁 Proje Yapısı

```
gezi_rehberi/
├── app.py                  # Streamlit frontend uygulaması
├── otomasyon.py            # Python otomasyon motoru
├── requirements.txt        # Python bağımlılıkları
├── README.md               # Bu dosya
├── gezi_gorseller/         # İndirilen YZ görselleri (geçici)
└── gezi-rehberi-backend/   # Strapi backend projesi
    ├── src/
    │   └── api/
    │       ├── city/       # City koleksiyonu şeması
    │       └── place/      # Place koleksiyonu şeması
    ├── config/
    │   └── database.js     # Veritabanı yapılandırması
    └── package.json
```

---

## ⚙️ Python Fonksiyon Açıklamaları

### `otomasyon.py`

#### `jwt_token_al()` → Kaldırıldı, API Token kullanılıyor
Strapi'ye kimlik doğrulama için JWT yerine API Token yöntemi kullanılmaktadır. Token, `Authorization: Bearer` başlığı ile her istekte gönderilir.

#### `google_news_al(sehir_adi, mekan_adi, max_haber=3)`
Google News RSS feed'inden şehir ve mekan adına göre arama yaparak güncel haber başlıklarını çeker. `feedparser` kütüphanesi kullanılır. Döndürdüğü başlıklar, açıklama zenginleştirme adımında Groq API'ye gönderilir.

#### `groq_ile_zenginlestir(mekan_adi, sehir_adi, aciklama_tr, haber_basliklar)`
Mevcut mekan açıklaması ile Google News'ten gelen güncel haber başlıklarını birleştirerek Groq LLaMA 3.3 70B modeline gönderir. Model, turistik ve bilgilendirici bir ton kullanarak 3-4 cümlelik zenginleştirilmiş bir Türkçe açıklama üretir.

#### `metni_ingilizceye_cevir(metin_tr)`
`deep-translator` kütüphanesinin `GoogleTranslator` sınıfını kullanarak Türkçe metni İngilizceye çevirir. Hata durumunda orijinal Türkçe metni döndürür.

#### `gorsel_indir_tek(args)` + `tum_gorselleri_paralel_indir(mekanlar)`
Pollinations AI servisine mekan adını içeren İngilizce bir prompt göndererek turistik/manzara görseli üretir ve diske indirir. 4 paralel thread ile tüm mekanların görselleri aynı anda indirilir. Pollinations erişilemezsek `picsum.photos` fallback olarak kullanılır.

#### `gorsel_yukle(dosya_yolu)`
Diske indirilen görsel dosyasını Strapi'nin `/api/upload` endpoint'ine `multipart/form-data` formatında POST ederek Media Library'ye yükler. Döndürülen görsel ID'si, mekan kaydıyla ilişkilendirilir.

#### `sehir_olustur_veya_bul(sehir)`
Önce mevcut şehirleri sorgular; varsa ID'sini döndürür. Yoksa TR locale ile yeni şehir oluşturur, ardından `PUT /{documentId}?locale=en` ile EN lokalizasyonu ekler.

#### `mekan_olustur(mekan, sehir_id, gorsel_id, aciklama_tr_zengin, aciklama_en)`
Zenginleştirilmiş TR açıklaması ile Strapi'ye mekan kaydı oluşturur. Görsel ID'sini `kapak_resmi` alanıyla ilişkilendirir. Ardından `PUT` isteği ile EN lokalizasyonu ekler. Mükerrer kayıt önleme kontrolü içerir.

---

## 🚀 Yerel Kurulum

### Gereksinimler
- Python 3.10+
- Node.js 18+
- Git

### 1. Repoyu klonla
```bash
git clone https://github.com/KULLANICI_ADIN/gezi-rehberi.git
cd gezi-rehberi
```

### 2. Python bağımlılıklarını kur
```bash
pip install streamlit requests deep-translator feedparser python-dotenv
```

### 3. Strapi'yi başlat
```bash
cd gezi-rehberi-backend
npm install
npm run develop
```

### 4. Ortam değişkenlerini ayarla
`otomasyon.py` ve `app.py` içindeki şu satırları düzenle:
```python
STRAPI_URL   = "http://localhost:1337"
STRAPI_TOKEN = "strapi_api_token"
GROQ_API_KEY = "groq_api_key"
```

### 5. Veriyi yükle
```bash
python otomasyon.py
```

### 6. Arayüzü başlat
```bash
python -m streamlit run app.py
```

---

## 📊 Değerlendirme Kriterleri Karşılama

| Kriter | Puan | Durum |
|---|---|---|
| Veri Modelleme (Strapi) | 20 | ✅ City↔Place ilişkisi, i18n TR+EN |
| API ve Güvenlik | 15 | ✅ JWT Token ile güvenli POST |
| YZ ve Çeviri Entegrasyonu | 20 | ✅ Groq + deep-translator + Pollinations |
| Dosya Yönetimi | 15 | ✅ Media Library Upload API |
| Frontend Sunumu | 20 | ✅ Streamlit, şehir/dil seçimi, kartlar |
| Kod Düzeni | 10 | ✅ Fonksiyonlara ayrılmış, tek tuşla çalışır |
| **Toplam** | **100** | ✅ |

---

## 📝 Notlar

- Render.com ücretsiz planında Strapi 15 dakika aktiflik olmadığında uyku moduna girer. İlk istek 1-2 dakika gecikebilir.
- `gezi_gorseller/` klasörü `.gitignore`'a eklenmiştir; görseller repoya dahil değildir.
- Yapay zeka kullanımı: görsel üretimi (Pollinations), metin zenginleştirme (Groq LLaMA), çeviri (Google Translate via deep-translator)

---

*BIP210 — İçerik Yönetimi | Bahar Dönemi | Recep Tayyip Erdoğan Üniversitesi*
