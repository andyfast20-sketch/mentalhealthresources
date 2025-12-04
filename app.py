import json
import os
import sqlite3
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
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

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOCAL_DATA_DIR = Path.home() / ".mentalhealthresources"
LEGACY_LOCAL_DATA_DIR = BASE_DIR / "local_data"
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
    if url.startswith("http://") or url.startswith("https://"):
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


def scrape_book_metadata(book_url):
    normalized_url = normalize_url(book_url)
    if not normalized_url:
        return None, "Please provide a book URL."

    headers = {"User-Agent": "Mozilla/5.0"}
    request = urlrequest.Request(normalized_url, headers=headers)

    try:
        with urlrequest.urlopen(request, timeout=10) as response:  # nosec B310
            charset = extract_html_charset(response.headers)
            html = response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
        return None, f"Unable to fetch book page: {exc}"

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
            count INTEGER DEFAULT 0
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
            has_helpline INTEGER NOT NULL DEFAULT 0,
            has_volunteers INTEGER NOT NULL DEFAULT 0,
            has_crisis_info INTEGER NOT NULL DEFAULT 0,
            has_text_support INTEGER NOT NULL DEFAULT 0,
            has_email_support INTEGER NOT NULL DEFAULT 0,
            has_live_chat INTEGER NOT NULL DEFAULT 0
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
    ]

    for statement in table_statements:
        d1_query(statement)

    # Always mirror the schema in the local fallback database so queries keep
    # working even if Cloudflare D1 is configured but temporarily unreachable.
    connection = open_local_db()
    with connection:
        for statement in table_statements:
            connection.execute(statement)

    # Apply schema migrations to keep legacy databases aligned with the current model.
    with open_local_db() as connection:
        migrate_charities_schema_local(connection)

    migrate_charities_schema_remote()


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


def load_calming_counts():
    ensure_tables()

    rows = d1_query("SELECT slug, count FROM calming_counts")
    counts = {}
    for row in rows:
        slug = row.get("slug") if isinstance(row, dict) else None
        if slug:
            counts[slug] = int(row.get("count", 0) or 0)

    for tool in CALMING_TOOLS:
        slug = tool.get("slug", slugify(tool["title"]))
        counts.setdefault(slug, 0)

    save_calming_counts(counts)
    return counts


def save_calming_counts(counts):
    ensure_tables()
    d1_query("DELETE FROM calming_counts")

    for slug, count in counts.items():
        d1_query(
            "INSERT INTO calming_counts (slug, count) VALUES (?, ?)",
            [slug, int(count or 0)],
        )


def calming_tools_with_counts():
    counts = load_calming_counts()
    updated = {}
    tools_with_counts = []

    for tool in CALMING_TOOLS:
        slug = tool.get("slug", slugify(tool["title"]))
        count = counts.get(slug, 0)
        updated[slug] = count
        tools_with_counts.append({**tool, "slug": slug, "completed_count": count})

    if counts.keys() != updated.keys():
        save_calming_counts(updated)

    return tools_with_counts


def calming_tool_cards():
    counts = load_calming_counts()
    cards = []

    for page in CALMING_TOOL_PAGES:
        count_slug = page.get("count_slug") or page["slug"]
        cards.append({**page, "completed_count": counts.get(count_slug, 0)})

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
    completed_count = counts.get(count_slug, 0)

    return render_template(
        page["template"],
        tool=page,
        tool_data=tool_data,
        completed_count=completed_count,
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


def render_admin_page(message=None, save_summary=None, load_summary=None):
    view_counts = load_book_view_counts()
    books = books_with_indices(load_books(), view_counts=view_counts)
    charities = load_charities()
    charity_activities = load_charity_activities()
    did_you_know_items = load_did_you_know_items()
    calming_tools = calming_tools_with_counts()
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
        save_summary=save_summary,
        load_summary=load_summary,
        construction_banner_enabled=construction_banner_enabled(),
    )


@app.route("/admin")
def admin():
    message = request.args.get("message")
    return render_admin_page(message=message)


@app.route("/admin/site-banner", methods=["POST"])
def update_site_banner():
    enabled = bool(request.form.get("construction_banner"))
    set_construction_banner(enabled)
    banner_message = "Construction banner turned on." if enabled else "Construction banner turned off."

    return redirect(url_for("admin", message=banner_message))


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
    logo_url = normalize_url(request.form.get("logo_url", ""))
    telephone = request.form.get("telephone", "").strip()
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
            has_helpline,
            has_volunteers,
            has_crisis_info,
            has_text_support,
            has_email_support,
            has_live_chat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            name,
            logo_url,
            description,
            website_url,
            created_at,
            telephone,
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

    logo_input = request.form.get("logo_url", "").strip()
    logo_url = normalize_url(logo_input) if logo_input else existing.get("logo_url", "")

    telephone = request.form.get("telephone", "").strip()
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

    return redirect(url_for("admin", message="Book scraped and added."))


@app.route("/admin/books", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    description = request.form.get("description", "").strip()
    affiliate_url = normalize_url(request.form.get("affiliate_url", ""))
    cover_url = normalize_url(request.form.get("cover_url", ""))

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
    return redirect(url_for("admin", message="Book added."))


@app.route("/admin/books/<int:book_index>/delete", methods=["POST"])
def delete_book(book_index):
    books = load_books()
    if 0 <= book_index < len(books):
        books.pop(book_index)
        save_books(books)
        return redirect(url_for("admin", message="Book removed."))
    return redirect(url_for("admin", message="Book not found."))


@app.route("/admin/books/delete-all", methods=["POST"])
def delete_all_books():
    save_books([])
    return redirect(url_for("admin", message="All books removed."))


@app.route("/admin/books/<int:book_index>/update", methods=["POST"])
def update_book(book_index):
    books = load_books()
    if not (0 <= book_index < len(books)):
        return redirect(url_for("admin", message="Book not found."))

    existing_book = books[book_index]

    title = request.form.get("title", "").strip() or existing_book.get("title", "")
    author = request.form.get("author", "").strip() or existing_book.get("author", "")
    description = request.form.get("description", "").strip() or existing_book.get("description", "")

    affiliate_input = request.form.get("affiliate_url", "").strip()
    affiliate_url = (
        normalize_url(affiliate_input) if affiliate_input else existing_book.get("affiliate_url", "")
    )

    cover_input = request.form.get("cover_url", "").strip()
    cover_url = normalize_url(cover_input) if cover_input else existing_book.get("cover_url", "")

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
    return redirect(url_for("admin", message="Book updated."))


@app.route("/calming-tools/<slug>/complete", methods=["POST"])
def track_calming_completion(slug):
    counts = load_calming_counts()
    if slug not in counts:
        return {"success": False, "message": "Exercise not found."}, 404

    counts[slug] = (counts.get(slug, 0) or 0) + 1
    save_calming_counts(counts)
    return {"success": True, "completed_count": counts[slug]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
