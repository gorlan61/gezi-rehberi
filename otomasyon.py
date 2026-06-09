"""
BIP210 - Final Projesi: YZ Destekli Gezi Rehberi
otomasyon.py

Resmi kaynaklardan içerik çeker, metni zenginleştirir, çevirir,
görsel üretir ve Strapi'ye yayınlanmış içerik olarak senkronize eder.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import os
import re
import shutil
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests
from deep_translator import GoogleTranslator


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = ROOT_DIR / "sources.json"
IMAGE_DIR = ROOT_DIR / "gezi_gorseller"
BACKEND_DIR = ROOT_DIR / "gezi-rehberi-backend"
SQLITE_PATH = BACKEND_DIR / ".tmp" / "data.db"
BACKUP_DIR = BACKEND_DIR / ".tmp" / "backups"

REQUEST_TIMEOUT = 25
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt/{prompt}"
    "?width={width}&height={height}&nologo=true&seed={seed}"
)

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass(frozen=True)
class SourceRecord:
    city: str
    country: str
    city_summary_tr: str
    place: str
    source_url: str
    extractor: str
    score: int
    image_prompt: str


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def bootstrap_env() -> None:
    load_env_file(ROOT_DIR / ".env")
    load_env_file(ROOT_DIR / ".env.local")


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def normalize_text(value: str) -> str:
    text = html.unescape(value or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def trim_title(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"\s*\|\s*Kültür Portalı\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\|\s*Trabzon Ortahisar Belediyesi\s*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "item"


def stable_seed(value: str) -> int:
    return abs(hash(value)) % 10000


def record_key(record: SourceRecord) -> str:
    return f"{record.city}::{record.place}"


def image_seed_from_prompt(prompt: str) -> int:
    return stable_seed(prompt)


def pollinations_image_url(prompt: str, seed: int, width: int = 800, height: int = 600) -> str:
    encoded_prompt = requests.utils.quote(prompt)
    return POLLINATIONS_URL.format(
        prompt=encoded_prompt,
        seed=seed,
        width=width,
        height=height,
    )


def picsum_image_url(seed: int, width: int = 800, height: int = 600) -> str:
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"


def extract_meta_content(page_text: str, attr_name: str, attr_value: str) -> str:
    escaped = re.escape(attr_value)
    patterns = [
        rf'<meta[^>]+{attr_name}=["\']{escaped}["\'][^>]+content=["\'](.*?)["\']',
        rf'<meta[^>]+content=["\'](.*?)["\'][^>]+{attr_name}=["\']{escaped}["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return normalize_text(match.group(1))

    return ""


def strip_tags(fragment: str) -> str:
    without_noise = re.sub(
        r"<(script|style|noscript)[^>]*>.*?</\1>",
        " ",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", without_noise)
    return normalize_text(text)


def extract_tag_texts(page_text: str, tag_name: str) -> list[str]:
    pattern = rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>"
    matches = re.findall(pattern, page_text, flags=re.IGNORECASE | re.DOTALL)
    return [strip_tags(match) for match in matches]


def pick_best_description(candidates: list[str]) -> str:
    ignored_fragments = (
        "turkiye-kultur-portali",
        "trabzon-ortahisar-belediyesinin-resmi-web-sitesidir",
        "kesfetmek-icin-bir-sehir-secin",
    )
    cleaned: list[str] = []

    for candidate in candidates:
        text = normalize_text(candidate)
        if len(text) < 80:
            continue

        comparable = slugify(text)
        if any(fragment in comparable for fragment in ignored_fragments):
            continue

        cleaned.append(text)

    if not cleaned:
        return ""

    return max(cleaned, key=len)


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_kulturportali(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        headers=HTTP_HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    response.raise_for_status()
    page = response.text

    if response.url.rstrip("/") != url.rstrip("/"):
        raise RuntimeError("Kultur Portali sayfasi beklenmeyen bir adrese yonlendirildi.")

    title = (
        extract_meta_content(page, "property", "og:title")
        or extract_meta_content(page, "name", "twitter:title")
        or (extract_tag_texts(page, "h1") or [""])[0]
    )
    description = (
        extract_meta_content(page, "name", "description")
        or extract_meta_content(page, "property", "og:description")
    )

    if (
        not description
        or "turkiye-nin-kulturel-mirasini-kesfedin" in slugify(description)
        or slugify(description) == "turkiye"
    ):
        description = pick_best_description(extract_tag_texts(page, "p"))

    if not description:
        raise RuntimeError("Kultur Portali aciklamasi cikarilamadi.")

    return trim_title(title), description


def extract_goturkiye(url: str) -> tuple[str, str]:
    response = requests.get(url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
    if response.status_code == 403 and "Just a moment" in response.text:
        raise RuntimeError("GoTürkiye sayfası Cloudflare koruması nedeniyle erişilemedi.")

    response.raise_for_status()
    page = response.text

    title = (
        extract_meta_content(page, "property", "og:title")
        or extract_meta_content(page, "name", "twitter:title")
        or extract_meta_content(page, "name", "title")
    )
    description = (
        extract_meta_content(page, "name", "description")
        or extract_meta_content(page, "property", "og:description")
    )

    if not description:
        raise RuntimeError("GoTürkiye açıklaması çıkarılamadı.")

    return trim_title(title), description


def extract_generic_meta(url: str) -> tuple[str, str]:
    page = fetch_html(url)
    title = (
        extract_meta_content(page, "property", "og:title")
        or extract_meta_content(page, "name", "twitter:title")
        or (extract_tag_texts(page, "h1") or [""])[0]
    )
    description = (
        extract_meta_content(page, "name", "description")
        or extract_meta_content(page, "property", "og:description")
    )

    if (
        not description
        or len(description) < 80
        or "resmi web sitesidir" in normalize_text(description).casefold()
    ):
        description = pick_best_description(extract_tag_texts(page, "p"))

    if not description:
        raise RuntimeError("Meta description cikarilamadi.")

    return trim_title(title), description


EXTRACTORS = {
    "kulturportali": extract_kulturportali,
    "goturkiye": extract_goturkiye,
    "generic_meta": extract_generic_meta,
}


def load_sources(limit: int | None = None) -> list[SourceRecord]:
    raw_sources = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    records = [
        SourceRecord(
            city=item["city"],
            country=item["country"],
            city_summary_tr=item["city_summary_tr"],
            place=item["place"],
            source_url=item["source_url"],
            extractor=item["extractor"],
            score=int(item["score"]),
            image_prompt=item["image_prompt"],
        )
        for item in raw_sources
    ]

    if limit is not None:
        return records[:limit]

    return records


def build_city_map(sources: list[SourceRecord]) -> dict[str, dict[str, str]]:
    cities: dict[str, dict[str, str]] = {}
    for source in sources:
        cities.setdefault(
            source.city,
            {
                "country": source.country,
                "summary_tr": source.city_summary_tr,
            },
        )
    return cities


def google_news_al(city_name: str, place_name: str, max_haber: int = 3) -> list[str]:
    query = f"{city_name} {place_name} turizm"
    url = (
        "https://news.google.com/rss/search"
        f"?q={requests.utils.quote(query)}"
        "&hl=tr&gl=TR&ceid=TR:tr"
    )

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        print(f"  [WARN] Google News okunamadı: {exc}")
        return []

    headlines = []
    for entry in feed.entries[:max_haber]:
        title = normalize_text(entry.get("title", "").split(" - ")[0])
        if title:
            headlines.append(title)

    return headlines


def metni_ingilizceye_cevir(text_tr: str) -> str:
    try:
        return GoogleTranslator(source="tr", target="en").translate(text_tr)
    except Exception as exc:
        print(f"  [WARN] Ceviri hatasi: {exc}")
        return text_tr


def groq_ile_zenginlestir(
    api_key: str,
    place_name: str,
    city_name: str,
    source_description_tr: str,
    headlines: list[str],
) -> str:
    if not api_key:
        return source_description_tr

    if headlines:
        headlines_text = "\n".join(f"- {headline}" for headline in headlines)
        prompt = f"""
