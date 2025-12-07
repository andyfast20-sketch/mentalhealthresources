import json
import os
import sqlite3
from datetime import datetime
from html.parser import HTMLParser
import re
from pathlib import Path
import time
from werkzeug.utils import secure_filename
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - fallback loader
    def load_dotenv(dotenv_path=None):
        path = Path(dotenv_path) if dotenv_path else Path(".env")
        if not path.exists():
            return
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
from flask import Flask, redirect, render_template, request, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOCAL_DATA_DIR = Path.home() / ".mentalhealthresources"
LEGACY_LOCAL_DATA_DIR = BASE_DIR / "local_data"
MEDIA_UPLOADS_DIR = BASE_DIR / "static" / "uploads"
BOOKS_FILE = DATA_DIR / "books.json"
LOCAL_BOOKS_FILE = LOCAL_DATA_DIR / "books.json"
LEGACY_LOCAL_BOOKS_FILE = LEGACY_LOCAL_DATA_DIR / "books.json"
CALMING_COUNTS_FILE = LOCAL_DATA_DIR / "calming_counts.json"
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "YOUR_TOKEN_HERE")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "YOUR_ACCOUNT_ID")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID", "YOUR_DATABASE_ID")
D1_BASE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"
)


def _d1_configured():
    placeholders = {
        "YOUR_TOKEN": CF_API_TOKEN,
        "YOUR_ACCOUNT": CF_ACCOUNT_ID,
        "YOUR_DATABASE": CF_D1_DATABASE_ID,
    }

    if not all(placeholders.values()):
        return False

    return not any(placeholder in value for placeholder, value in placeholders.items())


D1_CONFIGURED = _d1_configured()
D1_AVAILABLE = True
LOCAL_FALLBACK_DB = LOCAL_DATA_DIR / "d1_fallback.sqlite"
SQLITE_TIMEOUT = 30
CONSTRUCTION_BANNER_KEY = "construction_banner"
DEEPSEEK_SETTING_KEY = "deepseek_api_key"
CHAT_ENABLED_KEY = "chat_enabled"
CHAT_NEXT_SESSION_KEY = "chat_next_session"
CHAT_TOPIC_KEY = "chat_topic"
CHAT_RULES_KEY = "chat_rules"
CHAT_BLOCKED_WORDS_KEY = "chat_blocked_words"
CHAT_BLOCK_ACTION_KEY = "chat_block_action"


DEFAULT_BOOKS = [
    {
        "title": "Atlas of the Heart",
        "author": "Brené Brown",
        "description": "A compassionate guide through 87 emotions and experiences, helping readers name what they feel and find language for connection.",
        "affiliate_url": "https://amzn.to/3K6C0Lk",
        "cover_url": "https://m.media-amazon.com/images/I/71+Jx1gIdwL._SL1500_.jpg",
    },
    {
        "title": "Maybe You Should Talk to Someone",
        "author": "Lori Gottlieb",
        "description": "A therapist pulls back the curtain on her own sessions and reminds us therapy is a courageous act of care.",
        "affiliate_url": "https://amzn.to/4bj8QEv",
        "cover_url": "https://m.media-amazon.com/images/I/81PxgyrpFZL._SL1500_.jpg",
    },
    {
        "title": "The Body Keeps the Score",
        "author": "Bessel van der Kolk",
        "description": "Evidence-based insights on how trauma lives in the body and the healing pathways that restore safety.",
        "affiliate_url": "https://amzn.to/3yOaYDh",
        "cover_url": "https://m.media-amazon.com/images/I/81dQwQlmAXL._SL1500_.jpg",
    },
    {
        "title": "Set Boundaries, Find Peace",
        "author": "Nedra Glover Tawwab",
        "description": "Practical scripts and exercises to set limits with compassion, reduce overwhelm, and protect your energy.",
        "affiliate_url": "https://amzn.to/3YVn1ch",
        "cover_url": "https://m.media-amazon.com/images/I/71m3C1AI+8L._SL1500_.jpg",
    },
    {
        "title": "Burnout: The Secret to Unlocking the Stress Cycle",
        "author": "Emily Nagoski & Amelia Nagoski",
        "description": "Research-backed strategies for completing the stress cycle, especially for caregivers and high achievers.",
        "affiliate_url": "https://amzn.to/3WklwZg",
        "cover_url": "https://m.media-amazon.com/images/I/71A4HVWjQBL._SL1500_.jpg",
    },
    {
        "title": "Emotional Agility",
        "author": "Susan David",
        "description": "Science-backed tools to navigate emotions with curiosity and courage instead of getting stuck.",
        "affiliate_url": "https://amzn.to/3WOO5RW",
        "cover_url": "https://m.media-amazon.com/images/I/71kN7vR-4cL._SL1500_.jpg",
    },
    {
        "title": "The Happiness Trap",
        "author": "Russ Harris",
        "description": "An introduction to Acceptance and Commitment Therapy that shows how to unhook from unhelpful thoughts.",
        "affiliate_url": "https://amzn.to/4c8gZNh",
        "cover_url": "https://m.media-amazon.com/images/I/71K9CsgY1QL._SL1500_.jpg",
    },
    {
        "title": "What Happened to You?",
        "author": "Bruce D. Perry & Oprah Winfrey",
        "description": "A compassionate conversation about trauma, resilience, and the healing power of understanding.",
        "affiliate_url": "https://amzn.to/3KMV3r9",
        "cover_url": "https://m.media-amazon.com/images/I/81xG0LknQ+L._SL1500_.jpg",
    },
    {
        "title": "The Comfort Book",
        "author": "Matt Haig",
        "description": "Short, soothing reflections and reminders that hope can be found in small, everyday moments.",
        "affiliate_url": "https://amzn.to/3KJP3qH",
        "cover_url": "https://m.media-amazon.com/images/I/71lz6h6hysL._SL1500_.jpg",
    },
    {
        "title": "Self-Compassion",
        "author": "Kristin Neff",
        "description": "Practical exercises for treating yourself with the same kindness you offer others.",
        "affiliate_url": "https://amzn.to/3WUgJRl",
        "cover_url": "https://m.media-amazon.com/images/I/71pPpM9VfNL._SL1500_.jpg",
    },
]

DEFAULT_DID_YOU_KNOW_ITEMS = [
    {
        "headline": "In a mental health crisis, you can call 111 any time.",
        "detail": "NHS 111 has trained teams available 24/7 to help you get urgent mental health support and signpost local services.",
        "cta_label": "Call 111", 
        "cta_url": "tel:111",
    },
    {
        "headline": "You can text 'SHOUT' to 85258 for free, day or night.",
        "detail": "A trained volunteer will reply to guide you to calm and help you find a next step when things feel overwhelming.",
        "cta_label": "Text SHOUT to 85258",
        "cta_url": "sms:85258",
    },
    {
        "headline": "Urgent help is available without an appointment.",
        "detail": "Walk-in crisis cafés and safe havens are open in many areas. Try searching your town name and “crisis café” to find a nearby space.",
        "cta_label": "Find a crisis café",
        "cta_url": "https://www.google.com/search?q=crisis+cafe+near+me",
    },
]


def ensure_local_data_dir():
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_media_uploads_dir():
    MEDIA_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def store_uploaded_media(upload):
    if not upload or not upload.filename:
        return None

    ensure_media_uploads_dir()
    filename = secure_filename(upload.filename)
    if not filename:
        return None

    timestamp = int(time.time())
    saved_name = f"{timestamp}_{filename}"
    destination = MEDIA_UPLOADS_DIR / saved_name
    upload.save(destination)
    return f"/static/uploads/{saved_name}"


def remove_local_media_file(url):
    if not url:
        return

    relative_url = url.lstrip("/")
    candidate_path = BASE_DIR / relative_url

    try:
        uploads_root = MEDIA_UPLOADS_DIR.resolve()
        target_path = candidate_path.resolve()
        if uploads_root in target_path.parents or target_path == uploads_root:
            if target_path.exists():
                target_path.unlink()
    except FileNotFoundError:
        return


def load_books_file():
    ensure_local_data_dir()
    if not LOCAL_BOOKS_FILE.exists():
        return None

    try:
        with LOCAL_BOOKS_FILE.open() as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        return None

    return None


def slugify(value):
    return "-".join(value.lower().split())


def book_slug(book, fallback=None):
    title = book.get("title", "").strip()
    author = book.get("author", "").strip()
    combined = "-".join(filter(None, [title, author]))
    slug = slugify(combined)
    return slug or (fallback or "book")


def normalize_url(url):
    if not url:
        return ""
    url = url.strip()
    if url.startswith(("http://", "https://", "/", "data:")):
        return url
    return f"https://{url}"


def normalize_support_link(url):
    if not url:
        return ""

    url = url.strip()
    if url.startswith(("http://", "https://", "tel:", "sms:", "mailto:")):
        return url

    return f"https://{url}"


class MetaTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta_tags = []
        self.title_chunks = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "meta":
            self.meta_tags.append({key.lower(): value for key, value in attrs if value})
        elif tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_chunks.append(data)


def parse_meta_tags(html):
    parser = MetaTagParser()
    parser.feed(html)
    return parser.meta_tags, "".join(parser.title_chunks).strip()


def first_meta_content(meta_tags, names):
    names = {name.lower() for name in names}
    for tag in meta_tags:
        tag_name = tag.get("name") or tag.get("property")
        if tag_name and tag_name.lower() in names:
            content = tag.get("content")
            if content:
                return content.strip()
    return ""


def extract_html_charset(headers, default="utf-8"):
    content_type = headers.get("Content-Type")
    if not content_type:
        return default

    parts = content_type.split("charset=")
    if len(parts) == 2:
        charset = parts[1].split(";")[0].strip()
        if charset:
            return charset

    return default


def create_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(options=chrome_options)


def fetch_html_with_browser(url):
    """Fetch page HTML using a real browser to bypass strict blocking."""

    driver = None
    try:
        driver = create_selenium_driver()
        driver.get(url)
        time.sleep(4)
        return driver.page_source, None
    except Exception as exc:  # pragma: no cover - depends on browser availability
        return None, str(exc)
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass


