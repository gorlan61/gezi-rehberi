"""
BIP210 - Final Projesi: YZ Destekli Gezi Rehberi
app.py - Streamlit Frontend

- Strapi REST API'den sehir ve mekan verilerini okur.
- TR / EN arayuz metinlerini tek sozlukten yonetir.
- Dinamik sayaçlar ve documentId tabanli filtreleme kullanir.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
import streamlit as st


TEXT = {
    "tr": {
        "page_title": "Gezi Rehberi - Turkiye'yi Kesfet",
        "brand_tag": "BIP210 Final",
        "eyebrow": "Resmi kaynaklar + otomasyon + Strapi",
        "hero_title": "Turkiye'yi",
        "hero_accent": "Kesfet.",
        "hero_sub": (
            "Resmi kaynaklardan toplanan, cok dilli olarak yonetilen ve "
            "modern bir arayuzle sunulan dijital gezi rehberi."
        ),
        "stat_cities": "Sehir",
        "stat_places": "Mekan",
        "stat_languages": "Dil",
        "stat_media": "Medya",
        "stat_media_value": "Yedekli",
        "toolbar_label": "Sehir ve Dil Secimi",
        "city_label": "Sehir",
        "language_label": "Dil",
        "section_title": "Mekanlari Kesfet",
        "section_dynamic": "Dinamik Icerik",
        "city_badge": "Mekan",
        "no_connection_title": "Strapi baglantisi kurulamadi.",
        "no_connection_body": (
            "Local ortamda backend terminalinde `npm run develop` calistirin "
            "ve `STRAPI_URL` degerini kontrol edin."
        ),
        "no_cities": (
            "Sehir verisi bulunamadi. Once `python otomasyon.py` komutunu "
            "calistirin veya Strapi erisim izinlerini dogrulayin."
        ),
        "no_places": "Bu sehir icin yayinlanmis mekan bulunamadi.",
        "rating_suffix": "/ 5 puan",
        "card_badge": "Yayinlanmis Icerik",
        "footer_title": "BIP210 - Icerik Yonetimi Final Projesi",
        "footer_sub": "Strapi v5 · Python otomasyon · resmi kaynaklar · Streamlit",
        "lang_tr": "Turkce",
        "lang_en": "English",
    },
    "en": {
        "page_title": "Travel Guide - Discover Turkiye",
        "brand_tag": "BIP210 Final",
        "eyebrow": "Official sources + automation + Strapi",
        "hero_title": "Discover",
        "hero_accent": "Turkiye.",
        "hero_sub": (
            "A digital travel guide sourced from official content, managed in "
            "multiple languages and delivered through a modern interface."
        ),
        "stat_cities": "Cities",
        "stat_places": "Places",
        "stat_languages": "Languages",
        "stat_media": "Media",
        "stat_media_value": "Backup",
        "toolbar_label": "City and Language",
        "city_label": "City",
        "language_label": "Language",
        "section_title": "Explore Places",
        "section_dynamic": "Dynamic Content",
        "city_badge": "Places",
        "no_connection_title": "Strapi connection is unavailable.",
        "no_connection_body": (
            "Start the backend with `npm run develop` in local development "
            "and verify the `STRAPI_URL` setting."
        ),
        "no_cities": (
            "No city data was found. Run `python otomasyon.py` first or check "
            "Strapi access permissions."
        ),
        "no_places": "No published places were found for this city.",
        "rating_suffix": "/ 5 rating",
        "card_badge": "Published Content",
        "footer_title": "BIP210 - Content Management Final Project",
        "footer_sub": "Strapi v5 · Python automation · official sources · Streamlit",
        "lang_tr": "Turkish",
        "lang_en": "English",
    },
}


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_MEDIA_PATH = ROOT_DIR / "source_media_manifest.json"
FALLBACK_CONTENT_PATH = ROOT_DIR / "fallback_content_manifest.json"


def normalize_key(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.casefold().split())


def load_source_media_manifest() -> list[dict]:
    try:
        with SOURCE_MEDIA_PATH.open("r", encoding="utf-8") as source_file:
            data = json.load(source_file)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        pass
    return []


def load_fallback_content_manifest() -> list[dict]:
    try:
        with FALLBACK_CONTENT_PATH.open("r", encoding="utf-8") as source_file:
            data = json.load(source_file)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        pass
    return []


SOURCE_MEDIA_ITEMS = load_source_media_manifest()
FALLBACK_CONTENT_ITEMS = load_fallback_content_manifest()
CANONICAL_CITY_ORDER: list[str] = []
CANONICAL_CITY_KEYS: set[str] = set()
CANONICAL_PLACES_BY_CITY: dict[str, list[str]] = {}
OFFICIAL_IMAGE_BY_KEY: dict[tuple[str, str], str] = {}
CANONICAL_COUNTRY_BY_CITY: dict[str, str] = {}
CANONICAL_CITY_SUMMARY_TR: dict[str, str] = {}
FALLBACK_CITY_DATA_BY_KEY: dict[str, dict[str, object]] = {}
FALLBACK_PLACES_BY_CITY: dict[str, list[dict[str, object]]] = {}

for item in SOURCE_MEDIA_ITEMS:
    city_name = str(item.get("city") or "").strip()
    place_name = str(item.get("place") or "").strip()
    city_key = normalize_key(city_name)
    place_key = normalize_key(place_name)
    if not city_name or not place_name:
        continue
    if city_key not in CANONICAL_CITY_KEYS:
        CANONICAL_CITY_KEYS.add(city_key)
        CANONICAL_CITY_ORDER.append(city_name)
    CANONICAL_PLACES_BY_CITY.setdefault(city_key, []).append(place_name)
    official_image_url = str(item.get("official_image_url") or "").strip()
    if official_image_url:
        OFFICIAL_IMAGE_BY_KEY[(city_key, place_key)] = official_image_url
    country_name = str(item.get("country") or "").strip()
    if country_name and city_key not in CANONICAL_COUNTRY_BY_CITY:
        CANONICAL_COUNTRY_BY_CITY[city_key] = country_name
    summary_tr = str(item.get("city_summary_tr") or "").strip()
    if summary_tr and city_key not in CANONICAL_CITY_SUMMARY_TR:
        CANONICAL_CITY_SUMMARY_TR[city_key] = summary_tr

CANONICAL_TOTAL_PLACES = sum(len(places) for places in CANONICAL_PLACES_BY_CITY.values())

for item in FALLBACK_CONTENT_ITEMS:
    city_name = str(item.get("city") or "").strip()
    place_name = str(item.get("place") or "").strip()
    city_key = normalize_key(city_name)
    place_key = normalize_key(place_name)
    if not city_key or not place_key:
        continue

    if city_key not in FALLBACK_CITY_DATA_BY_KEY:
        FALLBACK_CITY_DATA_BY_KEY[city_key] = {
            "city": city_name,
            "country_tr": str(item.get("country_tr") or "").strip(),
            "country_en": str(item.get("country_en") or "").strip(),
            "city_summary_tr": str(item.get("city_summary_tr") or "").strip(),
            "city_summary_en": str(item.get("city_summary_en") or "").strip(),
        }

    FALLBACK_PLACES_BY_CITY.setdefault(city_key, []).append(
        {
            "city": city_name,
            "place": place_name,
            "description_tr": str(item.get("description_tr") or "").strip(),
            "description_en": str(item.get("description_en") or "").strip(),
            "score": item.get("score", 0),
            "official_image_url": str(item.get("official_image_url") or "").strip(),
            "source_url": str(item.get("source_url") or "").strip(),
        }
    )


def official_image_url_for(city_name: str, place_name: str) -> str | None:
    return OFFICIAL_IMAGE_BY_KEY.get((normalize_key(city_name), normalize_key(place_name)))


def canonical_place_names(city_name: str) -> list[str]:
    return CANONICAL_PLACES_BY_CITY.get(normalize_key(city_name), [])


def canonical_country_for_city(city_name: str) -> str:
    return CANONICAL_COUNTRY_BY_CITY.get(normalize_key(city_name), "")


def canonical_city_summary_tr(city_name: str) -> str:
    return CANONICAL_CITY_SUMMARY_TR.get(normalize_key(city_name), "")


def fallback_city_data(city_name: str) -> dict[str, object]:
    return FALLBACK_CITY_DATA_BY_KEY.get(normalize_key(city_name), {})


def fallback_country_for_city(city_name: str, lang: str) -> str:
    data = fallback_city_data(city_name)
    return str(data.get(f"country_{lang}") or data.get("country_tr") or "")


def fallback_city_summary(city_name: str, lang: str) -> str:
    data = fallback_city_data(city_name)
    return str(data.get(f"city_summary_{lang}") or data.get("city_summary_tr") or "")


def fallback_places_for_city(city_name: str, lang: str) -> list[dict]:
    fallback_places = FALLBACK_PLACES_BY_CITY.get(normalize_key(city_name), [])
    records: list[dict] = []

    for item in fallback_places:
        description = str(item.get(f"description_{lang}") or item.get("description_tr") or "").strip()
        records.append(
            {
                "documentId": f"fallback-place::{normalize_key(city_name)}::{normalize_key(item.get('place'))}",
                "mekan_adi": str(item.get("place") or "").strip(),
                "aciklama": description,
                "puan": item.get("score", 0),
                "gorsel_yedek_url": str(item.get("official_image_url") or "").strip(),
                "kaynak_url": str(item.get("source_url") or "").strip(),
            }
        )

    return records


def clean_api_token(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    token_match = re.search(r"([A-Za-z0-9_-]{32,})", text)
    if token_match:
        return token_match.group(1)
    return text.strip().strip('"').strip("'")


def setting_get(names: list[str] | str, default: str = "") -> str:
    if isinstance(names, str):
        names = [names]

    try:
        for name in names:
            value = st.secrets.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
    except Exception:
        pass

    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip():
            return str(value).strip()

    return default


STRAPI_URL = setting_get(["STRAPI_URL", "STRAPI_API_URL"], "http://localhost:1337").rstrip("/")
STRAPI_TOKEN = clean_api_token(setting_get(["STRAPI_TOKEN", "STRAPI_API_TOKEN"], ""))


def t(key: str, lang: str) -> str:
    return TEXT.get(lang, TEXT["tr"]).get(key, TEXT["tr"].get(key, key))


def uses_local_strapi() -> bool:
    try:
        return (urlparse(STRAPI_URL).hostname or "").lower() in {"localhost", "127.0.0.1"}
    except Exception:
        return False


def auth_headers() -> dict[str, str]:
    if STRAPI_TOKEN and not uses_local_strapi():
        return {"Authorization": f"Bearer {STRAPI_TOKEN}"}
    return {}


def stable_seed(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % 10000


def safe_text(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def field(record: dict, key: str, default: object = "") -> object:
    if key in record:
        return record.get(key, default)
    attrs = record.get("attributes")
    if isinstance(attrs, dict):
        return attrs.get(key, default)
    return default


def filter_canonical_cities(cities: list[dict]) -> list[dict]:
    if not CANONICAL_CITY_ORDER:
        return cities

    best_by_city: dict[str, dict] = {}
    for city in cities:
        city_name = str(field(city, "ad") or "").strip()
        city_key = normalize_key(city_name)
        if city_key in CANONICAL_CITY_KEYS and city_key not in best_by_city:
            best_by_city[city_key] = city

    ordered_cities: list[dict] = []
    for city_name in CANONICAL_CITY_ORDER:
        city = best_by_city.get(normalize_key(city_name))
        if city:
            ordered_cities.append(city)
    return ordered_cities


@st.cache_data(ttl=60, show_spinner=False)
def fetch_cities(lang: str = "tr") -> list[dict] | None:
    try:
        response = requests.get(
            f"{STRAPI_URL}/api/cities",
            params={
                "locale": lang,
                "status": "published",
                "pagination[pageSize]": 100,
                "sort": "ad:asc",
            },
            headers=auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return filter_canonical_cities(response.json().get("data", []))
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_places(city_document_id: str, lang: str = "tr") -> list[dict]:
    filters = {
        "filters[city][documentId][$eq]": city_document_id,
    }

    try:
        response = requests.get(
            f"{STRAPI_URL}/api/places",
            params={
                **filters,
                "locale": lang,
                "status": "published",
                "populate": "*",
                "pagination[pageSize]": 100,
                "sort": "puan:desc",
            },
            headers=auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_total_places() -> int:
    if CANONICAL_TOTAL_PLACES:
        return CANONICAL_TOTAL_PLACES

    try:
        response = requests.get(
            f"{STRAPI_URL}/api/places",
            params={
                "locale": "tr",
                "status": "published",
                "pagination[pageSize]": 200,
                "fields[0]": "documentId",
            },
            headers=auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return len({field(item, "documentId") for item in data if field(item, "documentId")})
    except Exception:
        return 0


def city_by_document_id(cities: list[dict], document_id: str) -> dict | None:
    for city in cities:
        if str(field(city, "documentId")) == str(document_id):
            return city
    return None


def city_by_name(cities: list[dict], city_name: str) -> dict | None:
    target_key = normalize_key(city_name)
    for city in cities:
        if normalize_key(field(city, "ad")) == target_key:
            return city
    return None


def city_name_from_key(city_key: str) -> str:
    target_key = normalize_key(city_key)
    for city_name in CANONICAL_CITY_ORDER:
        if normalize_key(city_name) == target_key:
            return city_name
    fallback_city = FALLBACK_CITY_DATA_BY_KEY.get(target_key) or {}
    return str(fallback_city.get("city") or "")


def build_city_options(cities_tr: list[dict], cities_ui: list[dict]) -> list[dict[str, str]]:
    preferred_names = CANONICAL_CITY_ORDER or [str(field(city, "ad") or "").strip() for city in cities_tr]
    options: list[dict[str, str]] = []
    seen: set[str] = set()

    for city_name in preferred_names:
        city_key = normalize_key(city_name)
        if not city_key or city_key in seen:
            continue

        seen.add(city_key)
        base_city = city_by_name(cities_tr, city_name) or city_by_name(cities_ui, city_name)
        ui_city = city_by_name(cities_ui, city_name) or base_city
        label = str(field(ui_city or base_city or {}, "ad") or city_name)
        options.append({"id": city_key, "city_name": city_name, "label": label})

    return options


def image_url_from_place(place: dict) -> str | None:
    try:
        image = place.get("kapak_resmi")
        if isinstance(image, dict):
            if image.get("url"):
                return normalize_media_url(image.get("url"))

            formats = image.get("formats") or {}
            for size in ("large", "medium", "small", "thumbnail"):
                candidate = (formats.get(size) or {}).get("url")
                if candidate:
                    return normalize_media_url(candidate)

            data = image.get("data")
            if isinstance(data, dict):
                if data.get("url"):
                    return normalize_media_url(data.get("url"))
                attrs = data.get("attributes") or {}
                if attrs.get("url"):
                    return normalize_media_url(attrs.get("url"))

        attrs = place.get("attributes") or {}
        image = attrs.get("kapak_resmi") or {}
        if isinstance(image, dict):
            data = image.get("data")
            if isinstance(data, dict):
                if data.get("url"):
                    return normalize_media_url(data.get("url"))
                attrs = data.get("attributes") or {}
                if attrs.get("url"):
                    return normalize_media_url(attrs.get("url"))
    except Exception:
        return None

    return None


def normalize_media_url(url: str | None) -> str | None:
    if not url:
        return None

    raw = str(url).strip()
    if not raw:
        return None
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("/"):
        return f"{STRAPI_URL}{raw}"

    parsed = urlparse(raw)
    if parsed.netloc.lower() in {"localhost:1337", "127.0.0.1:1337"} and not STRAPI_URL.startswith(
        "http://localhost"
    ):
        return f"{STRAPI_URL}{parsed.path}"

    return raw


def is_same_strapi_host(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        strapi_host = urlparse(STRAPI_URL).netloc.lower()
        return host == strapi_host or host in {"localhost:1337", "127.0.0.1:1337"}
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def remote_image_works(url: str) -> bool:
    if not url:
        return False

    try:
        response = requests.get(url, timeout=8, stream=True)
        content_type = response.headers.get("content-type", "").lower()
        return response.status_code == 200 and "image" in content_type
    except Exception:
        return False


def pollinations_image_url(prompt_text: str, seed: int) -> str:
    prompt = quote(prompt_text)
    return f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=500&nologo=true&seed={seed}"


def picsum_fallback_url(seed: int) -> str:
    return f"https://picsum.photos/seed/{seed}/800/500"


def backup_image_url_from_place(place: dict) -> str | None:
    raw_url = field(place, "gorsel_yedek_url", "")
    stored_url = normalize_media_url(raw_url if isinstance(raw_url, str) else "")
    if stored_url:
        return stored_url

    raw_prompt = field(place, "gorsel_prompt", "")
    prompt = raw_prompt.strip() if isinstance(raw_prompt, str) else ""
    raw_seed = field(place, "gorsel_seed", "")
    try:
        seed = int(raw_seed)
    except Exception:
        seed = stable_seed(prompt) if prompt else None

    if prompt and seed is not None:
        return pollinations_image_url(prompt, seed)

    return None


def is_generated_image_url(url: str | None) -> bool:
    if not url:
        return False

    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False

    return host in {"image.pollinations.ai", "picsum.photos"}


def fallback_image_url(place: dict, place_name: str, city_name: str) -> str:
    official_url = official_image_url_for(city_name, place_name)
    if official_url:
        return official_url

    backup_url = backup_image_url_from_place(place)
    if backup_url:
        return backup_url

    seed = stable_seed(f"{city_name}-{place_name}")
    return picsum_fallback_url(seed)


def safe_image_url(place: dict, place_name: str, city_name: str) -> str:
    official_url = official_image_url_for(city_name, place_name)
    if official_url and remote_image_works(official_url):
        return official_url

    backup_url = backup_image_url_from_place(place)
    if backup_url and not is_generated_image_url(backup_url) and remote_image_works(backup_url):
        return backup_url

    image_url = image_url_from_place(place)
    if image_url and is_same_strapi_host(image_url):
        if remote_image_works(image_url):
            return image_url
        return fallback_image_url(place, place_name, city_name)
    if image_url:
        return image_url
    return fallback_image_url(place, place_name, city_name)


def place_quality(place: dict) -> tuple[int, int, int, int, float]:
    image_url = image_url_from_place(place) or ""
    backup_url = backup_image_url_from_place(place) or ""
    description = str(field(place, "aciklama") or "")
    try:
        score = float(field(place, "puan") or 0)
    except Exception:
        score = 0.0

    return (
        1 if backup_url and not is_generated_image_url(backup_url) else 0,
        1 if image_url and not is_generated_image_url(image_url) else 0,
        1 if image_url or backup_url else 0,
        len(description),
        score,
    )


def filter_canonical_places(places: list[dict], city_name: str) -> list[dict]:
    allowed_places = canonical_place_names(city_name)
    if not allowed_places:
        return places

    allowed_keys = {normalize_key(name): name for name in allowed_places}
    best_by_place: dict[str, dict] = {}

    for place in places:
        place_name = str(field(place, "mekan_adi") or "").strip()
        place_key = normalize_key(place_name)
        if place_key not in allowed_keys:
            continue

        current = best_by_place.get(place_key)
        if current is None or place_quality(place) > place_quality(current):
            best_by_place[place_key] = place

    ordered_places: list[dict] = []
    for place_name in allowed_places:
        place = best_by_place.get(normalize_key(place_name))
        if place:
            ordered_places.append(place)
    return ordered_places


def merge_places_with_fallback(api_places: list[dict], city_name: str, lang: str) -> list[dict]:
    fallback_places = fallback_places_for_city(city_name, lang)
    if not fallback_places:
        return api_places

    api_by_key = {normalize_key(field(place, "mekan_adi")): place for place in api_places}
    fallback_by_key = {normalize_key(field(place, "mekan_adi")): place for place in fallback_places}
    ordered_names = canonical_place_names(city_name) or [str(field(place, "mekan_adi") or "") for place in fallback_places]

    merged_places: list[dict] = []
    for place_name in ordered_names:
        place_key = normalize_key(place_name)
        place = api_by_key.get(place_key) or fallback_by_key.get(place_key)
        if place:
            merged_places.append(place)

    return merged_places


def stars(score: object) -> str:
    try:
        bounded = max(0, min(5, int(score or 0)))
    except Exception:
        bounded = 0

    output = []
    for index in range(5):
        klass = "star-filled" if index < bounded else "star-empty"
        output.append(f'<span class="{klass}">★</span>')
    return "".join(output)


ui_lang = st.session_state.get("ui_lang", "tr")

st.set_page_config(
    page_title=t("page_title", ui_lang),
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #08111f !important;
    color: #d4dbe7 !important;
}

*, *::before, *::after { box-sizing: border-box; }
.block-container { padding: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"], footer, [data-testid="stToolbar"], .stDeployButton { display: none !important; }
section[data-testid="stSidebar"], div[data-testid="stDecoration"] { display: none !important; }

.navbar {
    position: sticky;
    top: 0;
    z-index: 999;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    background: rgba(8,17,31,0.88);
    backdrop-filter: blur(18px);
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.brand-icon {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: linear-gradient(135deg, #1ec67a, #0f9f6e);
}
.brand-text {
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #f8fafc;
}
.brand-text span { color: #4ade80; }
.brand-tag {
    font-size: 0.72rem;
    font-weight: 700;
    color: #86efac;
    border: 1px solid rgba(74,222,128,0.25);
    background: rgba(74,222,128,0.12);
    padding: 6px 12px;
    border-radius: 999px;
}

.hero {
    position: relative;
    overflow: hidden;
    padding: 96px 40px 72px;
    min-height: 440px;
    background:
        radial-gradient(circle at 75% 20%, rgba(16,185,129,0.14), transparent 28%),
        radial-gradient(circle at 20% 80%, rgba(56,189,248,0.12), transparent 26%),
        linear-gradient(180deg, #0b1525 0%, #09111d 100%);
}
.hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.35;
}
.hero-inner { position: relative; z-index: 1; }
.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #86efac;
    background: rgba(74,222,128,0.12);
    border: 1px solid rgba(74,222,128,0.2);
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.eyebrow::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
}
.hero-title {
    margin: 24px 0 18px;
    font-size: clamp(2.8rem, 6vw, 5rem);
    line-height: 0.98;
    font-weight: 900;
    letter-spacing: -0.05em;
    color: #ffffff;
}
.hero-title span { color: #4ade80; }
.hero-sub {
    max-width: 620px;
    color: #94a3b8;
    font-size: 1.05rem;
    line-height: 1.7;
}
.hero-stats {
    margin-top: 36px;
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
}
.hero-stat {
    min-width: 140px;
    padding: 18px 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
}
.hero-stat-value {
    color: #4ade80;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
}
.hero-stat-label {
    margin-top: 6px;
    color: #64748b;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.toolbar {
    padding: 28px 40px 24px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.toolbar-label {
    margin-bottom: 12px;
    color: #64748b;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
div[data-testid="stSelectbox"] > label { display: none !important; }
div[data-baseweb="select"] > div {
    min-height: 48px !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    background: #0f172a !important;
}
[data-baseweb="select"] span { color: #e2e8f0 !important; }

.city-panel-wrap { padding: 28px 40px 0; }
.city-panel {
    display: flex;
    gap: 24px;
    align-items: center;
    border-radius: 24px;
    border: 1px solid rgba(74,222,128,0.16);
    background: linear-gradient(135deg, rgba(16,185,129,0.10), rgba(15,23,42,0.92));
    padding: 30px 32px;
}
.city-icon {
    width: 68px;
    height: 68px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(74,222,128,0.10);
    border: 1px solid rgba(74,222,128,0.2);
    font-size: 30px;
}
.city-name {
    color: #f8fafc;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
}
.city-country {
    margin-top: 4px;
    color: #86efac;
    font-weight: 600;
}
.city-description {
    margin-top: 8px;
    max-width: 680px;
    color: #94a3b8;
    line-height: 1.7;
}
.city-count {
    margin-left: auto;
    padding: 12px 18px;
    border-radius: 16px;
    text-align: center;
    border: 1px solid rgba(74,222,128,0.18);
    background: rgba(74,222,128,0.10);
}
.city-count-value {
    color: #4ade80;
    font-size: 1.7rem;
    font-weight: 800;
}
.city-count-label {
    color: #86efac;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.section-head {
    margin-top: 8px;
    padding: 34px 40px 20px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.section-title {
    color: #f8fafc;
    font-size: 1.1rem;
    font-weight: 700;
}
.pill {
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.pill-count {
    color: #94a3b8;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
}
.pill-lang {
    color: #93c5fd;
    background: rgba(59,130,246,0.10);
    border: 1px solid rgba(59,130,246,0.18);
}
.pill-dynamic {
    color: #c4b5fd;
    background: rgba(167,139,250,0.10);
    border: 1px solid rgba(167,139,250,0.16);
}

.grid-wrap { padding: 28px 40px 80px; }
.card {
    background: #0d1727;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 22px;
    overflow: hidden;
    margin-bottom: 28px;
}
.card:hover { border-color: rgba(74,222,128,0.22); }
.card-media {
    position: relative;
    height: 236px;
    background: #111827;
    overflow: hidden;
}
.card-media img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}
.card-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(8,17,31,0.92), transparent 55%);
}
.card-badges {
    position: absolute;
    top: 14px;
    left: 14px;
    right: 14px;
    display: flex;
    justify-content: space-between;
}
.city-chip, .score-chip {
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 0.72rem;
    font-weight: 800;
}
.city-chip {
    color: #052e16;
    background: rgba(74,222,128,0.92);
}
.score-chip {
    color: #fef3c7;
    background: rgba(15,23,42,0.82);
    border: 1px solid rgba(250,204,21,0.18);
}
.card-title {
    position: absolute;
    left: 18px;
    right: 18px;
    bottom: 16px;
    color: #ffffff;
    font-size: 1.14rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.card-body { padding: 20px 22px 0; }
.card-description {
    color: #94a3b8;
    font-size: 0.9rem;
    line-height: 1.7;
}
.card-footer {
    margin-top: 16px;
    padding: 16px 22px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.stars { display: flex; gap: 3px; }
.star-filled { color: #f59e0b; font-size: 13px; }
.star-empty { color: #1e293b; font-size: 13px; }
.score-label {
    margin-left: 8px;
    color: #64748b;
    font-size: 0.78rem;
    font-weight: 700;
}
.card-tag {
    color: #c4b5fd;
    background: rgba(167,139,250,0.10);
    border: 1px solid rgba(167,139,250,0.18);
    padding: 5px 10px;
    border-radius: 10px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.message {
    margin: 40px;
    padding: 24px 28px;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.7;
}
.message-error {
    color: #fecaca;
    border: 1px solid rgba(248,113,113,0.18);
    background: rgba(127,29,29,0.16);
}
.message-warn {
    color: #fde68a;
    border: 1px solid rgba(250,204,21,0.18);
    background: rgba(120,53,15,0.18);
}

.footer {
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 34px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}
.footer-title { color: #94a3b8; font-size: 0.86rem; }
.footer-title strong { color: #cbd5e1; }
.footer-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.footer-tag {
    color: #94a3b8;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    padding: 5px 10px;
    border-radius: 10px;
    font-size: 0.68rem;
    font-weight: 700;
}

@media (max-width: 900px) {
    .navbar, .hero, .toolbar, .city-panel-wrap, .section-head, .grid-wrap, .footer { padding-left: 20px; padding-right: 20px; }
    .hero { padding-top: 72px; min-height: auto; }
    .city-panel { flex-direction: column; align-items: flex-start; }
    .city-count { margin-left: 0; }
}
</style>
""",
    unsafe_allow_html=True,
)