Sen bir gezi rehberi icerik yazarisin. Asagidaki resmi kaynak aciklamasini
ve guncel haber basliklarini birlestirerek ziyaretci dostu bir tanitim yazisi uret.

Mekan: {place_name}
Sehir: {city_name}
Resmi kaynak aciklamasi:
{source_description_tr}

Guncel haber basliklari:
{headlines_text}

Kurallar:
- Turkce yaz.
- 3 veya 4 cumle kullan.
- Abartili ve uydurma bilgi ekleme.
- Haberlerden sadece aciklamayi guclendiren kisimlari dogal bicimde kullan.
- Sadece nihai aciklamayi don.
"""
    else:
        prompt = f"""
Sen bir gezi rehberi icerik yazarisin. Asagidaki resmi kaynak aciklamasini
daha akici, bilgilendirici ve ziyaretci dostu hale getir.

Mekan: {place_name}
Sehir: {city_name}
Resmi kaynak aciklamasi:
{source_description_tr}

Kurallar:
- Turkce yaz.
- En fazla 3 cumle kullan.
- Sadece nihai aciklamayi don.
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt.strip()}],
        "max_tokens": 300,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return normalize_text(response.json()["choices"][0]["message"]["content"])
    except Exception as exc:
        print(f"  [WARN] Groq zenginlestirme basarisiz: {exc}")
        return source_description_tr