def extract_bookshop_title(driver):
    try:
        element = driver.find_element(By.CSS_SELECTOR, "h1[data-testid='book-title']")
        if element and element.text.strip():
            return element.text.strip()
    except Exception:
        pass

    selectors = [
        "h1.title",
        "h1.product-title",
        ".product-title h1",
        "h1[itemprop='name']",
        "meta[property='og:title']",
        "title",
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                text = element.text.strip()
                if not text and selector == "meta[property='og:title']":
                    text = element.get_attribute("content", "").strip()
                if text:
                    text = text.replace("| UK bookshop.org", "").strip()
                    text = text.replace("UK Bookshop -", "").strip()
                    text = text.split("|")[0].strip()
                    text = text.split("-")[0].strip()
                    return text
        except Exception:
            continue

    try:
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        for h1 in h1_elements:
            text = h1.text.strip()
            if text and 3 < len(text) < 200:
                if not text.lower().startswith(("http", "home", "shop", "about", "contact")):
                    return text
    except Exception:
        pass

    page_title = driver.title.strip()
    if page_title:
        page_title = page_title.replace("| UK bookshop.org", "").strip()
        page_title = page_title.replace("UK Bookshop -", "").strip()
        page_title = page_title.split("|")[0].strip()
        page_title = page_title.split("-")[0].strip()
        return page_title

    return ""


def extract_bookshop_author(driver):
    selectors = [
        "a[href*='/search?keywords=']",
        ".author",
        ".book-author",
        "[itemprop='author']",
        "a[href*='/author/']",
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                text = element.text.strip()
                if text:
                    text = text.replace("(Author)", "").strip()
                    text = text.replace("(author)", "").strip()
                    text = text.replace("By ", "").strip()
                    return text
        except Exception:
            continue

    return ""


def extract_bookshop_description(driver):
    selectors = [
        "div.bulleted-lists[dir='ltr']",
        ".description",
        ".book-description",
        "[itemprop='description']",
        ".product-description",
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                text = element.text.strip()
                if text:
                    return text
        except Exception:
            continue

    return ""


def extract_bookshop_image(driver):
    selectors = [
        "img[alt*='bookcover']",
        "img[alt*='cover']",
        ".book-cover img",
        "[itemprop='image']",
        "img.product-image",
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                srcset = element.get_attribute("srcset")
                if srcset:
                    urls = [url.strip().split(" ")[0] for url in srcset.split(",") if url.strip()]
                    if urls:
                        return urls[-1]

                src = element.get_attribute("src")
                if src:
                    return src
        except Exception:
            continue

    return ""


def scrape_bookshop_metadata(book_url):
    driver = None
    try:
        driver = create_selenium_driver()
    except Exception as exc:
        return None, f"Failed to initialize Chrome driver: {exc}"

    try:
        driver.get(book_url)
        time.sleep(4)

        title = extract_bookshop_title(driver)
        author = extract_bookshop_author(driver) or "Unknown author"
        description = extract_bookshop_description(driver) or "Description not available yet."
        cover_url = extract_bookshop_image(driver)

        if not title:
            return None, "Could not find a title on that page. Please add the book manually."

        return (
            {
                "title": title,
                "author": author,
                "description": description,
                "affiliate_url": book_url,
                "cover_url": normalize_url(cover_url) if cover_url else "",
            },
            None,
        )
    except Exception as exc:
        return None, f"Error while scraping book details: {exc}"
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def scrape_book_metadata(book_url):
    normalized_url = normalize_url(book_url)
    if not normalized_url:
        return None, "Please provide a book URL."

    if "uk.bookshop.org" in normalized_url:
        return scrape_bookshop_metadata(normalized_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    }
    request = urlrequest.Request(normalized_url, headers=headers)

    html = None

    try:
        with urlrequest.urlopen(request, timeout=10) as response:  # nosec B310
            charset = extract_html_charset(response.headers)
            html = response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        if exc.code in {403, 429}:
            html, browser_error = fetch_html_with_browser(normalized_url)
            if not html:
                return None, (
                    f"Unable to fetch book page (HTTP {exc.code}) and browser fallback failed: {browser_error}"
                )
        else:
            return None, f"Unable to fetch book page: {exc}"
    except (URLError, TimeoutError, UnicodeDecodeError) as exc:
        return None, f"Unable to fetch book page: {exc}"

    if html is None:
        return None, "Unable to fetch book page: Unknown error"

    meta_tags, title_from_markup = parse_meta_tags(html)

    title = first_meta_content(meta_tags, {"og:title", "twitter:title", "title"}) or title_from_markup
    description = first_meta_content(meta_tags, {"og:description", "description"})
    author = first_meta_content(meta_tags, {"author", "book:author", "og:book:author"})
    cover_url = first_meta_content(meta_tags, {"og:image", "twitter:image", "image"}) or ""

    if not title:
        return None, "Could not find a title on that page. Please add the book manually."

    book = {
        "title": title,
        "author": author or "Unknown author",
        "description": description or "Description not available yet.",
        "affiliate_url": normalized_url,
        "cover_url": normalize_url(cover_url) if cover_url.startswith("http") else "",
    }

    return book, None


def ensure_fallback_db():
    ensure_local_data_dir()
    if LOCAL_FALLBACK_DB.exists():
        return

    connection = sqlite3.connect(LOCAL_FALLBACK_DB, timeout=SQLITE_TIMEOUT)
    connection.close()


def open_local_db(row_factory=None):
    """Open a connection to the local fallback database with a generous timeout."""

    ensure_fallback_db()
    connection = sqlite3.connect(LOCAL_FALLBACK_DB, timeout=SQLITE_TIMEOUT)
    if row_factory:
        connection.row_factory = row_factory
    return connection


def get_table_columns(connection, table_name):
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def migrate_charities_schema_local(connection):
    columns = get_table_columns(connection, "charities")

    migrations = []
    if "website_url" not in columns:
        migrations.append("ALTER TABLE charities ADD COLUMN website_url TEXT NOT NULL DEFAULT ''")
    if "created_at" not in columns:
        migrations.append("ALTER TABLE charities ADD COLUMN created_at DATETIME")
    if "telephone" not in columns:
        migrations.append("ALTER TABLE charities ADD COLUMN telephone TEXT DEFAULT ''")
    for contact_column in ["contact_email", "text_number", "helpline_hours"]:
        if contact_column not in columns:
            migrations.append(
                f"ALTER TABLE charities ADD COLUMN {contact_column} TEXT DEFAULT ''"
            )
    for feature_column in [
        "has_helpline",
        "has_volunteers",
        "has_crisis_info",
        "has_text_support",
        "has_email_support",
        "has_live_chat",
    ]:
        if feature_column not in columns:
            migrations.append(
                f"ALTER TABLE charities ADD COLUMN {feature_column} INTEGER NOT NULL DEFAULT 0"
            )

    for statement in migrations:
        connection.execute(statement)

    if "created_at" not in columns:
        connection.execute(
            "UPDATE charities SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )


def migrate_charities_schema_remote():
    if not D1_CONFIGURED:
        return

    try:
        columns = {row.get("name") for row in d1_query("PRAGMA table_info(charities)")}
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Skipping D1 schema migration; unable to inspect schema. Details: {exc}")
        return

    if "website_url" not in columns:
        d1_query("ALTER TABLE charities ADD COLUMN website_url TEXT NOT NULL DEFAULT ''")
    if "created_at" not in columns:
        d1_query("ALTER TABLE charities ADD COLUMN created_at DATETIME")
        d1_query(
            "UPDATE charities SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )
    if "telephone" not in columns:
        d1_query("ALTER TABLE charities ADD COLUMN telephone TEXT DEFAULT ''")
    for contact_column in ["contact_email", "text_number", "helpline_hours"]:
        if contact_column not in columns:
            d1_query(
                f"ALTER TABLE charities ADD COLUMN {contact_column} TEXT DEFAULT ''"
        )
    for feature_column in [
        "has_helpline",
        "has_volunteers",
        "has_crisis_info",
        "has_text_support",
        "has_email_support",
        "has_live_chat",
    ]:
        if feature_column not in columns:
            d1_query(
                f"ALTER TABLE charities ADD COLUMN {feature_column} INTEGER NOT NULL DEFAULT 0"
            )


def migrate_useful_contacts_schema_local(connection):
    columns = get_table_columns(connection, "useful_contacts")

    migrations = []
    for optional_column in [
        "telephone",
        "contact_email",
        "text_number",
        "tags",
        "description",
    ]:
        if optional_column not in columns:
            migrations.append(
                f"ALTER TABLE useful_contacts ADD COLUMN {optional_column} TEXT DEFAULT ''"
            )

    if "created_at" not in columns:
        migrations.append("ALTER TABLE useful_contacts ADD COLUMN created_at DATETIME")

    for statement in migrations:
        connection.execute(statement)

    if "created_at" not in columns:
        connection.execute(
            "UPDATE useful_contacts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )


def migrate_useful_contacts_schema_remote():
    if not D1_CONFIGURED:
        return

    try:
        columns = {row.get("name") for row in d1_query("PRAGMA table_info(useful_contacts)")}
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Skipping D1 useful contacts migration; unable to inspect schema. Details: {exc}")
        return

    for optional_column in [
        "telephone",
        "contact_email",
        "text_number",
        "tags",
        "description",
    ]:
        if optional_column not in columns:
            d1_query(
                f"ALTER TABLE useful_contacts ADD COLUMN {optional_column} TEXT DEFAULT ''"
            )

    if "created_at" not in columns:
        d1_query("ALTER TABLE useful_contacts ADD COLUMN created_at DATETIME")
        d1_query(
            "UPDATE useful_contacts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )


def normalize_result_set(result_payload):
    if isinstance(result_payload, list) and result_payload:
        first = result_payload[0]
        if isinstance(first, dict):
            return first.get("results", result_payload)
    return result_payload or []


def d1_query(sql, params=None):
    params = params or []

    global D1_AVAILABLE

    if D1_CONFIGURED and D1_AVAILABLE:
        headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"sql": sql, "params": params}).encode()

        try:
            request = urlrequest.Request(D1_BASE_URL, data=payload, headers=headers, method="POST")
            with urlrequest.urlopen(request, timeout=5) as response:  # nosec B310
                data = json.loads(response.read().decode())
            if not data.get("success", False):
                raise RuntimeError(data.get("errors", "Unknown D1 error"))
            return normalize_result_set(data.get("result"))
        except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"D1 query failed; using local fallback database. Details: {exc}")
            D1_AVAILABLE = False

    connection = open_local_db(sqlite3.Row)
    with connection:
        cursor = connection.execute(sql, params)
        if cursor.description:
            return [dict(row) for row in cursor.fetchall()]
    return []


def ensure_tables():
    ensure_local_data_dir()
    table_statements = [
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT NOT NULL,
            affiliate_url TEXT NOT NULL,
            cover_url TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS book_views (
            slug TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS calming_counts (
            slug TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS charities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            logo_url TEXT,
            description TEXT NOT NULL,
            website_url TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            telephone TEXT DEFAULT '',
            contact_email TEXT DEFAULT '',
            text_number TEXT DEFAULT '',
            helpline_hours TEXT DEFAULT '',
            has_helpline INTEGER NOT NULL DEFAULT 0,
            has_volunteers INTEGER NOT NULL DEFAULT 0,
            has_crisis_info INTEGER NOT NULL DEFAULT 0,
            has_text_support INTEGER NOT NULL DEFAULT 0,
            has_email_support INTEGER NOT NULL DEFAULT 0,
            has_live_chat INTEGER NOT NULL DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS media_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            media_type TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS charity_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organisation_name TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            activity_type TEXT DEFAULT '',
            details TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS site_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL DEFAULT ''
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS did_you_know_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            detail TEXT DEFAULT '',
            cta_label TEXT DEFAULT '',
            cta_url TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS useful_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            telephone TEXT DEFAULT '',
            contact_email TEXT DEFAULT '',
            text_number TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ]

    for statement in table_statements:
        d1_query(statement)

    ensure_calming_counts_schema()

    # Always mirror the schema in the local fallback database so queries keep
    # working even if Cloudflare D1 is configured but temporarily unreachable.
    connection = open_local_db()
    with connection:
        for statement in table_statements:
            connection.execute(statement)
        ensure_calming_counts_schema(connection)
        migrate_useful_contacts_schema_local(connection)

    # Apply schema migrations to keep legacy databases aligned with the current model.
    with open_local_db() as connection:
        migrate_charities_schema_local(connection)
        migrate_useful_contacts_schema_local(connection)

    migrate_charities_schema_remote()
    migrate_useful_contacts_schema_remote()


def ensure_calming_counts_schema(connection=None):
    if connection:
        local_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(calming_counts)").fetchall()
        }
        if "view_count" not in local_columns:
            connection.execute("ALTER TABLE calming_counts ADD COLUMN view_count INTEGER DEFAULT 0")
        return

    columns = {row.get("name") for row in d1_query("PRAGMA table_info(calming_counts)")}

    if "view_count" not in columns:
        d1_query("ALTER TABLE calming_counts ADD COLUMN view_count INTEGER DEFAULT 0")


def normalize_calming_entry(entry):
    if isinstance(entry, dict):
        return {
            "completed": int(entry.get("completed", entry.get("count", 0) or 0)),
            "views": int(entry.get("views", entry.get("view_count", 0) or 0)),
        }

    return {"completed": int(entry or 0), "views": 0}


def load_site_settings():
    ensure_tables()

    rows = d1_query("SELECT setting_key, setting_value FROM site_settings")
    settings = {}

    for row in rows:
        key = row.get("setting_key") if isinstance(row, dict) else None
        if key:
            settings[key] = str(row.get("setting_value", ""))

    return settings


def save_site_setting(key, value):
    ensure_tables()

    d1_query(
        """
        INSERT INTO site_settings (setting_key, setting_value)
        VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value
        """,
        [key, value],
    )


def construction_banner_enabled():
    value = load_site_settings().get(CONSTRUCTION_BANNER_KEY, "0")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def set_construction_banner(enabled):
    save_site_setting(CONSTRUCTION_BANNER_KEY, "1" if enabled else "0")


def get_deepseek_api_key():
    return load_site_settings().get(DEEPSEEK_SETTING_KEY, "")


def chat_enabled():
    value = load_site_settings().get(CHAT_ENABLED_KEY, "1")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def set_chat_enabled(enabled):
    save_site_setting(CHAT_ENABLED_KEY, "1" if enabled else "0")


def get_chat_next_session():
    return load_site_settings().get(CHAT_NEXT_SESSION_KEY, "")


def set_chat_next_session(value):
    save_site_setting(CHAT_NEXT_SESSION_KEY, value)


def get_chat_topic():
    return load_site_settings().get(CHAT_TOPIC_KEY, "General mental health support")


def set_chat_topic(value):
    save_site_setting(CHAT_TOPIC_KEY, value)


def get_chat_rules():
    default_rules = """1. Be kind and respectful to everyone
2. No sharing personal contact information
3. No medical advice - suggest professional help instead
4. No harmful content or crisis discussions without proper resources
5. Keep conversations supportive and constructive"""
    return load_site_settings().get(CHAT_RULES_KEY, default_rules)


def set_chat_rules(value):
    save_site_setting(CHAT_RULES_KEY, value)


def get_chat_blocked_words():
    # Default blocked words/phrases (admin can customize)
    default_blocked = "suicide method,how to hurt,kill myself,self harm instructions"
    return load_site_settings().get(CHAT_BLOCKED_WORDS_KEY, default_blocked)


def set_chat_blocked_words(value):
    save_site_setting(CHAT_BLOCKED_WORDS_KEY, value)


def get_chat_block_action():
    # What happens when blocked content is detected: "hide" (silent) or "warn" (show warning)
    return load_site_settings().get(CHAT_BLOCK_ACTION_KEY, "warn")


def set_chat_block_action(value):
    save_site_setting(CHAT_BLOCK_ACTION_KEY, value)


def check_message_content_basic(message):
    """Basic keyword check for blocked content. Returns (is_safe, warning_message)"""
    if not message:
        return True, None
    
    message_lower = message.lower().strip()
    blocked_words = get_chat_blocked_words()
    
    if not blocked_words:
        return True, None
    
    # Split by comma and check each phrase
    blocked_list = [word.strip().lower() for word in blocked_words.split(",") if word.strip()]
    
    for blocked in blocked_list:
        if blocked in message_lower:
            return False, "blocked_word"
    
    return True, None


def ai_moderate_message(message, api_key):
    """Use AI to check message for rule violations. Returns (is_safe, violation_type)"""
    if not api_key or not message:
        return True, None
    
    moderation_prompt = """You are a chat room moderator for a mental health support community. 
Analyze this message and determine if it violates ANY of these rules:

1. CONTACT INFO: Any phone numbers, emails, social media handles, addresses, or attempts to share contact info (even disguised like "my insta is..." or "add me on..." or using spaces/symbols to hide it like "1 2 3 4 5 6 7 8 9 0")
2. MEETING REQUESTS: Asking to meet in person, suggesting meeting up, or trying to arrange offline contact
3. SEXUAL CONTENT: Any sexual talk, innuendos, flirting, suggestive comments, or inappropriate content
4. OFFENSIVE CONTENT: Slurs, hate speech, discriminatory language, bullying, or content that could offend
5. HARMFUL CONTENT: Instructions for self-harm, dangerous activities, or encouraging harmful behavior

Message to check: "{message}"

Respond with ONLY a JSON object:
{{"safe": true}} if the message is fine
{{"safe": false, "reason": "contact_info"}} if sharing/requesting contact info
{{"safe": false, "reason": "meeting_request"}} if trying to meet up
{{"safe": false, "reason": "sexual_content"}} if sexual/inappropriate
{{"safe": false, "reason": "offensive"}} if offensive/hateful
{{"safe": false, "reason": "harmful"}} if harmful content

Be strict. Even subtle attempts to bypass rules should be flagged."""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a strict chat moderator. Respond only with JSON."},
            {"role": "user", "content": moderation_prompt.format(message=message)},
        ],
        "temperature": 0.1,
        "max_tokens": 50,
    }

    try:
        request_data = json.dumps(payload).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        req = urlrequest.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=request_data,
            headers=request_headers,
        )
        with urlrequest.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        content = (result.get("choices") or [{}])[0].get("message", {}).get("content", "")
        
        # Parse the response
        parsed = extract_json_object(content)
        if parsed and isinstance(parsed, dict):
            if parsed.get("safe") == True:
                return True, None
            else:
                return False, parsed.get("reason", "rule_violation")
        
        # If we can't parse, assume safe
        return True, None
        
    except Exception as e:
        print(f"AI moderation error: {e}")
        # On error, fall back to basic check only
        return True, None


def check_message_content(message):
    """Full message check combining basic and AI moderation. Returns (is_safe, violation_type)"""
    if not message:
        return True, None
    
    # First do basic keyword check
    is_safe, reason = check_message_content_basic(message)
    if not is_safe:
        return False, reason
    
    # Then do AI check if API key is available
    api_key = get_deepseek_api_key().strip()
    if api_key:
        is_safe, reason = ai_moderate_message(message, api_key)
        if not is_safe:
            return False, reason
    
    return True, None


def extract_json_object(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        snippet = re.sub(r"```(json)?", "", snippet).strip()
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None

    return None


def deepseek_charity_lookup(api_key, charity):
    prompt = (
        "Use web knowledge and general reasoning to return concise JSON about this charity. "
        "Include fields: telephone (string), contact_email (string), text_number (string), "
        "helpline_hours (string), logo_url (string), has_helpline, has_volunteers, "
        "has_crisis_info, has_text_support, has_email_support, has_live_chat as booleans. "
        "If unknown, use null or false accordingly. Explore the charity's site (including helpline"
        " pages) to surface helpline hours and any text or email contact details."
    )

    charity_summary = (
        f"Name: {charity.get('name', '')}\n"
        f"Website: {charity.get('website_url', '')}\n"
        f"Description: {charity.get('description', '')}"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You return only helpful JSON without commentary."},
            {"role": "user", "content": f"{prompt}\n\n{charity_summary}"},
        ],
        "temperature": 0.2,
    }

    request_data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        req = urlrequest.Request(
            "https://api.deepseek.com/chat/completions",
            data=request_data,
            headers=request_headers,
        )
        with urlrequest.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - external dependency
        return None, f"DeepSeek request failed: {exc.reason or exc.code}"
    except URLError as exc:  # pragma: no cover - external dependency
        return None, f"DeepSeek request failed: {getattr(exc, 'reason', exc)}"
    except Exception as exc:  # pragma: no cover - network variability
        return None, f"DeepSeek lookup error: {exc}"

    content = (
        (result.get("choices") or [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    data = extract_json_object(content)
    if not isinstance(data, dict):
        return None, "Unable to parse DeepSeek response."

    return data, None


def deepseek_useful_contact_lookup(api_key, topic, forbidden_names=None):
    forbidden_names = forbidden_names or []
    avoidance = ""

    normalized_forbidden = sorted(
        {
            normalize_contact_name(name)
            for name in forbidden_names
            if isinstance(name, str) and normalize_contact_name(name)
        }
    )

    if normalized_forbidden:
        avoidance = (
            "Avoid returning any of these names or numbers to prevent duplicates: "
            + ", ".join(normalized_forbidden)
            + "."
        )

    prompt = (
        "Find one widely trusted mental health helpline or text line with strong practical value. "
        "Share concise JSON with fields: name, telephone, contact_email, text_number, description, tags (array of lowercase words). "
        "Include at least one phone or text number. If email or text support is unavailable, return null. "
        "Focus on accessibility and crisis relevance. "
        f"Topic to guide you: {topic}. "
        f"{avoidance}"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Respond with a single JSON object and no commentary."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    request_data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        req = urlrequest.Request(
            "https://api.deepseek.com/chat/completions",
            data=request_data,
            headers=request_headers,
        )
        with urlrequest.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - external dependency
        return None, f"DeepSeek request failed: {exc.code}"
    except URLError:  # pragma: no cover - external dependency
        return None, "Unable to reach DeepSeek API."
    except TimeoutError:  # pragma: no cover - external dependency
        return None, "DeepSeek request timed out."

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    data = extract_json_object(content)

    if not isinstance(data, dict):
        return None, "Unable to parse DeepSeek response."

    return data, None


def coerce_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def mask_secret(value):
    if not value:
        return ""
    value = str(value)
    if len(value) <= 8:
        return value
    return f"{value[:4]}…{value[-4:]}"

def load_books():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, title, author, description, affiliate_url, cover_url
        FROM books
        ORDER BY id
        """
    )

    if not rows:
        books_from_disk = load_books_file()
        if books_from_disk is None:
            books_from_disk = [book.copy() for book in DEFAULT_BOOKS]

        if books_from_disk:
            save_books(books_from_disk)
            rows = d1_query(
                """
                SELECT id, title, author, description, affiliate_url, cover_url
                FROM books
                ORDER BY id
                """
            )
        else:
            return []

    books = [
        {
            "id": row.get("id") if isinstance(row, dict) else None,
            "title": row.get("title", ""),
            "author": row.get("author", ""),
            "description": row.get("description", ""),
            "affiliate_url": row.get("affiliate_url", ""),
            "cover_url": row.get("cover_url", ""),
        }
        for row in rows
    ]

    deduped_books = deduplicate_books(books)
    if len(deduped_books) != len(books):
        save_books(deduped_books)
        return deduped_books

    return deduped_books


def deduplicate_books(books):
    deduped = []
    seen = {}

    for book in books:
        key = (
            book.get("title", "").strip().lower(),
            book.get("author", "").strip().lower(),
            book.get("affiliate_url", "").strip().lower(),
        )

        if key in seen:
            existing = seen[key]
            if not existing.get("cover_url") and book.get("cover_url"):
                existing["cover_url"] = book.get("cover_url")
            continue

        clean_book = {
            "title": book.get("title", ""),
            "author": book.get("author", ""),
            "description": book.get("description", ""),
            "affiliate_url": book.get("affiliate_url", ""),
            "cover_url": book.get("cover_url", ""),
        }
        seen[key] = clean_book
        deduped.append(clean_book)

    return deduped


def load_book_view_counts():
    ensure_tables()

    rows = d1_query("SELECT slug, count FROM book_views")
    counts = {row.get("slug"): row.get("count", 0) for row in rows if row.get("slug")}

    if counts:
        return counts

    with open_local_db(sqlite3.Row) as connection:
        cursor = connection.execute("SELECT slug, count FROM book_views")
        return {row["slug"]: row["count"] for row in cursor.fetchall()}


def increment_book_view(slug):
    if not slug:
        return

    ensure_tables()
    sql = """
    INSERT INTO book_views (slug, count)
    VALUES (?, 1)
    ON CONFLICT(slug) DO UPDATE SET count = book_views.count + 1
    """

    d1_query(sql, [slug])
    with open_local_db() as connection:
        connection.execute(sql, [slug])


def save_books(books):
    ensure_tables()
    books = deduplicate_books(books)

    ensure_local_data_dir()
    with LOCAL_BOOKS_FILE.open("w") as f:
        json.dump(books, f, indent=2)

    d1_query("DELETE FROM books")

    for book in books:
        d1_query(
            """
            INSERT INTO books (title, author, description, affiliate_url, cover_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                book.get("title", ""),
                book.get("author", ""),
                book.get("description", ""),
                book.get("affiliate_url", ""),
                book.get("cover_url", ""),
            ],
        )


def load_charities():
    ensure_tables()

    rows = d1_query(
        """
        SELECT
            id,
            name,
            logo_url,
            description,
            website_url,
            created_at,
            telephone,
            contact_email,
            text_number,
            helpline_hours,
            has_helpline,
            has_volunteers,
            has_crisis_info,
            has_text_support,
            has_email_support,
            has_live_chat
        FROM charities
        ORDER BY created_at DESC, id DESC
        """
    )

    charities = []
    for row in rows:
        charities.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "name": row.get("name", ""),
                "logo_url": row.get("logo_url", ""),
                "description": row.get("description", ""),
                "website_url": row.get("website_url", ""),
                "created_at": row.get("created_at"),
                "telephone": row.get("telephone", ""),
                "contact_email": row.get("contact_email", ""),
                "text_number": row.get("text_number", ""),
                "helpline_hours": row.get("helpline_hours", ""),
                "has_helpline": bool(row.get("has_helpline")),
                "has_volunteers": bool(row.get("has_volunteers")),
                "has_crisis_info": bool(row.get("has_crisis_info")),
                "has_text_support": bool(row.get("has_text_support")),
                "has_email_support": bool(row.get("has_email_support")),
                "has_live_chat": bool(row.get("has_live_chat")),
            }
        )

    return charities


def load_charity_activities():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, organisation_name, activity_name, activity_type, details, created_at
        FROM charity_activities
        ORDER BY created_at DESC, id DESC
        """
    )

    activities = []
    for row in rows:
        activities.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "organisation_name": row.get("organisation_name", ""),
                "activity_name": row.get("activity_name", ""),
                "activity_type": row.get("activity_type", ""),
                "details": row.get("details", ""),
                "created_at": row.get("created_at"),
            }
        )

    return activities


def seed_did_you_know_items():
    for item in DEFAULT_DID_YOU_KNOW_ITEMS:
        d1_query(
            """
            INSERT INTO did_you_know_items (headline, detail, cta_label, cta_url)
            VALUES (?, ?, ?, ?)
            """,
            [
                item.get("headline", ""),
                item.get("detail", ""),
                item.get("cta_label", ""),
                normalize_support_link(item.get("cta_url", "")),
            ],
        )


def load_did_you_know_items():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, headline, detail, cta_label, cta_url, created_at
        FROM did_you_know_items
        ORDER BY created_at DESC, id DESC
        """
    )

    if not rows:
        seed_did_you_know_items()
        rows = d1_query(
            """
            SELECT id, headline, detail, cta_label, cta_url, created_at
            FROM did_you_know_items
            ORDER BY created_at DESC, id DESC
            """
        )

    items = []
    for row in rows:
        items.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "headline": row.get("headline", ""),
                "detail": row.get("detail", ""),
                "cta_label": row.get("cta_label", ""),
                "cta_url": normalize_support_link(row.get("cta_url", "")),
                "created_at": row.get("created_at"),
            }
        )

    return items


