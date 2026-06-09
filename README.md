# BIP210 Final Projesi: YZ Destekli Çok Dilli Gezi Rehberi

Bu proje, BIP210 final izlencesine uygun olarak geliştirilmiş uçtan uca çalışan bir dijital gezi rehberi uygulamasıdır. Sistem; resmi turizm kaynaklarından veri toplar, içerikleri yapay zeka desteğiyle zenginleştirir, Türkçe ve İngilizce olarak yayınlar, görselleri kalıcı medya altyapısıyla yönetir ve tüm içeriği modern bir Streamlit arayüzünde kullanıcıya sunar.

Projenin temel teknolojileri `Strapi v5`, `Python`, `Streamlit`, `deep-translator`, `Groq API`, `Pollinations`, `Cloudinary` ve `PostgreSQL/SQLite` bileşenlerinden oluşur. Geliştirme ortamında SQLite ile hızlı çalışma desteklenirken, canlı ortam için Render + PostgreSQL + Cloudinary mimarisi hedeflenmiştir.

## Proje Özeti

| Başlık | Açıklama |
| --- | --- |
| Backend | Strapi v5 üzerinde `City` ve `Place` koleksiyonları, ilişkisel veri modeli ve i18n desteği |
| Otomasyon | Resmi kaynaklardan veri çekme, metin normalizasyonu, YZ zenginleştirme, TR/EN çeviri, medya yükleme ve idempotent senkronizasyon |
| Frontend | Streamlit ile modern, iki dilli, şehir bazlı filtrelenebilir gezi rehberi arayüzü |
| İçerik | 8 şehir, 30 mekan, resmi kaynak manifesti ve kalıcı görsel yedekleri |
| Güvenlik | JWT tabanlı Strapi yazma akışı, frontend için read-only token, gizli bilgilerin env/secrets üzerinden yönetimi |
| Canlılık | Cloudinary medya sağlayıcısı ve fallback manifestleri sayesinde canlı ortamda görsel sürekliliği |

## Mimari Akış

```mermaid
flowchart LR
    A["Resmi Turizm Kaynakları<br/>Kültür Portalı / GoTürkiye / Belediyeler"] --> B["Python Otomasyon<br/>otomasyon.py"]
    B --> C["Kaynak Metin Çıkarımı<br/>Extractor Adapter'ları"]
    B --> D["YZ Metin Zenginleştirme<br/>Groq API"]
    B --> E["TR -> EN Çeviri<br/>deep-translator"]
    B --> F["Görsel Üretimi ve Yedekleme<br/>Pollinations + Resmi Görseller"]
    B --> G["Strapi REST API<br/>JWT Auth + Upload API"]
    G --> H["Strapi CMS<br/>City / Place / Media Library"]
    H --> I["Streamlit Frontend<br/>app.py"]
    I --> J["Kullanıcı<br/>Şehir seçimi + TR/EN içerik"]
```

## Öne Çıkan Özellikler

- `City` ve `Place` koleksiyonları arasında bire-çok ilişki kurulmuştur.
- Strapi i18n desteğiyle Türkçe ve İngilizce içerikler aynı veri modeli içinde yönetilir.
- `sources.json` manifesti üzerinden resmi kaynaklara bağlı, tekrar üretilebilir veri toplama yapılır.
- Importer idempotent çalışır; aynı veri tekrar senkronize edildiğinde mükerrer şehir veya mekan üretmez.
- Otomasyon Strapi'ye yazarken JWT oturumu kullanır; frontend yalnızca okuma amaçlı token ile çalışır.
- Mekan açıklamaları kaynak metinden üretilir, Groq ile zenginleştirilir ve `deep-translator` ile İngilizceye çevrilir.
- Görseller Strapi Media Library'ye yüklenir; Cloudinary aktifse canlı ortamda kalıcı URL üzerinden servis edilir.
- `source_media_manifest.json` ve `fallback_content_manifest.json` sayesinde medya silinse veya API eksik veri dönse bile arayüz tutarlı kalır.
- Streamlit arayüzü şehir seçimi, dil seçimi, dinamik istatistik kartları, mekan kartları ve hata durumlarıyla tam kullanıcı akışı sunar.
- `--dry-run`, `--limit` ve `--reset-strapi` komutlarıyla güvenli test, sınırlı çalışma ve temiz yeniden kurulum desteklenir.

## Veri Kapsamı

| Şehir | Mekan Sayısı |
| --- | ---: |
| Trabzon | 5 |
| İstanbul | 3 |
| Ankara | 4 |
| Antalya | 3 |
| Bursa | 4 |
| Nevşehir | 4 |
| Muğla | 4 |
| Mersin | 3 |
| Toplam | 30 |