cities_tr_response = fetch_cities("tr")
cities_tr = cities_tr_response or []

if cities_tr_response is None and not FALLBACK_CONTENT_ITEMS:
    st.markdown(
        (
            f'<div class="message message-error"><strong>{safe_text(t("no_connection_title", ui_lang))}</strong> '
            f'{safe_text(t("no_connection_body", ui_lang))}</div>'
        ),
        unsafe_allow_html=True,
    )
    st.stop()

if not cities_tr and not FALLBACK_CONTENT_ITEMS:
    st.markdown(
        f'<div class="message message-warn">{safe_text(t("no_cities", ui_lang))}</div>',
        unsafe_allow_html=True,
    )
    st.stop()


if "ui_lang" not in st.session_state:
    st.session_state["ui_lang"] = "tr"


current_lang = st.session_state.get("ui_lang", "tr")
cities_ui = fetch_cities(current_lang) or []
city_options = build_city_options(cities_tr, cities_ui)
city_option_ids = [option["id"] for option in city_options]
if "selected_city_key" not in st.session_state or st.session_state["selected_city_key"] not in city_option_ids:
    st.session_state["selected_city_key"] = city_option_ids[0]
city_count = len(city_option_ids) if city_option_ids else len(CANONICAL_CITY_ORDER)
total_places = fetch_total_places()