def normalize_tag_list(raw_tags):
    tags = []
    for chunk in re.split(r",|;|\n", raw_tags or ""):
        tag = chunk.strip().lower()
        if tag:
            tags.append(tag)
    return tags


def derive_contact_tags(contact):
    tags = set(normalize_tag_list(contact.get("tags", "")))

    if contact.get("telephone"):
        tags.add("phone")
        tags.add("call")
    if contact.get("text_number"):
        tags.add("text")
        tags.add("sms")
    if contact.get("contact_email"):
        tags.add("email")

    return sorted(tags)


def normalize_contact_name(name):
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


def validate_useful_contact_channels(telephone, text_number, contact_email):
    telephone = (telephone or "").strip()
    text_number = (text_number or "").strip()
    contact_email = (contact_email or "").strip()

    if not (telephone or text_number or contact_email):
        return False, "Please include at least one contact method (phone, text, or email)."

    return True, None


def load_useful_contacts():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, name, telephone, contact_email, text_number, tags, description, created_at
        FROM useful_contacts
        ORDER BY created_at DESC, id DESC
        """
    )

    contacts = []
    for row in rows:
        contact = {
            "id": row.get("id") if isinstance(row, dict) else None,
            "name": row.get("name", ""),
            "telephone": row.get("telephone", ""),
            "contact_email": row.get("contact_email", ""),
            "text_number": row.get("text_number", ""),
            "tags": row.get("tags", ""),
            "description": row.get("description", ""),
            "created_at": row.get("created_at"),
        }
        contact["all_tags"] = derive_contact_tags(contact)
        contacts.append(contact)

    return contacts


def useful_contact_exists(name, telephone=None, contact_email=None):
    normalized_name = normalize_contact_name(name)
    telephone = (telephone or "").strip()
    contact_email = (contact_email or "").strip().lower()

    for contact in load_useful_contacts():
        if normalize_contact_name(contact.get("name")) == normalized_name:
            return True
        if telephone and contact.get("telephone", "").strip() == telephone:
            return True
        if contact_email and contact.get("contact_email", "").strip().lower() == contact_email:
            return True

    return False


def save_useful_contact(contact):
    ensure_tables()
    tags = ",".join(normalize_tag_list(contact.get("tags", "")))
    d1_query(
        """
        INSERT INTO useful_contacts (name, telephone, contact_email, text_number, tags, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            contact.get("name", ""),
            contact.get("telephone", ""),
            contact.get("contact_email", ""),
            contact.get("text_number", ""),
            tags,
            contact.get("description", ""),
        ],
    )