İçerik kaynakları proje içinde manifest olarak tutulur:

- `sources.json`: şehir, mekan, resmi kaynak URL'si, extractor türü, puan ve görsel prompt bilgileri.
- `source_media_manifest.json`: her mekan için sabitlenmiş görsel URL'leri ve medya yedekleri.
- `fallback_content_manifest.json`: canlı API eksik veri döndürdüğünde frontend sürekliliğini sağlayan içerik yedeği.

## Veri Modeli

| Koleksiyon | Alanlar |
| --- | --- |
| `City` | `ad`, `ulke`, `kisa_bilgi`, `places` ilişkisi, locale bilgisi |
| `Place` | `mekan_adi`, `aciklama`, `puan`, `kapak_resmi`, `gorsel_prompt`, `gorsel_seed`, `gorsel_yedek_url`, `city` ilişkisi, locale bilgisi |

Bu model, şehirlerin birden fazla mekana sahip olmasını sağlar. Her mekan bir şehre bağlıdır ve aynı içerik Türkçe/İngilizce lokalizasyonlarla yönetilir.

## Proje Yapısı

```text
.
├── app.py
├── otomasyon.py
├── sources.json
├── source_media_manifest.json
├── fallback_content_manifest.json
├── requirements.txt
├── FINAL_RAPOR_SABLONU.md
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
└── gezi-rehberi-backend/
    ├── src/api/city/
    ├── src/api/place/
    ├── config/database.ts
    ├── config/middlewares.ts
    ├── config/plugins.ts
    └── .env.example
```

## Kurulum

### 1. Python Bağımlılıkları

```bash
pip install -r requirements.txt
```

### 2. Strapi Backend

```bash
cd gezi-rehberi-backend
npm install
npm run develop
```

Strapi geliştirme ortamı varsayılan olarak `http://localhost:1337` adresinde çalışır.

### 3. Streamlit Frontend

```bash
streamlit run app.py
```

Streamlit arayüzü varsayılan olarak `http://localhost:8501` adresinde açılır.

## Ortam Değişkenleri

### Otomasyon

Kök dizindeki `.env.example` dosyası temel alınarak `.env` oluşturulur:

```bash
STRAPI_URL=http://localhost:1337
STRAPI_EMAIL=ingest@example.com
STRAPI_PASSWORD=change-me
GROQ_API_KEY=gsk_xxx
```

`STRAPI_EMAIL` ve `STRAPI_PASSWORD`, Strapi'deki özel ingest kullanıcısıyla JWT oturumu açmak için kullanılır. Geriye dönük uyumluluk amacıyla `STRAPI_TOKEN` de desteklenir.

### Streamlit

`.streamlit/secrets.toml.example` dosyası temel alınarak `.streamlit/secrets.toml` oluşturulur:

```toml
STRAPI_URL = "https://your-strapi-service.onrender.com"
STRAPI_TOKEN = "read-only-token"
```

Frontend tarafında yalnızca okuma yetkili token kullanılmalıdır.

### Strapi Backend

`gezi-rehberi-backend/.env.example` dosyası canlı ortam değişkenlerini içerir:

```bash
DATABASE_CLIENT=postgres
DATABASE_URL=postgresql://user:password@host:5432/database
CLOUDINARY_NAME=your-cloud-name
CLOUDINARY_KEY=your-api-key
CLOUDINARY_SECRET=your-api-secret
CLOUDINARY_FOLDER=gezi-rehberi
```

Geliştirme sırasında SQLite kullanılabilir; canlı ortamda PostgreSQL ve Cloudinary önerilir.

## Otomasyon Kullanımı

### Dry Run

Strapi'ye yazmadan tüm kaynak çıkarımı, metin üretimi, çeviri ve görsel hazırlık akışını test eder:

```bash
python otomasyon.py --dry-run
```

### Sınırlı Senkronizasyon

İlk birkaç kaynağı test etmek için kullanılır:

```bash
python otomasyon.py --limit 3
```

### Tam Senkronizasyon

Manifestteki tüm şehir ve mekanları Strapi'ye idempotent şekilde yazar:

```bash
python otomasyon.py
```

### Temiz Yeniden Kurulum

Mevcut içerikleri yedekleyip temizledikten sonra manifestten yeniden üretir:

```bash
python otomasyon.py --reset-strapi
```

Bu komut özellikle final tesliminden önce veritabanını tutarlı hale getirmek için kullanılır.

## Frontend Davranışı