city_label_map = {option["id"]: option["label"] for option in city_options}


st.markdown(
    f"""
<div class="navbar">
  <div class="brand">
    <div class="brand-icon">🗺️</div>
    <div class="brand-text">Gezi<span>Rehberi</span></div>
  </div>
  <div class="brand-tag">{safe_text(t("brand_tag", current_lang))}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="hero">
  <div class="hero-inner">
    <div class="eyebrow">{safe_text(t("eyebrow", current_lang))}</div>
    <div class="hero-title">{safe_text(t("hero_title", current_lang))}<br><span>{safe_text(t("hero_accent", current_lang))}</span></div>
    <div class="hero-sub">{safe_text(t("hero_sub", current_lang))}</div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="hero-stat-value">{city_count}</div><div class="hero-stat-label">{safe_text(t("stat_cities", current_lang))}</div></div>
      <div class="hero-stat"><div class="hero-stat-value">{total_places}</div><div class="hero-stat-label">{safe_text(t("stat_places", current_lang))}</div></div>
      <div class="hero-stat"><div class="hero-stat-value">2</div><div class="hero-stat-label">{safe_text(t("stat_languages", current_lang))}</div></div>
      <div class="hero-stat"><div class="hero-stat-value">{safe_text(t("stat_media_value", current_lang))}</div><div class="hero-stat-label">{safe_text(t("stat_media", current_lang))}</div></div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="toolbar">', unsafe_allow_html=True)
st.markdown(f'<div class="toolbar-label">{safe_text(t("toolbar_label", current_lang))}</div>', unsafe_allow_html=True)

col_city, col_lang, _ = st.columns([2.2, 1, 3.2])
with col_city:
    st.selectbox(
        t("city_label", current_lang),
        options=city_option_ids,
        format_func=lambda item: city_label_map.get(item, item),
        key="selected_city_key",
        label_visibility="collapsed",
    )
with col_lang:
    st.selectbox(
        t("language_label", current_lang),
        options=["tr", "en"],
        format_func=lambda item: t("lang_tr", current_lang) if item == "tr" else t("lang_en", current_lang),
        key="ui_lang",
        label_visibility="collapsed",
    )

st.markdown("</div>", unsafe_allow_html=True)


current_lang = st.session_state.get("ui_lang", "tr")
selected_city_key = st.session_state.get("selected_city_key", city_option_ids[0])
cities_ui = fetch_cities(current_lang) or []

selected_city_name = city_name_from_key(selected_city_key)
base_selected_city = city_by_name(cities_tr, selected_city_name) or city_by_name(cities_ui, selected_city_name)
selected_city = city_by_name(cities_ui, selected_city_name) or base_selected_city
selected_city_name = str(field(selected_city or {}, "ad") or "")
if not selected_city_name:
    selected_city_name = city_name_from_key(selected_city_key)
active_city_document_id = str(field(selected_city or {}, "documentId") or "")
selected_country_raw = str(field(selected_city or {}, "ulke") or "").strip() or fallback_country_for_city(selected_city_name, current_lang) or canonical_country_for_city(selected_city_name)
selected_info_raw = str(field(selected_city or {}, "kisa_bilgi") or "").strip()
if not selected_info_raw:
    fallback_city = city_by_name(cities_tr, selected_city_name)
    selected_info_raw = str(field(fallback_city or {}, "kisa_bilgi") or "").strip()
if not selected_info_raw:
    selected_info_raw = fallback_city_summary(selected_city_name, current_lang)
if not selected_info_raw and current_lang == "tr":
    selected_info_raw = canonical_city_summary_tr(selected_city_name)
selected_country = safe_text(selected_country_raw)
selected_info = safe_text(selected_info_raw)
selected_city_name_html = safe_text(selected_city_name)

api_places = filter_canonical_places(fetch_places(active_city_document_id, current_lang), selected_city_name) if active_city_document_id else []
places = merge_places_with_fallback(api_places, selected_city_name, current_lang)
place_count = len(places)

st.markdown(
    f"""
<div class="city-panel-wrap">
  <div class="city-panel">
    <div class="city-icon">📍</div>
    <div>
      <div class="city-name">{selected_city_name_html}</div>
      <div class="city-country">🌍 {selected_country}</div>
      <div class="city-description">{selected_info}</div>
    </div>
    <div class="city-count">
      <div class="city-count-value">{place_count}</div>
      <div class="city-count-label">{safe_text(t("city_badge", current_lang))}</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

lang_badge = "TR" if current_lang == "tr" else "EN"
st.markdown(
    f"""
<div class="section-head">
  <div class="section-title">{selected_city_name_html} · {safe_text(t("section_title", current_lang))}</div>
  <div class="pill pill-count">{place_count} {safe_text(t("stat_places", current_lang)).lower()}</div>
  <div class="pill pill-lang">{lang_badge}</div>
  <div class="pill pill-dynamic">{safe_text(t("section_dynamic", current_lang))}</div>
</div>
""",
    unsafe_allow_html=True,
)

if not places:
    st.markdown(
        f'<div class="message message-warn">{safe_text(t("no_places", current_lang))}</div>',
        unsafe_allow_html=True,
    )
    st.stop()


st.markdown('<div class="grid-wrap">', unsafe_allow_html=True)
columns = st.columns(2, gap="large")

for index, place in enumerate(places):
    place_name = str(field(place, "mekan_adi") or "Place")
    description = str(field(place, "aciklama") or "")
    score = field(place, "puan") or 0
    image_url = safe_image_url(place, place_name, selected_city_name)

    card_html = f"""
    <div class="card">
      <div class="card-media">
        <img src="{safe_text(image_url)}" alt="{safe_text(place_name)}" />
        <div class="card-overlay"></div>
        <div class="card-badges">
          <span class="city-chip">{selected_city_name_html.upper()}</span>
          <span class="score-chip">★ {safe_text(score)}/5</span>
        </div>
        <div class="card-title">{safe_text(place_name)}</div>
      </div>
      <div class="card-body">
        <div class="card-description">{safe_text(description)}</div>
      </div>
      <div class="card-footer">
        <div style="display:flex; align-items:center;">
          <div class="stars">{stars(score)}</div>
          <span class="score-label">{safe_text(score)} {safe_text(t("rating_suffix", current_lang))}</span>
        </div>
        <div class="card-tag">{safe_text(t("card_badge", current_lang))}</div>
      </div>
    </div>
    """

    with columns[index % 2]:
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
<div class="footer">
  <div class="footer-title">
    <strong>{safe_text(t("footer_title", current_lang))}</strong><br>
    {safe_text(t("footer_sub", current_lang))}
  </div>
  <div class="footer-tags">
    <span class="footer-tag">Headless CMS</span>
    <span class="footer-tag">REST API</span>
    <span class="footer-tag">Official Sources</span>
    <span class="footer-tag">Media Library</span>
    <span class="footer-tag">i18n</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