def update_useful_contact(contact_id, data):
    ensure_tables()
    tags = ",".join(normalize_tag_list(data.get("tags", "")))
    d1_query(
        """
        UPDATE useful_contacts
        SET name = ?, telephone = ?, contact_email = ?, text_number = ?, tags = ?, description = ?
        WHERE id = ?
        """,
        [
            data.get("name", ""),
            data.get("telephone", ""),
            data.get("contact_email", ""),
            data.get("text_number", ""),
            tags,
            data.get("description", ""),
            contact_id,
        ],
    )


def delete_useful_contact(contact_id):
    ensure_tables()
    d1_query("DELETE FROM useful_contacts WHERE id = ?", [contact_id])


def normalize_media_type(media_type):
    normalized = (media_type or "").strip().lower()
    return normalized if normalized in {"image", "video"} else None


def resolve_media_url(primary_url, library_url):
    library_choice = (library_url or "").strip()
    manual_choice = (primary_url or "").strip()
    chosen = library_choice or manual_choice

    return normalize_url(chosen)


def load_media_assets():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, name, media_type, url, description, created_at
        FROM media_assets
        ORDER BY created_at DESC, id DESC
        """
    )

    assets = []
    for row in rows:
        assets.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "name": row.get("name", ""),
                "media_type": row.get("media_type", ""),
                "url": row.get("url", ""),
                "description": row.get("description", ""),
                "created_at": row.get("created_at"),
            }
        )

    return assets


def find_media_asset_by_name(name):
    if not name:
        return None

    normalized = name.strip().lower()

    for asset in load_media_assets():
        if asset.get("name", "").strip().lower() == normalized:
            return asset

    return None


def pick_featured_books(books, count=3):
    if len(books) <= count:
        return list(range(len(books)))

    return list(range(count))


def books_with_indices(books, view_counts=None):
    view_counts = view_counts or load_book_view_counts()
    max_views = max(view_counts.values(), default=0)
    max_viewed_slug = None

    if max_views > 0:
        leaders = [slug for slug, count in view_counts.items() if count == max_views]
        if len(leaders) == 1:
            max_viewed_slug = leaders[0]

    books_with_data = []
    for idx, book in enumerate(books):
        slug = book.get("slug") or book_slug(book, f"book-{idx}")
        view_count = view_counts.get(slug, 0)
        books_with_data.append(
            {
                **book,
                "index": idx,
                "slug": slug,
                "view_count": view_count,
                "is_most_viewed": slug == max_viewed_slug,
            }
        )

    return books_with_data

RESOURCES = [
    {
        "title": "Crisis Support Lines",
        "description": "Round-the-clock phone and text lines offering immediate help and compassionate listeners.",
        "links": [
            {"label": "988 Suicide & Crisis Lifeline (US)", "url": "https://988lifeline.org/"},
            {"label": "Samaritans (UK & IE)", "url": "https://www.samaritans.org/how-we-can-help/contact-samaritan/"},
            {"label": "Lifeline Australia", "url": "https://www.lifeline.org.au/"},
        ],
        "tags": ["urgent", "phone", "text"],
    },
    {
        "title": "Find a Therapist",
        "description": "Search directories to connect with licensed therapists, counselors, and culturally competent providers.",
        "links": [
            {"label": "Psychology Today Directory", "url": "https://www.psychologytoday.com/us/therapists"},
            {"label": "Inclusive Therapists", "url": "https://www.inclusivetherapists.com/"},
            {"label": "Therapy for Black Girls", "url": "https://therapyforblackgirls.com/directory/"},
        ],
        "tags": ["therapy", "directory", "ongoing"],
    },
    {
        "title": "Self-Guided Programs",
        "description": "Evidence-based courses that teach coping skills, mindfulness, and resilience at your own pace.",
        "links": [
            {"label": "Moodgym", "url": "https://moodgym.com.au/"},
            {"label": "Centre for Clinical Interventions", "url": "https://www.cci.health.wa.gov.au/Resources/Looking-After-Yourself"},
            {"label": "Mindfulness Coach (VA)", "url": "https://mobile.va.gov/app/mindfulness-coach"},
        ],
        "tags": ["cbt", "mindfulness", "self-paced"],
    },
    {
        "title": "Peer Support Communities",
        "description": "Safe, moderated spaces to share experiences, ask questions, and find solidarity.",
        "links": [
            {"label": "7 Cups", "url": "https://www.7cups.com/"},
            {"label": "Mental Health America Forums", "url": "https://mhanational.org/find-support/groups"},
            {"label": "The Mighty", "url": "https://themighty.com/"},
        ],
        "tags": ["community", "online", "connection"],
    },
    {
        "title": "Crisis Planning",
        "description": "Templates and tools to build a safety plan, identify warning signs, and keep supportive contacts handy.",
        "links": [
            {"label": "Safety Plan Template (SPRC)", "url": "https://sprc.org/wp-content/uploads/2023/01/SafetyPlanTemplate.pdf"},
            {"label": "Now Matters Now", "url": "https://www.nowmattersnow.org/skills/safety-plan"},
            {"label": "Veterans Crisis Plan", "url": "https://www.mentalhealth.va.gov/suicide_prevention/docs/VA_Safety_planning_manual.pdf"},
        ],
        "tags": ["planning", "safety", "template"],
    },
    {
        "title": "Mental Health Education",
        "description": "Guides on anxiety, depression, trauma, and more—written in approachable, supportive language.",
        "links": [
            {"label": "National Institute of Mental Health", "url": "https://www.nimh.nih.gov/health/topics"},
            {"label": "Mind (UK) A-Z", "url": "https://www.mind.org.uk/information-support/"},
            {"label": "Anxiety & Depression Association of America", "url": "https://adaa.org/understanding-anxiety"},
        ],
        "tags": ["education", "reading", "learn"],
    },
    {
        "title": "Apps for Calm & Focus",
        "description": "Mobile apps featuring guided breathing, grounding exercises, and gentle reminders to pause.",
        "links": [
            {"label": "Insight Timer", "url": "https://insighttimer.com/"},
            {"label": "Smiling Mind", "url": "https://www.smilingmind.com.au/smiling-mind-app"},
            {"label": "MindShift CBT", "url": "https://www.anxietycanada.com/resources/mindshift-cbt/"},
        ],
        "tags": ["apps", "mindfulness", "breathing"],
    },
    {
        "title": "Support for Friends & Family",
        "description": "Resources that teach loved ones how to listen, validate, and respond during difficult moments.",
        "links": [
            {"label": "Seize the Awkward", "url": "https://seizetheawkward.org/"},
            {"label": "Active Listening Toolkit", "url": "https://www.mhanational.org/talking-friends-and-family-about-mental-health"},
            {"label": "Mental Health First Aid", "url": "https://www.mentalhealthfirstaid.org/"},
        ],
        "tags": ["family", "friends", "skills"],
    },
]

CALMING_TOOLS = [
    {
        "slug": "five-senses-reset",
        "title": "Five Senses Reset",
        "description": "A grounding practice to notice sight, sound, touch, scent, and taste in the room around you.",
        "steps": [
            "Name five things you can see.",
            "Notice four things you can touch.",
            "Listen for three sounds.",
            "Identify two scents near you.",
            "Take one slow sip of water or a mindful breath.",
        ],
    },
    {
        "slug": "box-breathing",
        "title": "Box Breathing",
        "description": "Steady your nervous system with a balanced inhale, hold, and exhale.",
        "steps": [
            "Inhale through your nose for four counts.",
            "Hold gently for four counts.",
            "Exhale through your mouth for four counts.",
            "Pause for four counts before the next breath.",
        ],
    },
    {
        "slug": "tension-release",
        "title": "Tension & Release",
        "description": "Relax each muscle group with a short squeeze and soften sequence.",
        "steps": [
            "Start at your hands: squeeze for five seconds, then release.",
            "Move to shoulders, face, and legs with the same pattern.",
            "Notice the warmth and heaviness after each release.",
        ],
    },
    {
        "slug": "ripple-journey",
        "title": "Aurora Ripple Journey",
        "description": "A gentle visualization that pairs your breath with soft waves of color and motion.",
        "steps": [
            "Sit comfortably and imagine a calm pool in front of you, lit by soft sunrise colors.",
            "Inhale for four counts as you picture a rosy glow spreading across the water.",
            "Hold for two counts and notice the glow shimmering with tiny ripples.",
            "Exhale for six counts, watching the colors fade into a cool lavender mist.",
            "Repeat for three rounds, letting each ripple carry tension away from your body.",
            "Finish by placing a hand over your heart and thanking yourself for pausing.",
        ],
    },
    {
        "slug": "anxiety-colour-drop",
        "title": "Anxiety Colour Drop",
        "description": "Drag coloured emotion droplets into a calm pool and watch them dissolve as a symbolic release.",
        "steps": [
            "Name the feeling you're holding—frustration, worry, guilt, fear, or anything else.",
            "Drag that droplet into the water and picture the colour softening as it lands.",
            "Take a slow exhale as the ripple fades, letting the feeling loosen its grip.",
            "Repeat with any remaining emotions until the pool looks lighter.",
        ],
    },
    {
        "slug": "tense-relax-spinner",
        "title": "Tense / Relax Spinner",
        "description": "Let the wheel pick a body area to gently tense and soften while the colours dance.",
        "steps": [
            "Watch the spinner choose a muscle group like shoulders, hands, or calves.",
            "On the highlighted area, tense for five seconds, then melt the tension away.",
            "Track the flashes—each one is your cue to breathe out and soften further.",
            "Repeat each spin or pause to notice warmth and heaviness spreading through you.",
        ],
    },
]

CALMING_TOOL_PAGES = [
    {
        "slug": "breath-flow",
        "title": "Breath Flow",
        "description": "Light, fluid breathwork with custom timing, waves, and a session timer.",
        "template": "tools/breath_flow.html",
    },
    {
        "slug": "progressive-muscle-relaxation",
        "title": "Progressive Muscle Relaxation",
        "description": "Travel from toes to forehead with gentle squeezes and glowing cues.",
        "template": "tools/muscle_relaxation.html",
    },
    {
        "slug": "anxiety-colour-drop",
        "title": "Anxiety Colour Drop",
        "description": "Drag coloured emotion droplets into the pool and release them with your breath.",
        "template": "tools/anxiety_colour_drop.html",
        "count_slug": "anxiety-colour-drop",
    },
    {
        "slug": "five-senses-reset",
        "title": "Five Senses Reset",
        "description": "Ground quickly by noticing sights, textures, sounds, scents, and taste.",
        "template": "tools/simple_tool.html",
        "count_slug": "five-senses-reset",
    },
    {
        "slug": "box-breathing",
        "title": "Box Breathing",
        "description": "Balance your nervous system with a steady four-count inhale, hold, and exhale.",
        "template": "tools/simple_tool.html",
        "count_slug": "box-breathing",
    },
    {
        "slug": "tension-release",
        "title": "Tension & Release",
        "description": "Use short squeezes and softens to melt muscle tension from head to toe.",
        "template": "tools/simple_tool.html",
        "count_slug": "tension-release",
    },
    {
        "slug": "ripple-journey",
        "title": "Aurora Ripple Journey",
        "description": "Pair your breath with sunrise colours and ripples that drift tension away.",
        "template": "tools/simple_tool.html",
        "count_slug": "ripple-journey",
    },
    {
        "slug": "tense-relax-spinner",
        "title": "Tense / Relax Spinner",
        "description": "A colour-soaked spinner that picks where to squeeze and release next.",
        "template": "tools/tense_relax_spinner.html",
        "count_slug": "tense-relax-spinner",
    },
]


CALMING_NAV_SLUGS = {
    "breath-flow",
    "progressive-muscle-relaxation",
    "anxiety-colour-drop",
    "tense-relax-spinner",
}


@app.context_processor
def inject_calming_nav():
    return {
        "calming_nav_items": [
            {
                "title": tool["title"],
                "slug": tool["slug"],
                "description": tool.get("description", ""),
            }
            for tool in CALMING_TOOL_PAGES
            if tool.get("slug") in CALMING_NAV_SLUGS
        ]
    }


@app.context_processor
def inject_site_flags():
    return {"construction_banner_enabled": construction_banner_enabled()}


@app.context_processor
def inject_media_library():
    assets = load_media_assets()
    lookup = {asset.get("name", ""): asset for asset in assets}

    def get_media_asset(name):
        key = (name or "").strip().lower()
        return next(
            (
                asset
                for asset in assets
                if asset.get("name", "").strip().lower() == key
            ),
            None,
        )

    return {"media_library": assets, "media_lookup": lookup, "get_media_asset": get_media_asset}


def load_calming_counts():
    ensure_tables()

    rows = d1_query("SELECT slug, count, view_count FROM calming_counts")
    counts = {}
    for row in rows:
        slug = row.get("slug") if isinstance(row, dict) else None
        if slug:
            counts[slug] = normalize_calming_entry(row)

    for tool in CALMING_TOOLS:
        slug = tool.get("slug", slugify(tool["title"]))
        counts.setdefault(slug, {"completed": 0, "views": 0})

    for page in CALMING_TOOL_PAGES:
        slug = page.get("count_slug") or page.get("slug")
        counts.setdefault(slug, {"completed": 0, "views": 0})

    normalized = {slug: normalize_calming_entry(entry) for slug, entry in counts.items()}

    save_calming_counts(normalized)
    return normalized


def save_calming_counts(counts):
    ensure_tables()
    d1_query("DELETE FROM calming_counts")

    normalized = {slug: normalize_calming_entry(entry) for slug, entry in counts.items()}

    for slug, count in normalized.items():
        d1_query(
            "INSERT INTO calming_counts (slug, count, view_count) VALUES (?, ?, ?)",
            [slug, int(count.get("completed", 0) or 0), int(count.get("views", 0) or 0)],
        )


def calming_tools_with_counts():
    counts = load_calming_counts()
    updated = {}
    tools_with_counts = []

    for tool in CALMING_TOOLS:
        slug = tool.get("slug", slugify(tool["title"]))
        count = counts.get(slug, {"completed": 0, "views": 0})
        updated[slug] = count
        tools_with_counts.append(
            {
                **tool,
                "slug": slug,
                "completed_count": count.get("completed", 0),
                "view_count": count.get("views", 0),
            }
        )

    if counts.keys() != updated.keys():
        save_calming_counts(updated)

    return tools_with_counts


def calming_tool_cards():
    counts = load_calming_counts()
    cards = []

    for page in CALMING_TOOL_PAGES:
        count_slug = page.get("count_slug") or page["slug"]
        count = counts.get(count_slug, {"completed": 0, "views": 0})
        cards.append(
            {
                **page,
                "completed_count": count.get("completed", 0),
                "view_count": count.get("views", 0),
            }
        )

    return cards


def find_calming_tool(slug):
    for tool in CALMING_TOOLS:
        if tool.get("slug") == slug:
            return tool
    return None

COMMUNITY_HIGHLIGHTS = [
    {
        "title": "Peer Circles",
        "description": "Weekly online spaces where you can share, listen, or simply sit with others who understand.",
    },
    {
        "title": "Story Spotlights",
        "description": "Gentle, anonymous stories from people who found support and kept going—proof that healing is possible.",
    },
    {
        "title": "Resource Swaps",
        "description": "A living list where the community adds podcasts, books, and practices that help them feel grounded.",
    },
]


@app.route("/")
def index():
    books = books_with_indices(load_books())
    charities = load_charities()
    did_you_know_items = load_did_you_know_items()
    return render_template(
        "home.html",
        resources=RESOURCES,
        books=books,
        charities=charities,
        did_you_know_items=did_you_know_items,
    )


@app.route("/books")
def books():
    book_list = books_with_indices(load_books())
    return render_template("books.html", books=book_list)


@app.route("/books/<slug>/view", methods=["POST"])
def track_book_view(slug):
    increment_book_view(slug)
    return {"success": True}


@app.route("/charities")
def charities_page():
    return render_template("charities.html", charities=load_charities())


@app.route("/activities")
def activities_page():
    activities = load_charity_activities()
    selected_id = request.args.get("activity_id", type=int)
    selected_activity = None

    if activities:
        selected_activity = next(
            (activity for activity in activities if activity.get("id") == selected_id),
            None,
        )
        if not selected_activity:
            selected_activity = activities[0]

    return render_template(
        "activities.html", activities=activities, selected_activity=selected_activity
    )


@app.route("/resources")
def resources():
    return render_template("resources.html", resources=RESOURCES)


@app.route("/chat")
def chat_room():
    return render_template(
        "chat.html",
        chat_enabled=chat_enabled(),
        chat_topic=get_chat_topic(),
        chat_next_session=get_chat_next_session(),
        chat_rules=get_chat_rules(),
    )


def build_chat_prompt(roster, history, latest_message, warmup=False, topic="", single_message=False, reply_to_user=False, last_speaker="", all_participants=None):
    history_lines = []
    last_message_in_history = ""
    last_few_speakers = []

    for item in history[-12:]:
        sender = (item.get("sender") or "Someone").strip() or "Someone"
        text = (item.get("text") or "").strip()
        if text:
            history_lines.append(f"{sender}: {text}")
            last_message_in_history = f"{sender} said: \"{text}\""
            if sender not in last_few_speakers:
                last_few_speakers.append(sender)

    # Keep track of recent speakers to sometimes address them by name
    recent_names = last_few_speakers[-4:] if last_few_speakers else []
    
    conversation_block = "\n".join(history_lines) if history_lines else "(quiet room - be the first to say something)"

    topic_context = f" Today's vibe/topic: '{topic}'." if topic else ""

    import random
    
    # Random personality type for this message
    personality_types = [
        ("joker", "You're funny and playful. Make jokes, tease people gently, use humor. Light-hearted."),
        ("joker", "You're funny and playful. Make jokes, tease people gently, use humor. Light-hearted."),
        ("curious", "You ask questions and are interested in others. 'wait what?' 'how come?' 'tell me more'"),
        ("curious", "You ask questions and are interested in others. 'wait what?' 'how come?' 'tell me more'"),
        ("chill", "You're laid back. Short responses, unbothered. 'lol nice' 'fair' 'mood'"),
        ("chill", "You're laid back. Short responses, unbothered. 'lol nice' 'fair' 'mood'"),
        ("chill", "You're laid back. Short responses, unbothered. 'lol nice' 'fair' 'mood'"),
        ("caring", "You're warm and check on people. 'u ok?' 'hope ur good' 'thats rough sending hugs'"),
        ("random", "You go off on tangents or bring up random stuff. Change the subject sometimes."),
    ]
    personality_name, personality_desc = random.choice(personality_types)
    
    # Random target message length (1-7 words, heavily weighted toward very short)
    length_options = [1, 1, 1, 2, 2, 2, 3, 3, 4, 5, 6, 7]
    target_length = random.choice(length_options)
    
    # Pick someone to potentially address by name (50% chance)
    address_someone = ""
    if recent_names and random.random() < 0.5:
        address_someone = random.choice(recent_names)
    
    # Varied conversation behaviors - NOT always responding to the last message
    behavior_roll = random.random()
    if behavior_roll < 0.25 and len(history_lines) > 3:
        # Start a new topic / tangent
        conversation_directions = [
            "change the subject - bring up something random but interesting",
            "start a new topic - ask about something unrelated",
            "go off on a tangent - mention something random thats on your mind",
            "ignore the current convo and say something funny or random",
        ]
    elif behavior_roll < 0.45 and address_someone:
        # Address someone specific
        conversation_directions = [
            f"talk directly TO {address_someone} - use their name, ask them something or react to them",
            f"reply to {address_someone} specifically - mention their name",
            f"check in with {address_someone} - '@' them basically",
        ]
    elif behavior_roll < 0.65 and last_speaker:
        # React to last speaker
        conversation_directions = [
            f"react to what {last_speaker} just said",
            f"respond to {last_speaker}'s message",
            f"agree or disagree with {last_speaker}",
        ]
    else:
        # General chat vibes
        conversation_directions = [
            "say something funny or make a joke",
            "share a quick thought or reaction",
            "ask a random question to anyone",
            "react with just an emoji response or very short text",
            "say something relatable",
        ]
    
    random_direction = random.choice(conversation_directions)

    # Build list of who's in the chat for @mentions
    participants_list = ", ".join(all_participants[:6]) if all_participants else "various people"

    personalities = f"""