Streamlit arayüzü Strapi'den şehir ve mekan verilerini çeker, seçilen dile göre içerikleri gösterir ve şehir-mekan ilişkisini `documentId` temelli olarak eşleştirir. API eksik veri döndürürse fallback manifesti devreye girer; böylece canlı ortamda şehir sayısı, mekan sayısı ve görseller kullanıcıya tutarlı görünür.

Arayüzde desteklenen ana özellikler:

- Türkçe ve İngilizce dil seçimi.
- 8 şehir ve 30 mekan için dinamik listeleme.
- Şehre göre mekan filtreleme.
- Resmi kaynaklara bağlı görsel gösterimi.
- Strapi medyası eksikse yedek görsel URL'si kullanımı.
- API bağlantı hatalarında kullanıcı dostu durum mesajları.

## Canlı Ortam

Önerilen canlı mimari:

| Katman | Servis |
| --- | --- |
| Backend | Render üzerinde Strapi |
| Veritabanı | Render PostgreSQL veya harici PostgreSQL |
| Medya | Cloudinary |
| Frontend | Streamlit Cloud |
| Gizli Bilgiler | Platform env vars / Streamlit secrets |

Canlı ortamda medya dosyalarının silinmemesi için Cloudinary sağlayıcısı etkinleştirilmiştir. Ayrıca frontend, Strapi medya URL'si bulunamazsa `source_media_manifest.json` içindeki sabit görsel URL'lerine düşerek görsel sürekliliğini korur.

## Güvenlik Yaklaşımı

- API anahtarları, Strapi kullanıcı bilgileri ve tokenlar repoya yazılmaz.
- Otomasyon yazma işlemleri için JWT tabanlı ingest kullanıcısı kullanılır.
- Frontend yalnızca okuma yetkili token ile Strapi API'ye erişir.
- `.env`, `.streamlit/secrets.toml`, yerel veritabanı ve çalışma zamanı logları git dışında tutulur.
- Canlı ortamda medya kalıcılığı Cloudinary ile sağlanır.

## Test ve Doğrulama

Final teslimi öncesinde önerilen kontrol adımları:

```bash
python otomasyon.py --dry-run
python otomasyon.py --limit 3
python otomasyon.py
streamlit run app.py
```

Kontrol listesi:

- Strapi admin paneli erişilebilir.
- `City` ve `Place` koleksiyonları ilişkiyle birlikte görünür.
- Türkçe ve İngilizce içerikler Strapi'de yayınlanmış durumdadır.
- 8 şehir ve 30 mekan frontend üzerinde listelenir.
- Trabzon, İstanbul, Ankara, Antalya, Bursa, Nevşehir, Muğla ve Mersin seçilebilir.
- Her mekan kartında açıklama, puan ve görsel görünür.
- Dil değişimi arayüz metinlerini ve içerikleri doğru şekilde değiştirir.
- Cloudinary medya URL'leri canlı ortamda çalışır.
- Fallback görsel sistemi medya eksikliği durumunda devreye girer.

## Teslim Dokümantasyonu

`FINAL_RAPOR_SABLONU.md`, final raporu için hazır bir iskelet sunar. Raporun aşağıdaki başlıklarla doldurulması önerilir:

- Kapak bilgileri.
- Mimari akış diyagramı.
- Strapi admin ve canlı Streamlit erişim bilgileri.
- Kullanılan veri modeli ve API yapısı.
- Otomasyon fonksiyonlarının açıklaması.
- Arayüz ekran görüntüleri.
- Test sonuçları ve kısa değerlendirme.

## Değerlendirme Kapsamı

Bu proje final izlencesindeki ana maddeleri karşılayacak şekilde yapılandırılmıştır:

- Strapi üzerinde ilişkisel ve çok dilli veri modeli.
- REST API üzerinden güvenli okuma/yazma akışı.
- Resmi kaynaklardan otomatik veri toplama.
- Yapay zeka destekli metin zenginleştirme.
- Türkçe-İngilizce çeviri akışı.
- Otomatik görsel üretimi ve medya yönetimi.
- Modern, filtrelenebilir ve iki dilli Streamlit arayüzü.
- Canlı dağıtım için kalıcı veritabanı ve medya stratejisi.
- Kurulum, kullanım ve teslim dokümantasyonu.

## Lisans ve Not

Bu repo BIP210 final projesi kapsamında akademik teslim amacıyla hazırlanmıştır. Resmi kaynak bağlantıları içerik doğrulama ve referans amacıyla manifest içinde saklanır; canlı kullanımda ilgili kaynakların kullanım koşullarına uyulmalıdır.