def image_path_for(record: SourceRecord) -> Path:
    file_name = f"{slugify(record.city)}-{slugify(record.place)}.jpg"
    return IMAGE_DIR / file_name


def backup_image_url_for_record(record: SourceRecord) -> str:
    seed = image_seed_from_prompt(record.image_prompt)
    return pollinations_image_url(record.image_prompt, seed)


def download_image(record: SourceRecord) -> Path | None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    target = image_path_for(record)

    if target.exists() and target.stat().st_size > 1024:
        return target

    seed = image_seed_from_prompt(record.image_prompt)
    image_url = pollinations_image_url(record.image_prompt, seed)

    try:
        response = requests.get(image_url, timeout=90)
        if response.status_code == 200 and len(response.content) > 1024:
            target.write_bytes(response.content)
            return target
        print(f"  [WARN] Pollinations basarisiz ({response.status_code}), fallback deneniyor.")
    except Exception as exc:
        print(f"  [WARN] Pollinations hatasi: {exc}")

    try:
        fallback_url = picsum_image_url(seed)
        response = requests.get(fallback_url, timeout=20, allow_redirects=True)
        response.raise_for_status()
        target.write_bytes(response.content)
        return target
    except Exception as exc:
        print(f"  [ERROR] Gorsel olusturulamadi: {exc}")
        return None


def prepare_local_images(sources: list[SourceRecord], enabled: bool) -> dict[str, Path | None]:
    if not enabled:
        return {record_key(source): None for source in sources}

    print("\n[IMG] Gorseller yerel cache'e hazirlaniyor...")
    results: dict[str, Path | None] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(download_image, source): source for source in sources}
        for future in concurrent.futures.as_completed(future_map):
            source = future_map[future]
            try:
                results[record_key(source)] = future.result()
            except Exception as exc:
                print(f"  [WARN] {source.place} gorseli hazirlanamadi: {exc}")
                results[record_key(source)] = None

    return results


def field(record: dict[str, Any] | None, key: str, default: Any = "") -> Any:
    if not isinstance(record, dict):
        return default
    if key in record:
        return record.get(key, default)
    attrs = record.get("attributes")
    if isinstance(attrs, dict):
        return attrs.get(key, default)
    return default