PERSONALITY: {personality_name.upper()}
{personality_desc}

PEOPLE IN CHAT: {participants_list}

TARGET LENGTH: {target_length} words max (shorter = better)

MAKING CHAT INTERESTING:
- Use @names sometimes: "@{address_someone or 'name'} lol what" or "{address_someone or 'name'} u ok?"
- Start NEW topics sometimes - dont just answer the same question forever
- Make jokes, be playful, tease people (nicely)
- Go off on tangents - real chats arent linear
- NOT everyone needs to answer every question - sometimes ignore it

EXAMPLE GOOD MESSAGES:
- "@maya wait that reminds me"
- "lol james ur so dramatic"
- "ok but random thought"
- "anyone else hungry or just me"
- "ngl i zoned out what we talking about"
- "@sarah u good?"
- "lmaooo"
- "wait can we talk about something else"

BAD (boring): "im doing okay" "just hanging in there" "surviving" [everyone saying the same thing]
GOOD (interesting): jokes, tangents, @mentions, questions, random thoughts, teasing

Recent chat:
{conversation_block}

Your task: {random_direction}"""

    if reply_to_user:
        guidance = (
            f"A real person just said: \"{latest_message}\"\n"
            f"RESPOND directly to what they said. React, relate, or ask a follow-up. Max {target_length} words."
        )
        request_block = (
            "Return JSON array with exactly 1 object: "
            "{\"sender\": \"Peer\", \"role\": \"peer\", \"text\": string}. "
            f"Max {target_length + 2} words. RESPOND to their message, don't change topic."
        )
    elif single_message:
        guidance = (
            f"Generate ONE message, max {target_length} words.{topic_context}\n"
            f"Task: {random_direction}\n"
            f"Be interesting - jokes, @mentions, tangents, questions. Not boring answers."
        )
        request_block = (
            "Return JSON array with exactly 1 object: "
            "{\"sender\": \"Peer\", \"role\": \"peer\", \"text\": string}. "
            f"Max {target_length} words. Be interesting not boring."
        )
    elif warmup:
        guidance = (
            f"Show 2 messages - someone says something, someone else reacts.{topic_context} Keep short and fun."
        )
        request_block = (
            "Return JSON array with 2 objects: "
            "{\"sender\": \"Peer\", \"role\": \"peer\", \"text\": string}. "
            "Keep each 2-5 words. Make it interesting - joke, question, or @mention."
        )
    else:
        guidance = f"Be a {personality_name} person. Max {target_length} words. Do: {random_direction}"
        request_block = (
            "Return JSON array with exactly 1 object: "
            "{\"sender\": \"Peer\", \"role\": \"peer\", \"text\": string}. "
            f"Max {target_length} words. Be interesting - use @names, jokes, or tangents."
        )

    return (
        f"Generate realistic group chat. Be INTERESTING - jokes, @mentions, tangents, not everyone answering same question.\n\n"
        f"{personalities}\n\n"
        f"{guidance}\n"
        f"{request_block}"
    )


def deepseek_chat_reply(api_key, message, history=None, warmup=False, topic="", single_message=False, reply_to_user=False, last_speaker="", all_participants=None):
    history = history or []
    all_participants = all_participants or []

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Generate brief group chat messages. Be INTERESTING: use @names, jokes, tangents, change topics. "
                    "NOT everyone answers every question. Max 7 words. Real chat energy."
                ),
            },
            {
                "role": "user",
                "content": build_chat_prompt(
                    [],  # Roster not used anymore
                    history,
                    message,
                    warmup=warmup,
                    topic=topic,
                    single_message=single_message,
                    reply_to_user=reply_to_user,
                    last_speaker=last_speaker,
                    all_participants=all_participants,
                ),
            },
        ],
        "temperature": 0.85,  # Good variety but more focused
        "max_tokens": 60,  # Shorter max to enforce brevity
    }

    request_data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        req = urlrequest.Request(
            "https://api.deepseek.com/chat/completions",
            data=request_data,
            headers=request_headers,
        )
        with urlrequest.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - external dependency
        return None, f"DeepSeek request failed: {exc.reason or exc.code}"
    except URLError as exc:  # pragma: no cover - external dependency
        return None, f"DeepSeek request failed: {getattr(exc, 'reason', exc)}"
    except Exception as exc:  # pragma: no cover - network variability
        return None, f"DeepSeek lookup error: {exc}"

    content = (
        (result.get("choices") or [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    parsed = extract_json_object(content)
    
    # Handle case where response is wrapped in a "messages" key
    if isinstance(parsed, dict) and "messages" in parsed:
        parsed = parsed.get("messages", [])
    
    if not isinstance(parsed, list):
        # Try to extract array from content if it starts with [
        if content.strip().startswith("["):
            try:
                parsed = json.loads(content.strip())
            except json.JSONDecodeError:
                return None, "Unable to parse DeepSeek response."
        else:
            return None, "Unable to parse DeepSeek response."

    messages = []

    for item in parsed:
        if not isinstance(item, dict):
            continue
        sender = (item.get("sender") or "Peer").strip() or "Peer"
        role = (item.get("role") or "peer").strip().lower()
        role = "mod" if role == "mod" else "peer"
        text = (item.get("text") or "").strip()
        if not text:
            continue
        
        # Add realistic text modifications (typos, slang, x's for women)
        text = add_realistic_text_style(text, sender)
        
        messages.append({"sender": sender[:40], "role": role, "text": text[:500]})

    if not messages:
        return None, "DeepSeek returned no usable messages."

    return messages, None


def add_realistic_text_style(text, sender_name=""):
    """Add realistic typos, slang, and style to messages"""
    import random
    
    # Common female names that might add 'x' at the end
    female_names = [
        'luna', 'zara', 'maya', 'ava', 'ivy', 'ella', 'mia', 'lily', 'emma', 'olivia',
        'sophia', 'isabella', 'charlotte', 'amelia', 'harper', 'evelyn', 'aria', 'chloe',
        'camila', 'penelope', 'riley', 'layla', 'zoey', 'nora', 'lily', 'eleanor', 'hannah',
        'lillian', 'addison', 'aubrey', 'ellie', 'stella', 'natalie', 'leah', 'hazel',
        'violet', 'aurora', 'savannah', 'audrey', 'brooklyn', 'bella', 'claire', 'skylar',
        'lucy', 'paisley', 'everly', 'anna', 'caroline', 'nova', 'genesis', 'emilia',
        'kennedy', 'samantha', 'maya', 'willow', 'kinsley', 'naomi', 'aaliyah', 'elena',
        'sarah', 'ariana', 'allison', 'gabriella', 'alice', 'madelyn', 'cora', 'ruby',
        'eva', 'serenity', 'autumn', 'adeline', 'hailey', 'gianna', 'valentina', 'isla',
        'eliana', 'quinn', 'nevaeh', 'ivy', 'sadie', 'piper', 'lydia', 'alexa', 'josephine',
        'priya', 'ananya', 'aisha', 'fatima', 'yasmin', 'sara', 'leila', 'nina', 'rosa',
        'maria', 'carmen', 'sofia', 'lucia', 'valentina', 'camila', 'nicole', 'jessica',
        'ashley', 'emily', 'madison', 'elizabeth', 'megan', 'jennifer', 'amanda', 'rachel'
    ]
    
    # Common typos/misspellings to randomly apply
    typo_replacements = {
        'the': ['teh', 'hte', 'the'],
        'you': ['yuo', 'you', 'u'],
        'your': ['yuor', 'your', 'ur'],
        "you're": ["youre", "your", "you're", "ur"],
        'have': ['ahve', 'have', 'hav'],
        'that': ['taht', 'that', 'tht'],
        'with': ['wiht', 'with', 'wth'],
        'just': ['jsut', 'just', 'jst'],
        'like': ['liek', 'like', 'lik'],
        'know': ['knwo', 'know', 'kno'],
        'think': ['thnk', 'think', 'thikn'],
        'really': ['realy', 'really', 'rly', 'rlly'],
        'people': ['poeple', 'people', 'ppl'],
        'about': ['abuot', 'about', 'abt'],
        'because': ['becuase', 'because', 'bc', 'cuz', 'cos'],
        'something': ['somethign', 'something', 'smth'],
        'though': ['tho', 'though', 'thouhg'],
        'through': ['thru', 'through'],
        'thought': ['thougt', 'thought', 'thot'],
        'would': ['woudl', 'would', 'wld'],
        'could': ['coudl', 'could', 'cld'],
        'should': ['shoudl', 'should', 'shld'],
        'going': ['goign', 'going', 'goin'],
        'being': ['beign', 'being', 'bein'],
        'probably': ['prolly', 'probably', 'prob'],
        'definitely': ['definetly', 'definitely', 'def', 'deffo'],
        'actually': ['actualy', 'actually', 'acc'],
        'literally': ['literaly', 'literally', 'lit'],
        'tonight': ['tonite', 'tonight', '2nite'],
        'tomorrow': ['tmrw', 'tomorrow', 'tomoro'],
        'okay': ['ok', 'okay', 'okayy', 'k'],
        'right': ['rigth', 'right', 'rite'],
        'want': ['wnat', 'want', 'wanna'],
        'what': ['waht', 'what', 'wut'],
        'before': ['befroe', 'before', 'b4'],
        'please': ['plz', 'please', 'pls'],
        'thanks': ['thx', 'thanks', 'thnks', 'ty'],
        'sorry': ['sry', 'sorry', 'srry'],
        'message': ['mesage', 'message', 'msg'],
        'different': ['diferent', 'different', 'diff'],
        'feeling': ['feelin', 'feeling', 'feelign'],
        'amazing': ['amazign', 'amazing', 'amazin'],
        'awesome': ['awsome', 'awesome', 'awsum'],
        'weird': ['wierd', 'weird'],
        'friend': ['freind', 'friend', 'frnd'],
        'good': ['goood', 'good', 'gud'],
        'great': ['greta', 'great', 'gr8'],
        'never': ['nevr', 'never', 'nvr'],
        'always': ['alwyas', 'always', 'alwys'],
        'today': ['tday', 'today', '2day'],
        'maybe': ['mabye', 'maybe', 'mayb'],
        'same': ['saem', 'same', 'samee'],
        'love': ['lvoe', 'love', 'luv'],
        'pretty': ['prtty', 'pretty', 'prety'],
        'anyone': ['anywone', 'anyone', 'any1'],
        'someone': ['somewone', 'someone', 'some1'],
        'everyone': ['evryone', 'everyone', 'every1'],
    }
    
    # 30% chance to apply a typo
    if random.random() < 0.30:
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?')
            if word_lower in typo_replacements and random.random() < 0.4:
                replacement = random.choice(typo_replacements[word_lower])
                # Preserve original case if it was capitalized
                if word[0].isupper() and replacement[0].islower():
                    replacement = replacement[0].upper() + replacement[1:]
                # Preserve trailing punctuation
                trailing = ''
                for char in reversed(word):
                    if char in '.,!?':
                        trailing = char + trailing
                    else:
                        break
                words[i] = replacement + trailing
                break  # Only one typo per message
        text = ' '.join(words)
    
    # 25% chance to add slang like "lol", "lmao", "tbh" if not already present
    slang_additions = ['lol', 'lmao', 'tbh', 'ngl', 'fr', 'icl', 'istg']
    text_lower = text.lower()
    if random.random() < 0.25 and not any(s in text_lower for s in slang_additions):
        slang = random.choice(slang_additions)
        # Add at end or beginning
        if random.random() < 0.7:
            # End - remove period if present and add slang
            text = text.rstrip('.') + ' ' + slang
        else:
            # Beginning
            text = slang + ' ' + text[0].lower() + text[1:] if text else slang
    
    # 40% chance for female names to add 'x' at the end
    if sender_name and sender_name.lower() in female_names and random.random() < 0.40:
        text = text.rstrip('.!') + ' x'
    
    # 15% chance to double a letter for emphasis (like "soooo" or "yesss")
    if random.random() < 0.15:
        emphasis_words = ['so', 'yes', 'no', 'oh', 'aw', 'ah', 'ugh', 'wow', 'yay', 'hey', 'hi']
        words = text.split()
        for i, word in enumerate(words):
            if word.lower().rstrip('.,!?') in emphasis_words and random.random() < 0.5:
                clean_word = word.rstrip('.,!?')
                trailing = word[len(clean_word):]
                # Double the last letter 2-3 times
                doubled = clean_word + clean_word[-1] * random.randint(1, 3)
                words[i] = doubled + trailing
                break
        text = ' '.join(words)
    
    return text


@app.route("/api/chat/reply", methods=["POST"])
def chat_reply():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []
    warmup = bool(data.get("warmup"))
    single_message = bool(data.get("singleMessage"))
    reply_to_user = bool(data.get("replyToUser"))
    topic = (data.get("topic") or get_chat_topic() or "").strip()
    last_speaker = (data.get("lastSpeaker") or "").strip()
    all_participants = data.get("participants") or []

    if not message and not warmup:
        return {"error": "Please share a message so the room can reply."}, 400

    api_key = get_deepseek_api_key().strip()
    if not api_key:
        # Fallback responses when no API key is configured
        import random
        short_fallbacks = [
            {"sender": "Peer", "role": "peer", "text": "hey! glad ur here 😊"},
            {"sender": "Peer", "role": "peer", "text": "just sitting with my thoughts today"},
            {"sender": "Peer", "role": "peer", "text": "you've got this!! 💪"},
            {"sender": "Peer", "role": "peer", "text": "yeah same tbh"},
            {"sender": "Peer", "role": "peer", "text": "been a rough one ngl"},
            {"sender": "Peer", "role": "peer", "text": "trying to stay focused lol"},
            {"sender": "Peer", "role": "peer", "text": "feeling pretty low tonite"},
            {"sender": "Peer", "role": "peer", "text": "anxiety's been hitting diferent lately"},
            {"sender": "Peer", "role": "peer", "text": "we're all in this together ❤️"},
            {"sender": "Peer", "role": "peer", "text": "just vibing honestly"},
            {"sender": "Peer", "role": "peer", "text": "lowkey strugglign but im here"},
            {"sender": "Peer", "role": "peer", "text": "anyone else procrastinating rn? 😅"},
            {"sender": "Peer", "role": "peer", "text": "thats so real"},
            {"sender": "Peer", "role": "peer", "text": "mood lmao"},
            {"sender": "Peer", "role": "peer", "text": "fr fr"},
            {"sender": "Peer", "role": "peer", "text": "felt that tbh"},
            {"sender": "Peer", "role": "peer", "text": "omg sameee"},
            {"sender": "Peer", "role": "peer", "text": "yesss exactly"},
            {"sender": "Peer", "role": "peer", "text": "ughhh i feel u"},
            {"sender": "Peer", "role": "peer", "text": "honestly tho"},
            {"sender": "Peer", "role": "peer", "text": "sooo true lol"},
            {"sender": "Peer", "role": "peer", "text": "wait what happend?"},
            {"sender": "Peer", "role": "peer", "text": "oh nooo"},
            {"sender": "Peer", "role": "peer", "text": "thats rough ngl"},
        ]
        return {"messages": [random.choice(short_fallbacks)]}

    replies, error = deepseek_chat_reply(
        api_key, message, history, 
        warmup=warmup, 
        topic=topic, 
        single_message=single_message,
        reply_to_user=reply_to_user,
        last_speaker=last_speaker,
        all_participants=all_participants
    )
    if error:
        # Return error flag so frontend can handle silently
        return {"messages": [], "error": "temporarily_unavailable"}

    return {"messages": replies}


@app.route("/api/chat/generate-names", methods=["POST"])
def generate_chat_names():
    """Generate random unique names for chat participants using AI"""
    data = request.get_json(silent=True) or {}
    count = min(int(data.get("count") or 8), 15)  # Max 15 names
    
    api_key = get_deepseek_api_key().strip()
    
    if not api_key:
        # Fallback to predefined diverse names
        import random
        fallback_names = [
            "Sky", "River", "Ash", "Quinn", "Jade", "Rain", "Storm", "Brook",
            "Wren", "Ember", "Luna", "Nova", "Kai", "Zara", "Finn", "Ivy",
            "Leo", "Milo", "Arlo", "Eden", "Sage", "Willow", "Phoenix", "Rowan",
            "Jasper", "Hazel", "Riley", "Jordan", "Casey", "Morgan", "Taylor", "Drew"
        ]
        random.shuffle(fallback_names)
        return {"names": fallback_names[:count]}
    
    # Use AI to generate unique, natural names
    prompt = f"""Generate {count} unique first names for a peer support chat room. 
