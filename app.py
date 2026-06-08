"""
BIP210 - Final Projesi: YZ Destekli Gezi Rehberi
app.py - Streamlit Frontend

Bu sürümde görseller tarayıcıya doğrudan uzak URL olarak verilmez.
Önce Python tarafında indirilir, base64 data-uri olarak karta gömülür.
Böylece Streamlit Cloud'da kırık /uploads URL'leri kartları boş bırakmaz.
"""

import base64
import hashlib
import html
import os
from urllib.parse import quote, urlparse

import requests
import streamlit as st


# ══════════════════════════════════════════════
# AYARLAR
# ══════════════════════════════════════════════
def ayar_al(adlar, varsayilan: str = "") -> str:
    if isinstance(adlar, str):
        adlar = [adlar]

    try:
        for ad in adlar:
            deger = st.secrets.get(ad, None)
            if deger is not None and str(deger).strip():
                return str(deger).strip()
    except Exception:
        pass

    for ad in adlar:
        deger = os.getenv(ad)
        if deger is not None and str(deger).strip():
            return str(deger).strip()

    return varsayilan


# Streamlit Cloud Secrets için önerilen isimler:
# STRAPI_URL = "https://gezi-rehberi-backend-11py.onrender.com"
# STRAPI_TOKEN = "Render Strapi Full Access Token"
#
# Eski isimlerin varsa onlar da çalışır:
# STRAPI_API_URL / STRAPI_API_TOKEN
STRAPI_URL = ayar_al(["STRAPI_URL", "STRAPI_API_URL"], "http://localhost:1337").rstrip("/")
STRAPI_TOKEN = ayar_al(["STRAPI_TOKEN", "STRAPI_API_TOKEN"], "").strip()


def auth_headers() -> dict:
    if STRAPI_TOKEN:
        return {"Authorization": f"Bearer {STRAPI_TOKEN}"}
    return {}


def stable_seed(text: str) -> int:
    return int(hashlib.md5(str(text).encode("utf-8")).hexdigest(), 16) % 10000


def guvenli_metin(deger) -> str:
    return html.escape(str(deger or ""), quote=True)


def data_uri_olustur(content: bytes, content_type: str = "image/jpeg") -> str:
    b64 = base64.b64encode(content).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