def media_id_from_entry(entry: dict[str, Any] | None) -> int | None:
    if not isinstance(entry, dict):
        return None

    media = entry.get("kapak_resmi")
    if isinstance(media, dict):
        if isinstance(media.get("id"), int):
            return media["id"]

        data = media.get("data")
        if isinstance(data, dict) and isinstance(data.get("id"), int):
            return data["id"]

    attrs = entry.get("attributes")
    if isinstance(attrs, dict):
        media = attrs.get("kapak_resmi")
        if isinstance(media, dict):
            data = media.get("data")
            if isinstance(data, dict) and isinstance(data.get("id"), int):
                return data["id"]

    return None


def normalize_media_url(url: str | None, base_url: str) -> str | None:
    if not url:
        return None

    raw = str(url).strip()
    if not raw:
        return None
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("/"):
        return f"{base_url.rstrip('/')}{raw}"

    parsed = urlparse(raw)
    base_host = urlparse(base_url).netloc.lower()
    if parsed.netloc.lower() in {"localhost:1337", "127.0.0.1:1337"} and base_host not in {
        "localhost:1337",
        "127.0.0.1:1337",
    }:
        return f"{base_url.rstrip('/')}{parsed.path}"

    return raw


def media_url_from_entry(entry: dict[str, Any] | None, base_url: str) -> str | None:
    if not isinstance(entry, dict):
        return None

    media = entry.get("kapak_resmi")
    if isinstance(media, dict):
        if media.get("url"):
            return normalize_media_url(media.get("url"), base_url)

        formats = media.get("formats") or {}
        for size in ("large", "medium", "small", "thumbnail"):
            candidate = (formats.get(size) or {}).get("url")
            if candidate:
                return normalize_media_url(candidate, base_url)

        data = media.get("data")
        if isinstance(data, dict):
            if data.get("url"):
                return normalize_media_url(data.get("url"), base_url)
            attrs = data.get("attributes") or {}
            if attrs.get("url"):
                return normalize_media_url(attrs.get("url"), base_url)

    attrs = entry.get("attributes")
    if isinstance(attrs, dict):
        media = attrs.get("kapak_resmi") or {}
        if isinstance(media, dict):
            data = media.get("data")
            if isinstance(data, dict):
                if data.get("url"):
                    return normalize_media_url(data.get("url"), base_url)
                nested_attrs = data.get("attributes") or {}
                if nested_attrs.get("url"):
                    return normalize_media_url(nested_attrs.get("url"), base_url)

    return None


def is_same_strapi_host(url: str, base_url: str) -> bool:
    try:
        return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()
    except Exception:
        return False


def remote_image_available(url: str) -> bool:
    if not url:
        return False

    try:
        response = requests.get(url, timeout=12, stream=True)
        content_type = response.headers.get("content-type", "").lower()
        return response.status_code == 200 and "image" in content_type
    except Exception:
        return False