Requirements:
- Mix of common and unique names
- Gender-neutral or varied genders
- Different cultural backgrounds represented
- Names that feel real and relatable (not weird/made-up)
- Names a young adult (18-30) might have
- NO names from this list: Alex, Jordan, Sam, Taylor (too common)

Return ONLY a JSON array of strings with just the first names, like:
["Luna", "Kai", "River", "Zara", "Marcus", "Priya", "Finn", "Ava"]

Generate {count} completely different names each time - be creative!"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You generate realistic names. Respond with only JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 1.0,  # High temperature for variety
        "max_tokens": 200,
    }

    try:
        request_data = json.dumps(payload).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        req = urlrequest.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=request_data,
            headers=request_headers,
        )
        with urlrequest.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        content = (result.get("choices") or [{}])[0].get("message", {}).get("content", "")
        
        # Parse the response
        names = None
        try:
            names = json.loads(content.strip())
        except json.JSONDecodeError:
            # Try to extract array from content
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1:
                try:
                    names = json.loads(content[start:end+1])
                except json.JSONDecodeError:
                    pass
        
        if isinstance(names, list) and len(names) > 0:
            # Filter to valid strings and limit length
            valid_names = [str(n).strip()[:20] for n in names if isinstance(n, str) and n.strip()]
            if valid_names:
                return {"names": valid_names[:count]}
        
        # Fallback if parsing failed
        import random
        fallback = ["Luna", "Kai", "River", "Zara", "Marcus", "Priya", "Finn", "Ava", "Noah", "Maya", "Leo", "Iris"]
        random.shuffle(fallback)
        return {"names": fallback[:count]}
        
    except Exception as e:
        print(f"Name generation error: {e}")
        import random
        fallback = ["Sky", "River", "Quinn", "Ember", "Nova", "Kai", "Zara", "Finn", "Ivy", "Milo"]
        random.shuffle(fallback)
        return {"names": fallback[:count]}


@app.route("/useful-contacts")
def useful_contacts():
    contacts = load_useful_contacts()
    tags = sorted({tag for contact in contacts for tag in contact.get("all_tags", [])})
    return render_template(
        "useful_contacts.html", contacts=contacts, contact_tags=tags
    )