def placeholder_svg(adi: str, sehir: str) -> str:
    adi = guvenli_metin(adi)
    sehir = guvenli_metin(sehir)
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#0f3d22"/>
          <stop offset="50%" stop-color="#0f172a"/>
          <stop offset="100%" stop-color="#111827"/>
        </linearGradient>
      </defs>
      <rect width="800" height="500" fill="url(#g)"/>
      <circle cx="650" cy="100" r="130" fill="#22c55e" opacity="0.12"/>
      <circle cx="140" cy="390" r="160" fill="#3b82f6" opacity="0.08"/>
      <text x="50" y="245" fill="#ffffff" font-family="Arial, sans-serif" font-size="46" font-weight="700">{adi}</text>
      <text x="52" y="300" fill="#4ade80" font-family="Arial, sans-serif" font-size="24" font-weight="600">{sehir}</text>
      <text x="52" y="345" fill="#94a3b8" font-family="Arial, sans-serif" font-size="18">YZ Destekli Gezi Rehberi</text>
    </svg>
    """.encode("utf-8")
    return data_uri_olustur(svg, "image/svg+xml")


# ══════════════════════════════════════════════
# SAYFA
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="Gezi Rehberi — Türkiye'yi Keşfet",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #080c14 !important;
    color: #c9d1e0 !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

header[data-testid="stHeader"],
.stDeployButton,
footer,
[data-testid="stToolbar"],
section[data-testid="stSidebar"],
div[data-testid="stDecoration"] {
    display: none !important;
}

.navbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: rgba(8,12,20,0.94);
    backdrop-filter: blur(18px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0 48px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-brand-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.nav-brand-text {
    font-size: 1rem;
    font-weight: 800;
    color: #f8fafc;
}

.nav-brand-text span {
    color: #22c55e;
}

.nav-tag {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(34,197,94,0.12);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.25);
    padding: 6px 14px;
    border-radius: 999px;
}

.hero-section {
    position: relative;
    overflow: hidden;
    padding: 90px 48px 70px;
    min-height: 430px;
    background:
        radial-gradient(ellipse 70% 70% at 75% 20%, rgba(34,197,94,0.09), transparent 60%),
        radial-gradient(ellipse 40% 40% at 20% 90%, rgba(59,130,246,0.08), transparent 55%),
        #0d1420;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.20);
    color: #4ade80;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    padding: 7px 14px;
    border-radius: 999px;
    margin-bottom: 26px;
}

.hero-title {
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
    letter-spacing: -0.04em;
    margin-bottom: 20px;
}

.hero-title .accent {
    color: #22c55e;
}

.hero-sub {
    font-size: 1.08rem;
    color: #64748b;
    max-width: 560px;
    line-height: 1.7;
    margin-bottom: 42px;
}

.hero-stats {
    display: inline-flex;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    overflow: hidden;
    background: rgba(255,255,255,0.03);
}

.hero-stat {
    padding: 18px 32px;
    border-right: 1px solid rgba(255,255,255,0.07);
    text-align: center;
}

.hero-stat:last-child {
    border-right: none;
}

.hero-stat .sv {
    font-size: 1.8rem;
    font-weight: 900;
    color: #22c55e;
    line-height: 1;
}

.hero-stat .sl {
    font-size: 0.7rem;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 5px;
}

.toolbar-section {
    padding: 28px 48px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.toolbar-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
}

div[data-testid="stSelectbox"] > label {
    display: none !important;
}

div[data-baseweb="select"] > div {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    min-height: 48px !important;
}

[data-baseweb="select"] span {
    color: #e2e8f0 !important;
}

.city-hero-wrap {
    padding: 32px 48px 0;
}

.city-hero {
    padding: 32px 36px;
    background: linear-gradient(135deg, #0f1f0f 0%, #0d1520 100%);
    border: 1px solid rgba(34,197,94,0.15);
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 28px;
    position: relative;
    overflow: hidden;
}

.city-hero-icon {
    width: 64px;
    height: 64px;
    flex-shrink: 0;
    background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.05));
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
}

.city-hero-name {
    font-size: 1.8rem;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: -0.02em;
}

.city-hero-country {
    font-size: 0.84rem;
    font-weight: 600;
    color: #22c55e;
    margin-top: 4px;
}

.city-hero-desc {
    font-size: 0.92rem;
    color: #64748b;
    line-height: 1.65;
    margin-top: 8px;
    max-width: 700px;
}

.city-hero-badge {
    margin-left: auto;
    flex-shrink: 0;
    padding: 14px 22px;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 14px;
    text-align: center;
}

.city-hero-badge .bv {
    font-size: 1.85rem;
    font-weight: 900;
    color: #22c55e;
    line-height: 1;
}

.city-hero-badge .bl {
    font-size: 0.68rem;
    font-weight: 700;
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.section-head {
    padding: 40px 48px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.section-head-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #f1f5f9;
}

.section-pill {
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
}

.pill-count {
    background: rgba(255,255,255,0.06);
    color: #64748b;
    border: 1px solid rgba(255,255,255,0.08);
}

.pill-lang {
    background: rgba(59,130,246,0.1);
    color: #60a5fa;
    border: 1px solid rgba(59,130,246,0.2);
}

.pill-ai {
    background: rgba(168,85,247,0.1);
    color: #c084fc;
    border: 1px solid rgba(168,85,247,0.2);
}

.grid-outer {
    padding: 32px 48px 80px;
}

.mcard {
    background: #0e1420;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 28px;
    transition: border-color 0.2s, transform 0.2s;
}

.mcard:hover {
    border-color: rgba(34,197,94,0.25);
    transform: translateY(-2px);
}

.mcard-img {
    position: relative;
    height: 250px;
    overflow: hidden;
    background: #111827;
}

.mcard-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.mcard-img-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(14,20,32,0.92) 0%, rgba(14,20,32,0.25) 55%, rgba(14,20,32,0.05) 100%);
}

.mcard-img-badges {
    position: absolute;
    top: 14px;
    left: 14px;
    right: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.img-badge-left {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(34,197,94,0.92);
    color: #052e12;
    padding: 6px 11px;
    border-radius: 9px;
}

.img-badge-right {
    background: rgba(0,0,0,0.72);
    color: #fbbf24;
    font-size: 0.84rem;
    font-weight: 800;
    padding: 6px 11px;
    border-radius: 9px;
    border: 1px solid rgba(251,191,36,0.15);
}

.mcard-img-title {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 18px 22px;
}

.mcard-img-title h3 {
    font-size: 1.28rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.01em;
    text-shadow: 0 1px 8px rgba(0,0,0,0.55);
}

.mcard-body {
    padding: 20px 22px 0;
}

.mcard-desc {
    font-size: 0.9rem;
    color: #7387a8;
    line-height: 1.72;
}

.mcard-footer {
    padding: 16px 22px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 18px;
    gap: 12px;
}

.stars {
    display: flex;
    gap: 3px;
}

.star-f {
    color: #f59e0b;
    font-size: 13px;
}

.star-e {
    color: #1e293b;
    font-size: 13px;
}

.puan-label {
    font-size: 0.78rem;
    font-weight: 700;
    color: #475569;
}

.ai-tag {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(168,85,247,0.1);
    color: #c084fc;
    border: 1px solid rgba(168,85,247,0.15);
    padding: 5px 10px;
    border-radius: 8px;
}

.msg-box {
    margin: 48px;
    padding: 28px 32px;
    border-radius: 16px;
    border: 1px solid;
    font-size: 0.9rem;
    line-height: 1.6;
}

.msg-error {
    background: rgba(239,68,68,0.06);
    border-color: rgba(239,68,68,0.15);
    color: #fca5a5;
}

.msg-warn {
    background: rgba(245,158,11,0.06);
    border-color: rgba(245,158,11,0.15);
    color: #fcd34d;
}

.site-footer {
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 36px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}

.footer-left {
    font-size: 0.82rem;
    color: #334155;
}

.footer-left strong {
    color: #475569;
}

.footer-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.footer-tag {
    font-size: 0.68rem;
    font-weight: 600;
    background: rgba(255,255,255,0.04);
    color: #475569;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 4px 10px;
    border-radius: 8px;
}

@media (max-width: 900px) {
    .navbar, .toolbar-section, .section-head, .grid-outer, .site-footer {
        padding-left: 20px;
        padding-right: 20px;
    }

    .hero-section {
        padding: 70px 20px 50px;
        min-height: 380px;
    }

    .city-hero-wrap {
        padding-left: 20px;
        padding-right: 20px;
    }

    .city-hero {
        flex-direction: column;
        align-items: flex-start;
    }

    .city-hero-badge {
        margin-left: 0;
    }

    .hero-stats {
        flex-wrap: wrap;
    }

    .hero-stat {
        min-width: 50%;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════
# VERİ FONKSİYONLARI
# ══════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def sehirleri_getir(dil: str = "tr"):
    try:
        r = requests.get(
            f"{STRAPI_URL}/api/cities?locale={dil}&pagination[pageSize]=100&sort=ad:asc",
            headers=auth_headers(),
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("data", [])
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def mekanlari_getir(sehir_doc_id, dil: str = "tr"):
    filtreler = [
        f"filters[city][documentId][$eq]={sehir_doc_id}",
        f"filters[city][id][$eq]={sehir_doc_id}",
    ]

    for filtre in filtreler:
        try:
            r = requests.get(
                f"{STRAPI_URL}/api/places?{filtre}&populate=*&locale={dil}"
                f"&pagination[pageSize]=50&sort=puan:desc",
                headers=auth_headers(),
                timeout=15,
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            if data:
                return data
        except Exception:
            continue

    return []


def alan(kayit: dict, alan_adi: str, varsayilan=""):
    if isinstance(kayit, dict) and alan_adi in kayit:
        return kayit.get(alan_adi, varsayilan)

    attrs = kayit.get("attributes", {}) if isinstance(kayit, dict) else {}
    return attrs.get(alan_adi, varsayilan)


def tam_gorsel_url(url: str):
    if not url:
        return None

    url = str(url).strip()
    if not url:
        return None

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        return f"{STRAPI_URL}{url}"

    parsed = urlparse(url)

    # DB içinde localhost kayıtlıysa ve bulutta çalışıyorsak aynı path'i Render URL'ine taşır.
    if parsed.netloc.lower() in {"localhost:1337", "127.0.0.1:1337"} and not STRAPI_URL.startswith("http://localhost"):
        return f"{STRAPI_URL}{parsed.path}"

    return url


def gorsel_url_al(mekan: dict):
    try:
        kapak = mekan.get("kapak_resmi")

        if isinstance(kapak, dict):
            if kapak.get("url"):
                return tam_gorsel_url(kapak.get("url"))

            formats = kapak.get("formats") or {}
            for boyut in ["large", "medium", "small", "thumbnail"]:
                u = (formats.get(boyut) or {}).get("url")
                if u:
                    return tam_gorsel_url(u)

            data = kapak.get("data")
            if isinstance(data, dict):
                if data.get("url"):
                    return tam_gorsel_url(data.get("url"))

                attrs = data.get("attributes") or {}
                if attrs.get("url"):
                    return tam_gorsel_url(attrs.get("url"))

                formats2 = attrs.get("formats") or {}
                for boyut in ["large", "medium", "small", "thumbnail"]:
                    u = (formats2.get(boyut) or {}).get("url")
                    if u:
                        return tam_gorsel_url(u)

        attrs = mekan.get("attributes") or {}
        medya = attrs.get("kapak_resmi") or {}

        if isinstance(medya, dict):
            data2 = medya.get("data")
            if isinstance(data2, dict):
                if data2.get("url"):
                    return tam_gorsel_url(data2.get("url"))

                attrs2 = data2.get("attributes") or {}
                if attrs2.get("url"):
                    return tam_gorsel_url(attrs2.get("url"))

                formats3 = attrs2.get("formats") or {}
                for boyut in ["large", "medium", "small", "thumbnail"]:
                    u = (formats3.get(boyut) or {}).get("url")
                    if u:
                        return tam_gorsel_url(u)

    except Exception:
        pass

    return None


def yedek_gorsel_adaylari(adi: str, sehir: str):
    seed = stable_seed(f"{sehir}-{adi}")
    prompt = quote(f"{sehir} {adi} Turkey travel landmark realistic photo")

    return [
        f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=500&nologo=true&seed={seed}",
        f"https://picsum.photos/seed/{seed}/800/500",
    ]


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def resmi_indir_data_uri(url: str):
    """
    Görseli Python tarafında indirip base64 data-uri üretir.
    Böylece tarayıcıda kırık uzak URL görünmez.
    """
    if not url:
        return None

    try:
        r = requests.get(
            url,
            timeout=25,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
        )

        content_type = r.headers.get("content-type", "image/jpeg").split(";")[0].lower()

        if r.status_code == 200 and r.content and content_type.startswith("image/"):
            return data_uri_olustur(r.content, content_type)

    except Exception:
        return None

    return None


def kart_gorseli_data_uri(mekan: dict, adi: str, sehir: str) -> str:
    adaylar = []

    strapi_gorsel = gorsel_url_al(mekan)
    if strapi_gorsel:
        adaylar.append(strapi_gorsel)

    adaylar.extend(yedek_gorsel_adaylari(adi, sehir))

    for url in adaylar:
        data_uri = resmi_indir_data_uri(url)
        if data_uri:
            return data_uri

    return placeholder_svg(adi, sehir)


def yildiz(puan):
    try:
        p = max(0, min(5, int(puan or 0)))
    except Exception:
        p = 0

    return "".join(
        [
            '<span class="star-f">★</span>' if i < p else '<span class="star-e">★</span>'
            for i in range(5)
        ]
    )


# ══════════════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="navbar">
  <div class="nav-brand">
    <div class="nav-brand-icon">🗺️</div>
    <div class="nav-brand-text">Gezi<span>Rehberi</span></div>
  </div>
  <div class="nav-links">
    <span class="nav-tag">BIP210 · Final</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════
# VERİ YÜKLE
# ══════════════════════════════════════════════
sehirler = sehirleri_getir("tr")

if sehirler is None:
    st.markdown(
        '<div class="msg-box msg-error">❌ <strong>Strapi bağlantısı yok.</strong> '
        "Localde çalışıyorsan backend terminalinde <code>npm run develop</code> çalıştır. "
        "Bulutta çalışıyorsan Streamlit Secrets içindeki <code>STRAPI_URL</code> değerini kontrol et.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

if not sehirler:
    st.markdown(
        '<div class="msg-box msg-warn">⚠️ Şehir verisi bulunamadı. '
        "Önce <code>python otomasyon.py</code> çalıştır veya Strapi Public izinlerini kontrol et.</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ══════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════
sehir_sayisi = len(sehirler)
st.markdown(
    f"""