class StrapiClient:
    def __init__(self, base_url: str, email: str = "", password: str = "", token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

        auth_token = token or self._login(email, password)
        self.session.headers["Authorization"] = f"Bearer {auth_token}"

    def _login(self, email: str, password: str) -> str:
        if not email or not password:
            raise RuntimeError(
                "Strapi yazma islemleri icin STRAPI_EMAIL + STRAPI_PASSWORD veya STRAPI_TOKEN gerekli."
            )

        payload = {"identifier": email, "password": password}
        response = requests.post(
            f"{self.base_url}/api/auth/local",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        jwt = data.get("jwt")
        if not jwt:
            raise RuntimeError("JWT alinamadi.")
        return jwt

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        response = self.session.request(method, f"{self.base_url}{path}", timeout=REQUEST_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response

    def find_many(
        self,
        collection: str,
        filters: dict[str, Any] | None = None,
        locale: str = "tr",
        populate: str | None = None,
        status: str = "published",
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "locale": locale,
            "status": status,
            "pagination[pageSize]": page_size,
        }
        if populate:
            params["populate"] = populate
        if filters:
            params.update(filters)

        response = self.request("GET", f"/api/{collection}", params=params)
        return response.json().get("data", [])

    def find_one(
        self,
        collection: str,
        filters: dict[str, Any],
        locale: str = "tr",
        populate: str | None = None,
        status: str = "published",
    ) -> dict[str, Any] | None:
        entries = self.find_many(
            collection=collection,
            filters=filters,
            locale=locale,
            populate=populate,
            status=status,
            page_size=1,
        )
        return entries[0] if entries else None

    def upsert_document(
        self,
        collection: str,
        lookup_filters: dict[str, Any],
        data: dict[str, Any],
        locale: str,
        document_id: str | None = None,
        populate: str | None = None,
    ) -> dict[str, Any]:
        existing = self.find_one(collection, lookup_filters, locale=locale, populate=populate)
        target_document_id = field(existing, "documentId") if existing else document_id
        params = {"locale": locale, "status": "published"}
        payload = {"data": data}

        if target_document_id:
            response = self.request(
                "PUT",
                f"/api/{collection}/{target_document_id}",
                params=params,
                json=payload,
            )
        else:
            response = self.request(
                "POST",
                f"/api/{collection}",
                params=params,
                json=payload,
            )

        return response.json()["data"]

    def upload_file(self, file_path: Path) -> int | None:
        headers = {"Authorization": self.session.headers["Authorization"]}
        with file_path.open("rb") as file_handle:
            response = requests.post(
                f"{self.base_url}/api/upload",
                headers=headers,
                files={"files": (file_path.name, file_handle, "image/jpeg")},
                timeout=60,
            )

        response.raise_for_status()
        payload = response.json()
        return payload[0]["id"] if payload else None

    def list_document_ids(self, collection: str) -> list[str]:
        entries = self.find_many(collection, locale="tr", status="published", page_size=200)
        return sorted({field(entry, "documentId") for entry in entries if field(entry, "documentId")})

    def delete_document(self, collection: str, document_id: str) -> None:
        self.request("DELETE", f"/api/{collection}/{document_id}")

    def list_files(self) -> list[dict[str, Any]]:
        response = self.request("GET", "/api/upload/files")
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def delete_file(self, file_id: int) -> None:
        self.request("DELETE", f"/api/upload/files/{file_id}")


def backup_sqlite_db() -> Path | None:
    if not SQLITE_PATH.exists():
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"data_{time.strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(SQLITE_PATH, backup_path)
    return backup_path


def reset_strapi_content(client: StrapiClient) -> None:
    backup_path = backup_sqlite_db()
    if backup_path:
        print(f"[RESET] SQLite yedegi olusturuldu: {backup_path}")

    for collection in ("places", "cities"):
        document_ids = client.list_document_ids(collection)
        for document_id in document_ids:
            client.delete_document(collection, document_id)
        print(f"[RESET] {collection} koleksiyonundan {len(document_ids)} dokuman silindi.")

    files = client.list_files()
    deleted = 0
    for file_item in files:
        file_id = file_item.get("id")
        if isinstance(file_id, int):
            client.delete_file(file_id)
            deleted += 1

    print(f"[RESET] Media Library icinden {deleted} dosya silindi.")


def extract_source_content(record: SourceRecord) -> tuple[str, str]:
    extractor = EXTRACTORS.get(record.extractor)
    if extractor is None:
        raise RuntimeError(f"Bilinmeyen extractor: {record.extractor}")
    return extractor(record.source_url)


def verify_groq(api_key: str) -> bool:
    if not api_key:
        return False

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": "Merhaba"}],
        "max_tokens": 8,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return True
    except Exception:
        return False


def sync_cities(
    client: StrapiClient,
    city_map: dict[str, dict[str, str]],
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}

    for city_name, city_data in city_map.items():
        summary_tr = city_data["summary_tr"]
        summary_en = metni_ingilizceye_cevir(summary_tr)

        lookup = {"filters[ad][$eq]": city_name}
        tr_entry = client.upsert_document(
            collection="cities",
            lookup_filters=lookup,
            data={
                "ad": city_name,
                "ulke": city_data["country"],
                "kisa_bilgi": summary_tr,
            },
            locale="tr",
        )
        document_id = field(tr_entry, "documentId")
        en_entry = client.upsert_document(
            collection="cities",
            lookup_filters=lookup,
            data={
                "ad": city_name,
                "ulke": city_data["country"],
                "kisa_bilgi": summary_en,
            },
            locale="en",
            document_id=document_id,
        )

        results[city_name] = {
            "document_id": document_id,
            "tr_id": field(tr_entry, "id"),
            "en_id": field(en_entry, "id"),
        }

    return results


def sync_places(
    client: StrapiClient,
    sources: list[SourceRecord],
    city_state: dict[str, dict[str, Any]],
    local_images: dict[str, Path | None],
    groq_api_key: str,
) -> tuple[int, int]:
    success = 0
    failed = 0

    for index, record in enumerate(sources, start=1):
        print(f"\n[{index}/{len(sources)}] {record.place} - {record.city}")
        try:
            source_title, description_tr = extract_source_content(record)
            print(f"  [OK] Kaynak okundu: {source_title or record.place}")
            headlines = google_news_al(record.city, record.place)
            if headlines:
                print(f"  [OK] {len(headlines)} guncel haber bulundu.")
            enriched_tr = groq_ile_zenginlestir(
                groq_api_key,
                record.place,
                record.city,
                description_tr,
                headlines,
            )
            description_en = metni_ingilizceye_cevir(enriched_tr)

            city_info = city_state[record.city]
            image_seed = image_seed_from_prompt(record.image_prompt)
            backup_url = backup_image_url_for_record(record)
            lookup = {
                "filters[mekan_adi][$eq]": record.place,
                "filters[city][documentId][$eq]": city_info["document_id"],
            }
            existing_tr = client.find_one("places", lookup, locale="tr", populate="*")
            document_id = field(existing_tr, "documentId") if existing_tr else None
            media_id = media_id_from_entry(existing_tr)
            media_url = media_url_from_entry(existing_tr, client.base_url)
            needs_media_refresh = media_id is None

            if media_url and is_same_strapi_host(media_url, client.base_url) and not remote_image_available(
                media_url
            ):
                print("  [WARN] Mevcut Strapi gorseli erisilemiyor, yeniden yukleme denenecek.")
                needs_media_refresh = True

            if needs_media_refresh:
                image_path = local_images.get(record_key(record))
                if image_path:
                    media_id = client.upload_file(image_path)
                    print(f"  [OK] Gorsel yuklendi: {image_path.name}")

            tr_payload = {
                "mekan_adi": record.place,
                "aciklama": enriched_tr,
                "puan": record.score,
                "gorsel_prompt": record.image_prompt,
                "gorsel_seed": image_seed,
                "gorsel_yedek_url": backup_url,
                "city": city_info["tr_id"],
            }
            if media_id is not None:
                tr_payload["kapak_resmi"] = media_id

            tr_entry = client.upsert_document(
                collection="places",
                lookup_filters=lookup,
                data=tr_payload,
                locale="tr",
                document_id=document_id,
                populate="*",
            )
            document_id = field(tr_entry, "documentId")

            en_payload = {
                "mekan_adi": record.place,
                "aciklama": description_en,
                "puan": record.score,
                "gorsel_prompt": record.image_prompt,
                "gorsel_seed": image_seed,
                "gorsel_yedek_url": backup_url,
                "city": city_info["en_id"] or city_info["tr_id"],
            }
            if media_id is not None:
                en_payload["kapak_resmi"] = media_id

            client.upsert_document(
                collection="places",
                lookup_filters=lookup,
                data=en_payload,
                locale="en",
                document_id=document_id,
                populate="*",
            )

            print("  [OK] TR ve EN lokalizasyonlari senkronize edildi.")
            success += 1
        except Exception as exc:
            print(f"  [ERROR] {record.place} islenemedi: {exc}")
            failed += 1

    return success, failed


def dry_run_preview(sources: list[SourceRecord], groq_api_key: str) -> tuple[int, int]:
    success = 0
    failed = 0

    for index, record in enumerate(sources, start=1):
        print(f"\n[DRY-RUN {index}/{len(sources)}] {record.place} - {record.city}")
        try:
            source_title, description_tr = extract_source_content(record)
            headlines = google_news_al(record.city, record.place)
            enriched_tr = groq_ile_zenginlestir(
                groq_api_key,
                record.place,
                record.city,
                description_tr,
                headlines,
            )
            description_en = metni_ingilizceye_cevir(enriched_tr)

            print(f"  Kaynak: {source_title or record.place}")
            print(f"  URL: {record.source_url}")
            print(f"  Extractor: {record.extractor}")
            print(f"  Gorsel promptu: {record.image_prompt}")
            print(f"  Haber sayisi: {len(headlines)}")
            print(f"  TR aciklama: {enriched_tr[:220]}")
            print(f"  EN aciklama: {description_en[:220]}")
            success += 1
        except Exception as exc:
            print(f"  [ERROR] Dry-run basarisiz: {exc}")
            failed += 1

    return success, failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BIP210 gezi rehberi otomasyon motoru")
    parser.add_argument("--dry-run", action="store_true", help="Strapi'ye yazmadan akisi dogrular")
    parser.add_argument("--limit", type=int, default=None, help="Ilk N kaynagi isler")
    parser.add_argument(
        "--reset-strapi",
        action="store_true",
        help="Mevcut city/place icerigini ve medyayi temizler, sonra yeniden senkronize eder",
    )
    return parser.parse_args()


def main() -> None:
    bootstrap_env()
    args = parse_args()

    if args.dry_run and args.reset_strapi:
        raise SystemExit("--dry-run ve --reset-strapi birlikte kullanilamaz.")

    sources = load_sources(limit=args.limit)
    city_map = build_city_map(sources)

    strapi_url = get_env("STRAPI_URL", "http://localhost:1337")
    strapi_email = get_env("STRAPI_EMAIL")
    strapi_password = get_env("STRAPI_PASSWORD")
    strapi_token = get_env("STRAPI_TOKEN")
    groq_api_key = get_env("GROQ_API_KEY")

    print("=" * 72)
    print(" BIP210 | YZ Destekli Gezi Rehberi Otomasyon Motoru")
    print("=" * 72)
    print(f"Kaynak sayisi: {len(sources)}")
    print(f"Dry run: {'evet' if args.dry_run else 'hayir'}")
    print(f"Groq durumu: {'hazir' if verify_groq(groq_api_key) else 'devre disi veya ulasilamiyor'}")

    if args.dry_run:
        success, failed = dry_run_preview(sources, groq_api_key)
        print("\n" + "=" * 72)
        print(f"Dry-run tamamlandi | basarili: {success} | basarisiz: {failed}")
        print("=" * 72)
        return

    client = StrapiClient(
        base_url=strapi_url,
        email=strapi_email,
        password=strapi_password,
        token=strapi_token,
    )

    print("\n[AUTH] Strapi yetkilendirmesi basarili.")
    if args.reset_strapi:
        reset_strapi_content(client)

    local_images = prepare_local_images(sources, enabled=True)
    city_state = sync_cities(client, city_map)
    success, failed = sync_places(client, sources, city_state, local_images, groq_api_key)

    print("\n" + "=" * 72)
    print(f"Senkronizasyon tamamlandi | basarili: {success} | basarisiz: {failed}")
    print(f"Gorsel cache klasoru: {IMAGE_DIR}")
    print("=" * 72)


if __name__ == "__main__":
    main()