@app.route("/calming-tools")
def calming_tools():
    return render_template(
        "calming_tools.html",
        tool_cards=calming_tool_cards(),
        tools=calming_tools_with_counts(),
    )


@app.route("/tools/<slug>")
def calming_tool(slug):
    page = next((tool for tool in CALMING_TOOL_PAGES if tool["slug"] == slug), None)
    if not page:
        return redirect(url_for("calming_tools"))

    counts = load_calming_counts()
    count_slug = page.get("count_slug") or slug
    tool_data = find_calming_tool(count_slug)
    count_data = counts.get(count_slug, {"completed": 0, "views": 0})

    return render_template(
        page["template"],
        tool=page,
        tool_data=tool_data,
        completed_count=count_data.get("completed", 0),
        view_count=count_data.get("views", 0),
    )


@app.route("/community")
def community():
    return render_template("community.html", highlights=COMMUNITY_HIGHLIGHTS)


@app.route("/crisis")
def crisis_info():
    return render_template("crisis.html")



def build_dataset_summary(books):
    return {
        "books": [
            {
                "title": book.get("title", "Untitled"),
                "author": book.get("author", ""),
                "affiliate_url": book.get("affiliate_url", ""),
            }
            for book in books
        ]
    }


def render_admin_page(message=None, save_summary=None, load_summary=None, section=None):
    view_counts = load_book_view_counts()
    books = books_with_indices(load_books(), view_counts=view_counts)
    charities = load_charities()
    charity_activities = load_charity_activities()
    did_you_know_items = load_did_you_know_items()
    media_assets = load_media_assets()
    calming_tools = calming_tools_with_counts()
    useful_contacts = load_useful_contacts()
    books_with_covers = sum(1 for book in books if book.get("cover_url"))
    books_without_covers = len(books) - books_with_covers
    books_per_row = 4

    return render_template(
        "admin.html",
        books=books,
        message=message,
        books_with_covers=books_with_covers,
        books_without_covers=books_without_covers,
        books_per_row=books_per_row,
        calming_tools=calming_tools,
        charities=charities,
        charity_activities=charity_activities,
        did_you_know_items=did_you_know_items,
        media_assets=media_assets,
        useful_contacts=useful_contacts,
        save_summary=save_summary,
        load_summary=load_summary,
        construction_banner_enabled=construction_banner_enabled(),
        active_section=section,
        deepseek_api_key=get_deepseek_api_key(),
        deepseek_api_key_masked=mask_secret(get_deepseek_api_key()),
        chat_enabled=chat_enabled(),
        chat_topic=get_chat_topic(),
        chat_next_session=get_chat_next_session(),
        chat_rules=get_chat_rules(),
        chat_blocked_words=get_chat_blocked_words(),
        chat_block_action=get_chat_block_action(),
    )


@app.route("/admin")
def admin():
    message = request.args.get("message")
    section = request.args.get("section")
    return render_admin_page(message=message, section=section)


@app.route("/admin/site-banner", methods=["POST"])
def update_site_banner():
    enabled = bool(request.form.get("construction_banner"))
    set_construction_banner(enabled)
    banner_message = "Construction banner turned on." if enabled else "Construction banner turned off."

    return redirect(url_for("admin", message=banner_message))


@app.route("/admin/deepseek-key", methods=["POST"])
def update_deepseek_api_key():
    api_key = request.form.get("deepseek_api_key", "").strip()
    save_site_setting(DEEPSEEK_SETTING_KEY, api_key)

    if api_key:
        message = "DeepSeek API key saved."
    else:
        message = "DeepSeek API key cleared."

    return redirect(url_for("admin", message=message, section="ai-tools"))


@app.route("/admin/chat-settings", methods=["POST"])
def update_chat_settings():
    enabled = request.form.get("chat_enabled") == "on"
    topic = request.form.get("chat_topic", "").strip()
    next_session = request.form.get("chat_next_session", "").strip()
    rules = request.form.get("chat_rules", "").strip()
    blocked_words = request.form.get("chat_blocked_words", "").strip()
    block_action = request.form.get("chat_block_action", "warn").strip()

    set_chat_enabled(enabled)
    set_chat_topic(topic)
    set_chat_next_session(next_session)
    set_chat_rules(rules)
    set_chat_blocked_words(blocked_words)
    set_chat_block_action(block_action)

    message = "Chat room settings saved."
    return redirect(url_for("admin", message=message, section="chat-room"))


@app.route("/api/chat/check-message", methods=["POST"])
def check_chat_message():
    """Check if a message is allowed before sending"""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    
    is_safe, violation_type = check_message_content(message)
    
    if is_safe:
        return {"allowed": True}
    else:
        # Return violation type so frontend can show appropriate message
        return {"allowed": False, "violation": violation_type}