<div class="hero-section">
  <div class="hero-eyebrow">YZ + Google News + Strapi</div>
  <h1 class="hero-title">Türkiye'yi<br><span class="accent">Keşfet.</span></h1>
  <p class="hero-sub">Yapay zeka ve güncel haberlerle zenginleştirilmiş, çok dilli dijital gezi rehberi. Şehirleri, tarihi mekânları ve kültürel hazineleri keşfet.</p>
  <div class="hero-stats">
    <div class="hero-stat"><div class="sv">{sehir_sayisi}</div><div class="sl">Şehir</div></div>
    <div class="hero-stat"><div class="sv">8</div><div class="sl">Mekân</div></div>
    <div class="hero-stat"><div class="sv">2</div><div class="sl">Dil</div></div>
    <div class="hero-stat"><div class="sv">AI</div><div class="sl">Görsel</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════
# TOOLBAR
# ══════════════════════════════════════════════
st.markdown('<div class="toolbar-section">', unsafe_allow_html=True)
st.markdown('<div class="toolbar-label">Şehir & Dil Seçin</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 4])

with col1:
    sehir_map = {str(alan(s, "ad")): s for s in sehirler if alan(s, "ad")}
    secilen_ad = st.selectbox("Şehir", list(sehir_map.keys()), label_visibility="collapsed")

with col2:
    dil = st.selectbox(
        "Dil",
        ["tr", "en"],
        format_func=lambda x: "🇹🇷 Türkçe" if x == "tr" else "🇬🇧 English",
        label_visibility="collapsed",
    )

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ŞEHİR VERİSİ
# ══════════════════════════════════════════════
secilen = sehir_map[secilen_ad]
sehir_doc_id = secilen.get("documentId") or secilen.get("id")

sehirler_dil = sehirleri_getir(dil)
secilen_dil = next((s for s in (sehirler_dil or []) if alan(s, "ad") == secilen_ad), secilen)

ulke = guvenli_metin(alan(secilen_dil, "ulke"))
bilgi = guvenli_metin(alan(secilen_dil, "kisa_bilgi"))

mekanlar = mekanlari_getir(sehir_doc_id, dil)
mekan_say = len(mekanlar)

secilen_ad_html = guvenli_metin(secilen_ad)


# ══════════════════════════════════════════════
# ŞEHİR HERO KARTI
# ══════════════════════════════════════════════
st.markdown(
    f"""
<div class="city-hero-wrap">
<div class="city-hero">
  <div class="city-hero-icon">📍</div>
  <div style="flex:1; min-width:0;">
    <div class="city-hero-name">{secilen_ad_html}</div>
    <div class="city-hero-country">🌍 {ulke}</div>
    <div class="city-hero-desc">{bilgi}</div>
  </div>
  <div class="city-hero-badge">
    <div class="bv">{mekan_say}</div>
    <div class="bl">Mekân</div>
  </div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════
# BÖLÜM BAŞLIĞI
# ══════════════════════════════════════════════
dil_etiket = "🇹🇷 TR" if dil == "tr" else "🇬🇧 EN"
baslik_txt = "Mekânları Keşfet" if dil == "tr" else "Explore Places"

st.markdown(
    f"""
<div class="section-head">
  <span style="font-size:1.3rem">🏛️</span>
  <span class="section-head-title">{secilen_ad_html} · {baslik_txt}</span>
  <span class="section-pill pill-count">{mekan_say} mekân</span>
  <span class="section-pill pill-lang">{dil_etiket}</span>
  <span class="section-pill pill-ai">✦ AI + News</span>
</div>
""",
    unsafe_allow_html=True,
)

if not mekanlar:
    st.markdown(
        '<div class="msg-box msg-warn">⚠️ Bu şehir için mekân verisi bulunamadı.</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ══════════════════════════════════════════════
# MEKAN GRİDİ
# ══════════════════════════════════════════════
st.markdown('<div class="grid-outer">', unsafe_allow_html=True)

cols = st.columns(2, gap="large")

for i, mekan in enumerate(mekanlar):
    adi = str(alan(mekan, "mekan_adi") or "Mekân")
    aciklama = str(alan(mekan, "aciklama") or "")
    puan = alan(mekan, "puan") or 0
    sehir_nm = secilen_ad

    gorsel_data_uri = kart_gorseli_data_uri(mekan, adi, sehir_nm)

    adi_html = guvenli_metin(adi)
    aciklama_html = guvenli_metin(aciklama)
    sehir_html = guvenli_metin(sehir_nm).upper()
    puan_html = guvenli_metin(puan)
    yldz = yildiz(puan)

    with cols[i % 2]:
        st.markdown(
            f"""
        <div class="mcard">
          <div class="mcard-img">
            <img src="{gorsel_data_uri}" alt="{adi_html}"/>
            <div class="mcard-img-overlay"></div>
            <div class="mcard-img-badges">
              <span class="img-badge-left">{sehir_html}</span>
              <span class="img-badge-right">★ {puan_html}/5</span>
            </div>
            <div class="mcard-img-title"><h3>{adi_html}</h3></div>
          </div>
          <div class="mcard-body">
            <p class="mcard-desc">{aciklama_html}</p>
          </div>
          <div class="mcard-footer">
            <div style="display:flex;align-items:center;gap:8px;">
              <div class="stars">{yldz}</div>
              <span class="puan-label">{puan_html} / 5 puan</span>
            </div>
            <span class="ai-tag">✦ AI Zenginleştirildi</span>
          </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.markdown(
    """
<div class="site-footer">
  <div class="footer-left">
    <strong>BIP210 · İçerik Yönetimi · Final Projesi</strong><br>
    Strapi v5 · Python Otomasyon · Google News RSS · Groq LLaMA · Streamlit
  </div>
  <div class="footer-tags">
    <span class="footer-tag">Headless CMS</span>
    <span class="footer-tag">REST API</span>
    <span class="footer-tag">deep-translator</span>
    <span class="footer-tag">Pollinations AI</span>
    <span class="footer-tag">i18n</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
