"""
BIP210 - Final Projesi: YZ Destekli Gezi Rehberi
app.py - Streamlit Frontend (Son Kullanıcı Odaklı Tasarım)
"""

import streamlit as st
import requests
import os

# ══════════════════════════════════════════════
STRAPI_URL   = os.getenv("STRAPI_API_URL", "http://localhost:1337")
STRAPI_TOKEN = os.getenv("STRAPI_API_TOKEN", "")
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="Gezi Rehberi — Türkiye'yi Keşfet",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #080c14 !important;
    color: #c9d1e0 !important;
    -webkit-font-smoothing: antialiased;
}

.block-container { padding: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { display: none !important; }
.stDeployButton, footer, [data-testid="stToolbar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* ── NAVBAR ── */
.navbar {
    position: sticky; top: 0; z-index: 999;
    background: rgba(8,12,20,0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0 48px;
    height: 62px;
    display: flex; align-items: center; justify-content: space-between;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-brand-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}
.nav-brand-text { font-size: 1rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.01em; }
.nav-brand-text span { color: #22c55e; }
.nav-links { display: flex; align-items: center; gap: 8px; }
.nav-tag {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(34,197,94,0.12);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.2);
    padding: 5px 12px; border-radius: 20px;
}

/* ── HERO ── */
.hero-section {
    position: relative; overflow: hidden;
    padding: 100px 48px 80px;
    min-height: 480px;
    display: flex; flex-direction: column;
    align-items: flex-start; justify-content: flex-end;
    background: #0d1420;
}
.hero-bg {
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 70% 30%, rgba(34,197,94,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 20% 80%, rgba(59,130,246,0.06) 0%, transparent 50%);
}
.hero-grid {
    position: absolute; inset: 0; opacity: 0.03;
    background-image: linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px);
    background-size: 40px 40px;
}
.hero-eyebrow {
    position: relative;
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.2);
    color: #4ade80;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 7px 14px; border-radius: 20px;
    margin-bottom: 28px;
}
.hero-eyebrow::before {
    content: '';
    width: 6px; height: 6px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.7); }
}
.hero-title {
    position: relative;
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 900;
    color: #ffffff;
    line-height: 1.0;
    letter-spacing: -0.03em;
    margin-bottom: 20px;
}
.hero-title .accent { color: #22c55e; }
.hero-title .muted { color: rgba(255,255,255,0.35); }
.hero-sub {
    position: relative;
    font-size: 1.1rem;
    color: #64748b;
    max-width: 500px;
    line-height: 1.65;
    margin-bottom: 48px;
    font-weight: 400;
}
.hero-stats {
    position: relative;
    display: flex; gap: 0;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    overflow: hidden;
    background: rgba(255,255,255,0.03);
}
.hero-stat {
    padding: 18px 32px;
    border-right: 1px solid rgba(255,255,255,0.07);
    text-align: center;
}
.hero-stat:last-child { border-right: none; }
.hero-stat .sv { font-size: 1.8rem; font-weight: 800; color: #22c55e; line-height: 1; }
.hero-stat .sl { font-size: 0.7rem; font-weight: 500; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }

/* ── TOOLBAR SECTION ── */
.toolbar-section {
    padding: 28px 48px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding-bottom: 28px;
}
.toolbar-label {
    font-size: 0.7rem; font-weight: 600; color: #475569;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin-bottom: 12px;
}

/* Streamlit selectbox override */
div[data-testid="stSelectbox"] > label { display: none !important; }
div[data-baseweb="select"] > div {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    min-height: 48px !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: rgba(34,197,94,0.4) !important;
}
[data-baseweb="select"] span { color: #e2e8f0 !important; font-size: 0.95rem !important; }

/* ── ŞEHİR HERO ── */
.city-hero {
    margin: 0 48px;
    padding: 32px 36px;
    background: linear-gradient(135deg, #0f1f0f 0%, #0d1520 100%);
    border: 1px solid rgba(34,197,94,0.15);
    border-radius: 20px;
    display: flex; align-items: center; gap: 28px;
    position: relative; overflow: hidden;
}
.city-hero::before {
    content: '';
    position: absolute; right: -40px; top: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(34,197,94,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.city-hero-icon {
    width: 64px; height: 64px; flex-shrink: 0;
    background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.05));
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
}
.city-hero-name { font-size: 1.8rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; }
.city-hero-country {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.82rem; font-weight: 500; color: #22c55e; margin-top: 4px;
}
.city-hero-desc { font-size: 0.9rem; color: #64748b; line-height: 1.6; margin-top: 8px; max-width: 600px; }
.city-hero-badge {
    margin-left: auto; flex-shrink: 0;
    padding: 12px 20px;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 14px;
    text-align: center;
}
.city-hero-badge .bv { font-size: 1.8rem; font-weight: 800; color: #22c55e; line-height: 1; }
.city-hero-badge .bl { font-size: 0.68rem; font-weight: 500; color: #4ade80; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── BÖLÜM BAŞLIĞI ── */
.section-head {
    padding: 40px 48px 24px;
    display: flex; align-items: center; gap: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    margin-bottom: 0;
}
.section-head-title { font-size: 1.15rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.01em; }
.section-pill {
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em;
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

/* ── MEKAN GRID ── */
.grid-outer { padding: 32px 48px 80px; }

/* ── MEKAN KARTI ── */
.mcard {
    background: #0e1420;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 28px;
    transition: border-color 0.2s;
}
.mcard:hover { border-color: rgba(34,197,94,0.25); }

.mcard-img {
    position: relative;
    height: 240px;
    overflow: hidden;
    background: #111827;
}
.mcard-img img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 0.4s ease;
}
.mcard:hover .mcard-img img { transform: scale(1.03); }
.mcard-img-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(14,20,32,0.85) 0%, transparent 50%);
}
.mcard-img-badges {
    position: absolute; top: 14px;
    width: 100%; padding: 0 14px;
    display: flex; justify-content: space-between; align-items: flex-start;
}
.img-badge-left {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(34,197,94,0.9);
    color: #052e12;
    padding: 5px 10px; border-radius: 8px;
}
.img-badge-right {
    display: flex; align-items: center; gap: 5px;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(8px);
    color: #fbbf24;
    font-size: 0.82rem; font-weight: 700;
    padding: 5px 10px; border-radius: 8px;
    border: 1px solid rgba(251,191,36,0.15);
}
.mcard-img-title {
    position: absolute; bottom: 0; left: 0; right: 0;
    padding: 14px 20px 16px;
}
.mcard-img-title h3 {
    font-size: 1.15rem; font-weight: 700; color: #ffffff;
    letter-spacing: -0.01em; text-shadow: 0 1px 8px rgba(0,0,0,0.5);
}

.mcard-body { padding: 20px 22px 0; }
.mcard-desc { font-size: 0.875rem; color: #64748b; line-height: 1.65; }

.mcard-footer {
    padding: 16px 22px 18px;
    display: flex; align-items: center; justify-content: space-between;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 16px;
}
.stars { display: flex; gap: 3px; }
.star-f { color: #f59e0b; font-size: 13px; }
.star-e { color: #1e293b; font-size: 13px; }
.puan-label { font-size: 0.78rem; font-weight: 600; color: #475569; }
.ai-tag {
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(168,85,247,0.1);
    color: #c084fc;
    border: 1px solid rgba(168,85,247,0.15);
    padding: 4px 10px; border-radius: 8px;
    display: flex; align-items: center; gap: 4px;
}

/* ── DURUM MESAJLARI ── */
.msg-box {
    margin: 48px;
    padding: 28px 32px;
    border-radius: 16px;
    border: 1px solid;
    font-size: 0.9rem;
    line-height: 1.6;
}
.msg-error { background: rgba(239,68,68,0.06); border-color: rgba(239,68,68,0.15); color: #fca5a5; }
.msg-warn  { background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.15); color: #fcd34d; }

/* ── FOOTER ── */
.site-footer {
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 36px 48px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 12px;
}
.footer-left { font-size: 0.82rem; color: #1e293b; }
.footer-left strong { color: #334155; }
.footer-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.footer-tag {
    font-size: 0.68rem; font-weight: 500;
    background: rgba(255,255,255,0.04);
    color: #334155;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 4px 10px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── VERİ ──────────────────────────────────────
def auth_headers():
    return {"Authorization": f"Bearer {STRAPI_TOKEN}"}

@st.cache_data(ttl=60, show_spinner=False)
def sehirleri_getir(dil="tr"):
    try:
        r = requests.get(
            f"{STRAPI_URL}/api/cities?locale={dil}&pagination[pageSize]=100&sort=ad:asc",
            headers=auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return []

@st.cache_data(ttl=60, show_spinner=False)
def mekanlari_getir(sehir_doc_id, dil="tr"):
    for filtre in [f"filters[city][documentId][$eq]={sehir_doc_id}",
                   f"filters[city][id][$eq]={sehir_doc_id}"]:
        try:
            r = requests.get(
                f"{STRAPI_URL}/api/places?{filtre}&populate=*&locale={dil}"
                f"&pagination[pageSize]=50&sort=puan:desc",
                headers=auth_headers(), timeout=10)
            r.raise_for_status()
            data = r.json().get("data", [])
            if data: return data
        except Exception:
            continue
    return []

def gorsel_url_al(mekan):
    def tam(url):
        if not url: return None
        return f"{STRAPI_URL}{url}" if url.startswith("/") else url
    try:
        kapak = mekan.get("kapak_resmi")
        if isinstance(kapak, dict):
            if kapak.get("url"): return tam(kapak["url"])
            for b in ["large","medium","small","thumbnail"]:
                u = kapak.get("formats", {}).get(b, {}).get("url")
                if u: return tam(u)
            data = kapak.get("data", {})
            if isinstance(data, dict):
                u = data.get("url") or data.get("attributes", {}).get("url")
                if u: return tam(u)
        attrs = mekan.get("attributes", {})
        data2 = attrs.get("kapak_resmi", {}).get("data", {})
        if isinstance(data2, dict):
            u = data2.get("url") or data2.get("attributes", {}).get("url")
            if u: return tam(u)
    except Exception:
        pass
    return None

def alan(m, k):
    if k in m: return m[k]
    return m.get("attributes", {}).get(k, "")

def yildiz(puan):
    p = int(puan or 0)
    d = ''.join(['<span class="star-f">★</span>' if i<p else '<span class="star-e">★</span>' for i in range(5)])
    return d

# ── NAVBAR ──────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="nav-brand">
    <div class="nav-brand-icon">🗺️</div>
    <div class="nav-brand-text">Gezi<span>Rehberi</span></div>
  </div>
  <div class="nav-links">
    <span class="nav-tag">BIP210 · Final</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── VERİ YÜKLE ──────────────────────────────────
sehirler = sehirleri_getir("tr")

if sehirler is None:
    st.markdown('<div class="msg-box msg-error">❌ <strong>Strapi bağlantısı yok.</strong> Terminalde <code>npm run develop</code> çalıştırın.</div>', unsafe_allow_html=True)
    st.stop()
if not sehirler:
    st.markdown('<div class="msg-box msg-warn">⚠️ Şehir verisi bulunamadı. <code>python otomasyon.py</code> çalıştırın.</div>', unsafe_allow_html=True)
    st.stop()

# ── HERO ────────────────────────────────────────
sehir_sayisi  = len(sehirler)
st.markdown(f"""
<div class="hero-section">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
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
""", unsafe_allow_html=True)

# ── TOOLBAR ─────────────────────────────────────
st.markdown('<div class="toolbar-section">', unsafe_allow_html=True)
st.markdown('<div class="toolbar-label">Şehir & Dil Seçin</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 4])
with col1:
    sehir_map   = {alan(s, "ad"): s for s in sehirler}
    secilen_ad  = st.selectbox("Şehir", list(sehir_map.keys()), label_visibility="collapsed")
with col2:
    dil = st.selectbox("Dil", ["tr", "en"],
                       format_func=lambda x: "🇹🇷 Türkçe" if x == "tr" else "🇬🇧 English",
                       label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# ── ŞEHİR VERİSİ ────────────────────────────────
secilen      = sehir_map[secilen_ad]
sehir_doc_id = secilen.get("documentId") or secilen.get("id")

sehirler_dil = sehirleri_getir(dil)
secilen_dil  = next((s for s in (sehirler_dil or []) if alan(s,"ad") == secilen_ad), secilen)

ulke  = alan(secilen_dil, "ulke")
bilgi = alan(secilen_dil, "kisa_bilgi")

mekanlar  = mekanlari_getir(sehir_doc_id, dil)
mekan_say = len(mekanlar)

# ── ŞEHİR HERO KARTI ────────────────────────────
st.markdown(f"""
<div style="padding: 32px 48px 0;">
<div class="city-hero">
  <div class="city-hero-icon">📍</div>
  <div style="flex:1; min-width:0;">
    <div class="city-hero-name">{secilen_ad}</div>
    <div class="city-hero-country">🌍 {ulke}</div>
    <div class="city-hero-desc">{bilgi}</div>
  </div>
  <div class="city-hero-badge">
    <div class="bv">{mekan_say}</div>
    <div class="bl">Mekân</div>
  </div>
</div>
</div>
""", unsafe_allow_html=True)

# ── BÖLÜM BAŞLIĞI ───────────────────────────────
dil_etiket = "🇹🇷 TR" if dil == "tr" else "🇬🇧 EN"
baslik_txt  = "Mekânları Keşfet" if dil == "tr" else "Explore Places"

st.markdown(f"""
<div class="section-head">
  <span style="font-size:1.3rem">🏛️</span>
  <span class="section-head-title">{secilen_ad} · {baslik_txt}</span>
  <span class="section-pill pill-count">{mekan_say} mekân</span>
  <span class="section-pill pill-lang">{dil_etiket}</span>
  <span class="section-pill pill-ai">✦ AI + News</span>
</div>
""", unsafe_allow_html=True)

if not mekanlar:
    st.markdown('<div class="msg-box msg-warn">⚠️ Bu şehir için mekân verisi bulunamadı.</div>', unsafe_allow_html=True)
    st.stop()

# ── MEKAN GRİDİ ─────────────────────────────────
st.markdown('<div class="grid-outer">', unsafe_allow_html=True)

cols = st.columns(2, gap="large")
for i, mekan in enumerate(mekanlar):
    adi      = alan(mekan, "mekan_adi")
    aciklama = alan(mekan, "aciklama")
    puan     = alan(mekan, "puan") or 0
    gorsel   = gorsel_url_al(mekan)
    sehir_nm = secilen_ad

    if not gorsel:
        gorsel = f"https://picsum.photos/seed/{abs(hash(adi))%900}/800/500"

    yldz = yildiz(puan)

    with cols[i % 2]:
        st.markdown(f"""
        <div class="mcard">
          <div class="mcard-img">
            <img src="{gorsel}" alt="{adi}"
                 onerror="this.src='https://picsum.photos/seed/{abs(hash(adi))%400}/800/500'"/>
            <div class="mcard-img-overlay"></div>
            <div class="mcard-img-badges">
              <span class="img-badge-left">{sehir_nm}</span>
              <span class="img-badge-right">★ {puan}/5</span>
            </div>
            <div class="mcard-img-title"><h3>{adi}</h3></div>
          </div>
          <div class="mcard-body">
            <p class="mcard-desc">{aciklama}</p>
          </div>
          <div class="mcard-footer">
            <div style="display:flex;align-items:center;gap:8px;">
              <div class="stars">{yldz}</div>
              <span class="puan-label">{puan} / 5 puan</span>
            </div>
            <span class="ai-tag">✦ AI Zenginleştirildi</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ──────────────────────────────────────
st.markdown("""
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
""", unsafe_allow_html=True)