@app.route("/admin/did-you-know", methods=["POST"])
def add_did_you_know_item():
    headline = request.form.get("headline", "").strip()
    detail = request.form.get("detail", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = normalize_support_link(request.form.get("cta_url", ""))

    if not headline:
        return redirect(url_for("admin", message="Please add a headline for the Did you know? item."))

    d1_query(
        """
        INSERT INTO did_you_know_items (headline, detail, cta_label, cta_url)
        VALUES (?, ?, ?, ?)
        """,
        [headline, detail, cta_label, cta_url],
    )

    return redirect(url_for("admin", message="Did you know? item added."))


@app.route("/admin/did-you-know/<int:item_id>/delete", methods=["POST"])
def delete_did_you_know_item(item_id):
    d1_query("DELETE FROM did_you_know_items WHERE id = ?", [item_id])
    return redirect(url_for("admin", message="Did you know? item removed."))


@app.route("/admin/did-you-know/<int:item_id>/update", methods=["POST"])
def update_did_you_know_item(item_id):
    headline = request.form.get("headline", "").strip()
    detail = request.form.get("detail", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = normalize_support_link(request.form.get("cta_url", ""))

    if not headline:
        return redirect(url_for("admin", message="Please include a headline before saving."))

    d1_query(
        """
        UPDATE did_you_know_items
        SET headline = ?, detail = ?, cta_label = ?, cta_url = ?
        WHERE id = ?
        """,
        [headline, detail, cta_label, cta_url, item_id],
    )

    return redirect(url_for("admin", message="Did you know? item updated."))


@app.route("/admin/useful-contacts", methods=["POST"])
def add_useful_contact_admin():
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    text_number = request.form.get("text_number", "").strip()
    tags = request.form.get("tags", "")
    description = request.form.get("description", "").strip()

    if not name:
        return redirect(
            url_for("admin", message="Please add a name for the contact.", section="useful-contacts")
        )

    is_valid, error_message = validate_useful_contact_channels(
        telephone, text_number, contact_email
    )
    if not is_valid:
        return redirect(
            url_for("admin", message=error_message, section="useful-contacts")
        )

    if useful_contact_exists(name, telephone, contact_email):
        return redirect(
            url_for(
                "admin",
                message="That contact already exists. Try editing the existing entry instead.",
                section="useful-contacts",
            )
        )

    save_useful_contact(
        {
            "name": name,
            "telephone": telephone,
            "contact_email": contact_email,
            "text_number": text_number,
            "tags": tags,
            "description": description,
        }
    )

    return redirect(url_for("admin", message="Contact added.", section="useful-contacts"))


@app.route("/admin/useful-contacts/<int:contact_id>/update", methods=["POST"])
def update_useful_contact_admin(contact_id):
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    text_number = request.form.get("text_number", "").strip()
    tags = request.form.get("tags", "")
    description = request.form.get("description", "").strip()

    if not name:
        return redirect(
            url_for("admin", message="Please add a name for the contact.", section="useful-contacts")
        )

    is_valid, error_message = validate_useful_contact_channels(
        telephone, text_number, contact_email
    )
    if not is_valid:
        return redirect(
            url_for("admin", message=error_message, section="useful-contacts")
        )

    update_useful_contact(
        contact_id,
        {
            "name": name,
            "telephone": telephone,
            "contact_email": contact_email,
            "text_number": text_number,
            "tags": tags,
            "description": description,
        },
    )

    return redirect(url_for("admin", message="Contact updated.", section="useful-contacts"))


@app.route("/admin/useful-contacts/<int:contact_id>/delete", methods=["POST"])
def delete_useful_contact_admin(contact_id):
    delete_useful_contact(contact_id)
    return redirect(url_for("admin", message="Contact removed.", section="useful-contacts"))


@app.route("/admin/useful-contacts/ai", methods=["POST"])
def ai_useful_contact_admin():
    topic = request.form.get("topic", "").strip() or "urgent mental health helplines"
    api_key = get_deepseek_api_key().strip()

    if not api_key:
        return redirect(
            url_for(
                "admin",
                message="Please save a DeepSeek API key before requesting AI suggestions.",
                section="useful-contacts",
            )
        )

    existing = load_useful_contacts()
    existing_names = [contact.get("name", "") for contact in existing]
    ai_data, error = deepseek_useful_contact_lookup(api_key, topic, existing_names)

    if error:
        return redirect(url_for("admin", message=error, section="useful-contacts"))

    if not ai_data or not ai_data.get("name"):
        return redirect(
            url_for(
                "admin",
                message="The AI response was missing a name. Please try again.",
                section="useful-contacts",
            )
        )

    is_valid, error_message = validate_useful_contact_channels(
        ai_data.get("telephone"), ai_data.get("text_number"), ai_data.get("contact_email")
    )
    if not is_valid:
        return redirect(
            url_for("admin", message=error_message, section="useful-contacts")
        )

    if useful_contact_exists(ai_data.get("name"), ai_data.get("telephone"), ai_data.get("contact_email")):
        return redirect(
            url_for(
                "admin",
                message="That contact already exists. AI suggestions will skip duplicates.",
                section="useful-contacts",
            )
        )

    tags = ai_data.get("tags", [])
    if isinstance(tags, list):
        tags = ",".join(tags)

    save_useful_contact(
        {
            "name": ai_data.get("name", ""),
            "telephone": ai_data.get("telephone", ""),
            "contact_email": ai_data.get("contact_email", ""),
            "text_number": ai_data.get("text_number", ""),
            "tags": tags,
            "description": ai_data.get("description", ""),
        }
    )

    return redirect(url_for("admin", message="AI contact added.", section="useful-contacts"))


@app.route("/admin/media", methods=["POST"])
def add_media_asset():
    name = request.form.get("name", "").strip()
    media_type = normalize_media_type(request.form.get("media_type"))
    uploaded_url = store_uploaded_media(request.files.get("file"))
    url_input = request.form.get("url", "").strip()
    url = uploaded_url or normalize_url(url_input)
    description = request.form.get("description", "").strip()
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if not name or not media_type or not url:
        return redirect(
            url_for(
                "admin",
                message="Please include a name, upload or link, and whether this is an image or video.",
                section="media",
            )
        )

    existing = d1_query(
        "SELECT id FROM media_assets WHERE lower(name) = lower(?)",
        [name],
    )
    if existing:
        return redirect(
            url_for(
                "admin",
                message="A media asset with that name already exists. Update it instead.",
                section="media",
            )
        )

    d1_query(
        """
        INSERT INTO media_assets (name, media_type, url, description, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [name, media_type, url, description, created_at],
    )

    return redirect(url_for("admin", message="Media asset added.", section="media"))


@app.route("/admin/media/<int:asset_id>/update", methods=["POST"])
def update_media_asset(asset_id):
    assets = [asset for asset in load_media_assets() if asset.get("id") == asset_id]
    if not assets:
        return redirect(url_for("admin", message="Media asset not found.", section="media"))

    existing_asset = assets[0]

    name = request.form.get("name", "").strip() or existing_asset.get("name", "")
    media_type = normalize_media_type(request.form.get("media_type")) or existing_asset.get(
        "media_type", ""
    )
    uploaded_url = store_uploaded_media(request.files.get("file"))
    url_input = request.form.get("url", "").strip()
    url = uploaded_url or (normalize_url(url_input) if url_input else existing_asset.get("url", ""))
    description = request.form.get("description", "").strip() or existing_asset.get("description", "")

    if not name or not media_type or not url:
        return redirect(
            url_for(
                "admin",
                message="Please complete all fields before updating this media asset.",
                section="media",
            )
        )

    conflict = d1_query(
        "SELECT id FROM media_assets WHERE lower(name) = lower(?) AND id != ?",
        [name, asset_id],
    )
    if conflict:
        return redirect(
            url_for(
                "admin",
                message="Another asset is already using that name.",
                section="media",
            )
        )

    d1_query(
        """
        UPDATE media_assets
        SET name = ?, media_type = ?, url = ?, description = ?
        WHERE id = ?
        """,
        [name, media_type, url, description, asset_id],
    )

    if uploaded_url:
        remove_local_media_file(existing_asset.get("url"))

    return redirect(url_for("admin", message="Media asset updated.", section="media"))


@app.route("/admin/media/<int:asset_id>/delete", methods=["POST"])
def delete_media_asset(asset_id):
    assets = [asset for asset in load_media_assets() if asset.get("id") == asset_id]
    for asset in assets:
        remove_local_media_file(asset.get("url"))

    d1_query("DELETE FROM media_assets WHERE id = ?", [asset_id])
    return redirect(url_for("admin", message="Media asset removed.", section="media"))


@app.route("/admin/activities", methods=["POST"])
def add_charity_activity():
    organisation_name = request.form.get("organisation_name", "").strip()
    activity_name = request.form.get("activity_name", "").strip()
    activity_type = request.form.get("activity_type", "").strip()
    details = request.form.get("details", "").strip()

    if not organisation_name or not activity_name:
        return redirect(
            url_for("admin", message="Please provide an organisation and activity name."),
        )

    d1_query(
        """
        INSERT INTO charity_activities (organisation_name, activity_name, activity_type, details)
        VALUES (?, ?, ?, ?)
        """,
        [organisation_name, activity_name, activity_type, details],
    )

    return redirect(url_for("admin", message="Activity added."))


@app.route("/admin/activities/<int:activity_id>/delete", methods=["POST"])
def delete_charity_activity(activity_id):
    d1_query("DELETE FROM charity_activities WHERE id = ?", [activity_id])
    return redirect(url_for("admin", message="Activity removed."))


@app.route("/admin/activities/<int:activity_id>/update", methods=["POST"])
def update_charity_activity(activity_id):
    organisation_name = request.form.get("organisation_name", "").strip()
    activity_name = request.form.get("activity_name", "").strip()
    activity_type = request.form.get("activity_type", "").strip()
    details = request.form.get("details", "").strip()

    if not organisation_name or not activity_name:
        return redirect(
            url_for(
                "admin",
                message="Please include both an organisation and an activity name.",
            )
        )

    d1_query(
        """
        UPDATE charity_activities
        SET organisation_name = ?, activity_name = ?, activity_type = ?, details = ?
        WHERE id = ?
        """,
        [organisation_name, activity_name, activity_type, details, activity_id],
    )

    return redirect(url_for("admin", message="Activity updated."))


@app.route("/admin/charities", methods=["POST"])
def add_charity():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    website_url = normalize_url(request.form.get("website_url", ""))
    logo_url = resolve_media_url(
        request.form.get("logo_url", ""), request.form.get("logo_asset_url", "")
    )
    telephone = request.form.get("telephone", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    text_number = request.form.get("text_number", "").strip()
    helpline_hours = request.form.get("helpline_hours", "").strip()
    has_helpline = 1 if request.form.get("has_helpline") else 0
    has_volunteers = 1 if request.form.get("has_volunteers") else 0
    has_crisis_info = 1 if request.form.get("has_crisis_info") else 0
    has_text_support = 1 if request.form.get("has_text_support") else 0
    has_email_support = 1 if request.form.get("has_email_support") else 0
    has_live_chat = 1 if request.form.get("has_live_chat") else 0
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if not all([name, description, website_url]):
        return redirect(url_for("admin", message="Please complete all charity fields."))

    d1_query(
        """
        INSERT INTO charities (
            name,
            logo_url,
            description,
            website_url,
            created_at,
            telephone,
            contact_email,
            text_number,
            helpline_hours,
            has_helpline,
            has_volunteers,
            has_crisis_info,
            has_text_support,
            has_email_support,
            has_live_chat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            name,
            logo_url,
            description,
            website_url,
            created_at,
            telephone,
            contact_email,
            text_number,
            helpline_hours,
            has_helpline,
            has_volunteers,
            has_crisis_info,
            has_text_support,
            has_email_support,
            has_live_chat,
        ],
    )
    return redirect(url_for("admin", message="Charity added."))


@app.route("/admin/charities/<int:charity_id>/update", methods=["POST"])
def update_charity(charity_id):
    charities = load_charities()
    existing = next((c for c in charities if c.get("id") == charity_id), None)
    if not existing:
        return redirect(url_for("admin", message="Charity not found."))

    name = request.form.get("name", "").strip() or existing.get("name", "")
    description = request.form.get("description", "").strip() or existing.get("description", "")

    website_input = request.form.get("website_url", "").strip()
    website_url = normalize_url(website_input) if website_input else existing.get("website_url", "")

    logo_url = resolve_media_url(
        request.form.get("logo_url", "").strip() or existing.get("logo_url", ""),
        request.form.get("logo_asset_url", ""),
    ) or existing.get("logo_url", "")

    telephone = request.form.get("telephone", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    text_number = request.form.get("text_number", "").strip()
    helpline_hours = request.form.get("helpline_hours", "").strip()
    has_helpline = 1 if request.form.get("has_helpline") else 0
    has_volunteers = 1 if request.form.get("has_volunteers") else 0
    has_crisis_info = 1 if request.form.get("has_crisis_info") else 0
    has_text_support = 1 if request.form.get("has_text_support") else 0
    has_email_support = 1 if request.form.get("has_email_support") else 0
    has_live_chat = 1 if request.form.get("has_live_chat") else 0

    if not all([name, description, website_url]):
        return redirect(url_for("admin", message="Please complete all charity fields."))

    d1_query(
        """
        UPDATE charities
        SET
            name = ?,
            logo_url = ?,
            description = ?,
            website_url = ?,
            telephone = ?,
            contact_email = ?,
            text_number = ?,
            helpline_hours = ?,
            has_helpline = ?,
            has_volunteers = ?,
            has_crisis_info = ?,
            has_text_support = ?,
            has_email_support = ?,
            has_live_chat = ?
        WHERE id = ?
        """,
        [
            name,
            logo_url,
            description,
            website_url,
            telephone,
            contact_email,
            text_number,
            helpline_hours,
            has_helpline,
            has_volunteers,
            has_crisis_info,
            has_text_support,
            has_email_support,
        has_live_chat,
        charity_id,
    ],
    )
    return redirect(url_for("admin", message="Charity updated."))


def build_charity_ai_update(existing, ai_data):
    telephone = ai_data.get("telephone") if isinstance(ai_data, dict) else None
    contact_email = ai_data.get("contact_email") if isinstance(ai_data, dict) else None
    text_number = ai_data.get("text_number") if isinstance(ai_data, dict) else None
    helpline_hours = ai_data.get("helpline_hours") if isinstance(ai_data, dict) else None
    logo_url = ai_data.get("logo_url") if isinstance(ai_data, dict) else None

    def resolve_boolean(key, current):
        if isinstance(ai_data, dict) and key in ai_data:
            return 1 if coerce_bool(ai_data.get(key)) else 0
        return 1 if current else 0

    updates = {
        "telephone": telephone.strip() if isinstance(telephone, str) else existing.get("telephone", ""),
        "contact_email": contact_email.strip() if isinstance(contact_email, str) else existing.get("contact_email", ""),
        "text_number": text_number.strip() if isinstance(text_number, str) else existing.get("text_number", ""),
        "helpline_hours": helpline_hours.strip() if isinstance(helpline_hours, str) else existing.get("helpline_hours", ""),
        "logo_url": normalize_url(logo_url) if logo_url else existing.get("logo_url", ""),
        "has_helpline": resolve_boolean("has_helpline", existing.get("has_helpline")),
        "has_volunteers": resolve_boolean("has_volunteers", existing.get("has_volunteers")),
        "has_crisis_info": resolve_boolean("has_crisis_info", existing.get("has_crisis_info")),
        "has_text_support": resolve_boolean("has_text_support", existing.get("has_text_support")),
        "has_email_support": resolve_boolean("has_email_support", existing.get("has_email_support")),
        "has_live_chat": resolve_boolean("has_live_chat", existing.get("has_live_chat")),
    }

    return updates


@app.route("/admin/charities/<int:charity_id>/enrich", methods=["POST"])
def enrich_charity(charity_id):
    charities = load_charities()
    existing = next((c for c in charities if c.get("id") == charity_id), None)
    if not existing:
        return redirect(url_for("admin", message="Charity not found.", section="charities"))

    api_key = get_deepseek_api_key().strip()
    if not api_key:
        return redirect(
            url_for(
                "admin",
                message="Add a DeepSeek API key before running an AI lookup.",
                section="ai-tools",
            )
        )

    ai_data, error = deepseek_charity_lookup(api_key, existing)
    if error:
        return redirect(url_for("admin", message=error, section="charities"))

    updates = build_charity_ai_update(existing, ai_data or {})

    d1_query(
        """
        UPDATE charities
        SET
            telephone = ?,
            contact_email = ?,
            text_number = ?,
            helpline_hours = ?,
            logo_url = ?,
            has_helpline = ?,
            has_volunteers = ?,
            has_crisis_info = ?,
            has_text_support = ?,
            has_email_support = ?,
            has_live_chat = ?
        WHERE id = ?
        """,
        [
            updates["telephone"],
            updates["contact_email"],
            updates["text_number"],
            updates["helpline_hours"],
            updates["logo_url"],
            updates["has_helpline"],
            updates["has_volunteers"],
            updates["has_crisis_info"],
            updates["has_text_support"],
            updates["has_email_support"],
            updates["has_live_chat"],
            charity_id,
        ],
    )

    return redirect(
        url_for(
            "admin",
            message="Charity details refreshed with DeepSeek.",
            section="charities",
        )
    )


@app.route("/admin/charities/<int:charity_id>/delete", methods=["POST"])
def delete_charity(charity_id):
    d1_query("DELETE FROM charities WHERE id = ?", [charity_id])
    return redirect(url_for("admin", message="Charity removed."))


@app.route("/admin/save-data", methods=["POST"])
def snapshot_save():
    books = load_books()
    save_books(books)

    save_summary = build_dataset_summary(books)
    return render_admin_page(message="Data saved to the database.", save_summary=save_summary)


@app.route("/admin/load-data", methods=["POST"])
def snapshot_load():
    books = load_books()
    load_summary = build_dataset_summary(books)

    return render_admin_page(message="Data loaded from the database.", load_summary=load_summary)


@app.route("/admin/books/scrape", methods=["POST"])
def scrape_book():
    book_url = request.form.get("book_url", "").strip()
    if not book_url:
        return redirect(url_for("admin", message="Please provide a book URL to scrape."))

    book, error = scrape_book_metadata(book_url)
    if error:
        return redirect(url_for("admin", message=error))

    books = load_books()
    books.append(book)
    save_books(books)

    return redirect(url_for("admin", message="Book scraped and added.", section="books"))


@app.route("/admin/books", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    description = request.form.get("description", "").strip()
    affiliate_url = normalize_url(request.form.get("affiliate_url", ""))
    cover_url = resolve_media_url(
        request.form.get("cover_url", ""),
        request.form.get("cover_asset_url", ""),
    )

    if not all([title, author, description, affiliate_url]):
        return redirect(url_for("admin", message="Please fill in all book fields."))

    books = load_books()
    books.append(
        {
            "title": title,
            "author": author,
            "description": description,
            "affiliate_url": affiliate_url,
            "cover_url": cover_url,
        }
    )
    save_books(books)
    return redirect(url_for("admin", message="Book added.", section="books"))


@app.route("/admin/books/<int:book_index>/delete", methods=["POST"])
def delete_book(book_index):
    books = load_books()
    if 0 <= book_index < len(books):
        books.pop(book_index)
        save_books(books)
        return redirect(url_for("admin", message="Book removed.", section="books"))
    return redirect(url_for("admin", message="Book not found.", section="books"))


@app.route("/admin/books/delete-all", methods=["POST"])
def delete_all_books():
    save_books([])
    return redirect(url_for("admin", message="All books removed.", section="books"))


@app.route("/admin/books/<int:book_index>/update", methods=["POST"])
def update_book(book_index):
    books = load_books()
    if not (0 <= book_index < len(books)):
        return redirect(url_for("admin", message="Book not found.", section="books"))

    existing_book = books[book_index]

    title = request.form.get("title", "").strip() or existing_book.get("title", "")
    author = request.form.get("author", "").strip() or existing_book.get("author", "")
    description = request.form.get("description", "").strip() or existing_book.get("description", "")

    affiliate_input = request.form.get("affiliate_url", "").strip()
    affiliate_url = (
        normalize_url(affiliate_input) if affiliate_input else existing_book.get("affiliate_url", "")
    )

    cover_url = resolve_media_url(
        request.form.get("cover_url", "").strip() or existing_book.get("cover_url", ""),
        request.form.get("cover_asset_url", ""),
    ) or existing_book.get("cover_url", "")

    if not all([title, author, description, affiliate_url]):
        return redirect(url_for("admin", message="Please complete all book fields to update."))

    books[book_index] = {
        "title": title,
        "author": author,
        "description": description,
        "affiliate_url": affiliate_url,
        "cover_url": cover_url,
    }
    save_books(books)
    return redirect(url_for("admin", message="Book updated.", section="books"))


@app.route("/calming-tools/<slug>/complete", methods=["POST"])
def track_calming_completion(slug):
    counts = load_calming_counts()
    if slug not in counts:
        return {"success": False, "message": "Exercise not found."}, 404

    entry = normalize_calming_entry(counts.get(slug, {}))
    entry["completed"] = (entry.get("completed", 0) or 0) + 1
    counts[slug] = entry
    save_calming_counts(counts)
    return {"success": True, "completed_count": entry.get("completed", 0), "view_count": entry.get("views", 0)}


@app.route("/calming-tools/<slug>/view", methods=["POST"])
def track_calming_view(slug):
    counts = load_calming_counts()
    if slug not in counts:
        return {"success": False, "message": "Exercise not found."}, 404

    entry = normalize_calming_entry(counts.get(slug, {}))
    entry["views"] = (entry.get("views", 0) or 0) + 1
    counts[slug] = entry
    save_calming_counts(counts)
    return {
        "success": True,
        "view_count": entry.get("views", 0),
        "completed_count": entry.get("completed", 0),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
