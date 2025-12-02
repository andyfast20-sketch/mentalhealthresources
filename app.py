import json
import os
import random
import sqlite3
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from uuid import uuid4

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
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOCAL_DATA_DIR = Path.home() / ".mentalhealthresources"
LEGACY_LOCAL_DATA_DIR = BASE_DIR / "local_data"
CHARITIES_FILE = DATA_DIR / "charities.json"
BOOKS_FILE = DATA_DIR / "books.json"
LOCAL_CHARITIES_FILE = LOCAL_DATA_DIR / "charities.json"
LOCAL_BOOKS_FILE = LOCAL_DATA_DIR / "books.json"
LEGACY_LOCAL_CHARITIES_FILE = LEGACY_LOCAL_DATA_DIR / "charities.json"
LEGACY_LOCAL_BOOKS_FILE = LEGACY_LOCAL_DATA_DIR / "books.json"
CALMING_COUNTS_FILE = LOCAL_DATA_DIR / "calming_counts.json"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
CHARITY_ASPECTS_FILE = DATA_DIR / "charity_aspects.json"
LOCAL_CHARITY_ASPECTS_FILE = LOCAL_DATA_DIR / "charity_aspects.json"
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "YOUR_TOKEN_HERE")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "YOUR_ACCOUNT_ID")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID", "YOUR_DATABASE_ID")
D1_BASE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"
)
D1_CONFIGURED = not any(
    placeholder in value
    for placeholder, value in {
        "YOUR_TOKEN": CF_API_TOKEN,
        "YOUR_ACCOUNT": CF_ACCOUNT_ID,
        "YOUR_DATABASE": CF_D1_DATABASE_ID,
    }.items()
)
LOCAL_FALLBACK_DB = LOCAL_DATA_DIR / "d1_fallback.sqlite"


DEFAULT_CHARITIES = []

DEFAULT_CHARITY_ASPECTS = [
    "Website",
    "Helpline",
    "Live Chat",
    "Textline",
    "Resource Library",
]

DEFAULT_BOOKS = [
    {
        "title": "Atlas of the Heart",
        "author": "Brené Brown",
        "description": "A compassionate guide through 87 emotions and experiences, helping readers name what they feel and find language for connection.",
        "affiliate_url": "https://amzn.to/3K6C0Lk",
        "cover_url": "https://m.media-amazon.com/images/I/71+Jx1gIdwL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "Maybe You Should Talk to Someone",
        "author": "Lori Gottlieb",
        "description": "A therapist pulls back the curtain on her own sessions and reminds us therapy is a courageous act of care.",
        "affiliate_url": "https://amzn.to/4bj8QEv",
        "cover_url": "https://m.media-amazon.com/images/I/81PxgyrpFZL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "The Body Keeps the Score",
        "author": "Bessel van der Kolk",
        "description": "Evidence-based insights on how trauma lives in the body and the healing pathways that restore safety.",
        "affiliate_url": "https://amzn.to/3yOaYDh",
        "cover_url": "https://m.media-amazon.com/images/I/81dQwQlmAXL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "Set Boundaries, Find Peace",
        "author": "Nedra Glover Tawwab",
        "description": "Practical scripts and exercises to set limits with compassion, reduce overwhelm, and protect your energy.",
        "affiliate_url": "https://amzn.to/3YVn1ch",
        "cover_url": "https://m.media-amazon.com/images/I/71m3C1AI+8L._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "Burnout: The Secret to Unlocking the Stress Cycle",
        "author": "Emily Nagoski & Amelia Nagoski",
        "description": "Research-backed strategies for completing the stress cycle, especially for caregivers and high achievers.",
        "affiliate_url": "https://amzn.to/3WklwZg",
        "cover_url": "https://m.media-amazon.com/images/I/71A4HVWjQBL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "Emotional Agility",
        "author": "Susan David",
        "description": "Science-backed tools to navigate emotions with curiosity and courage instead of getting stuck.",
        "affiliate_url": "https://amzn.to/3WOO5RW",
        "cover_url": "https://m.media-amazon.com/images/I/71kN7vR-4cL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "The Happiness Trap",
        "author": "Russ Harris",
        "description": "An introduction to Acceptance and Commitment Therapy that shows how to unhook from unhelpful thoughts.",
        "affiliate_url": "https://amzn.to/4c8gZNh",
        "cover_url": "https://m.media-amazon.com/images/I/71K9CsgY1QL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "What Happened to You?",
        "author": "Bruce D. Perry & Oprah Winfrey",
        "description": "A compassionate conversation about trauma, resilience, and the healing power of understanding.",
        "affiliate_url": "https://amzn.to/3KMV3r9",
        "cover_url": "https://m.media-amazon.com/images/I/81xG0LknQ+L._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "The Comfort Book",
        "author": "Matt Haig",
        "description": "Short, soothing reflections and reminders that hope can be found in small, everyday moments.",
        "affiliate_url": "https://amzn.to/3KJP3qH",
        "cover_url": "https://m.media-amazon.com/images/I/71lz6h6hysL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
    {
        "title": "Self-Compassion",
        "author": "Kristin Neff",
        "description": "Practical exercises for treating yourself with the same kindness you offer others.",
        "affiliate_url": "https://amzn.to/3WUgJRl",
        "cover_url": "https://m.media-amazon.com/images/I/71pPpM9VfNL._SL1500_.jpg",
        "view_count": 0,
        "scroll_count": 0,
    },
]


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


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


def load_charities_file():
    ensure_local_data_dir()
    ensure_data_dir()

    migrate_legacy_data(LEGACY_LOCAL_CHARITIES_FILE, LOCAL_CHARITIES_FILE)

    for source in (LOCAL_CHARITIES_FILE, CHARITIES_FILE):
        if source.exists():
            try:
                with source.open() as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                continue

    return None


def slugify(value):
    return "-".join(value.lower().split())


def ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def allowed_logo(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_LOGO_EXTENSIONS


def normalize_url(url):
    if not url:
        return ""
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"


def normalize_logo_url(url):
    if not url:
        return ""

    cleaned = url.strip()
    if cleaned.startswith("/static/uploads/"):
        return cleaned

    return normalize_url(cleaned)


def store_logo_file(logo_file):
    if not logo_file or not logo_file.filename:
        return None
    if not allowed_logo(logo_file.filename):
        return None

    ensure_upload_dir()
    filename = f"{uuid4().hex}_{secure_filename(logo_file.filename)}"
    logo_file.save(UPLOAD_DIR / filename)
    return f"/static/uploads/{filename}"


def delete_logo_file(logo_url):
    if not logo_url or not logo_url.startswith("/static/uploads/"):
        return

    file_path = BASE_DIR / logo_url.lstrip("/")
    if file_path.exists() and file_path.is_file():
        file_path.unlink()


def ensure_fallback_db():
    ensure_local_data_dir()
    if LOCAL_FALLBACK_DB.exists():
        return

    connection = sqlite3.connect(LOCAL_FALLBACK_DB)
    connection.close()


def normalize_result_set(result_payload):
    if isinstance(result_payload, list) and result_payload:
        first = result_payload[0]
        if isinstance(first, dict):
            return first.get("results", result_payload)
    return result_payload or []


def d1_query(sql, params=None):
    params = params or []

    if D1_CONFIGURED:
        headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"sql": sql, "params": params}).encode()

        try:
            request = urlrequest.Request(D1_BASE_URL, data=payload, headers=headers, method="POST")
            with urlrequest.urlopen(request, timeout=20) as response:  # nosec B310
                data = json.loads(response.read().decode())
            if not data.get("success", False):
                raise RuntimeError(data.get("errors", "Unknown D1 error"))
            return normalize_result_set(data.get("result"))
        except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"D1 query failed; using local fallback database. Details: {exc}")

    ensure_fallback_db()
    connection = sqlite3.connect(LOCAL_FALLBACK_DB)
    connection.row_factory = sqlite3.Row
    with connection:
        cursor = connection.execute(sql, params)
        if cursor.description:
            return [dict(row) for row in cursor.fetchall()]
    return []


def ensure_tables():
    ensure_local_data_dir()
    table_statements = [
        """
        CREATE TABLE IF NOT EXISTS charities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            logo_url TEXT NOT NULL,
            site_url TEXT NOT NULL,
            json_aspects TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT NOT NULL,
            affiliate_url TEXT NOT NULL,
            cover_url TEXT,
            view_count INTEGER DEFAULT 0,
            scroll_count INTEGER DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS calming_counts (
            slug TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        );
        """,
    ]

    for statement in table_statements:
        d1_query(statement)

    # Always mirror the schema in the local fallback database so queries keep
    # working even if Cloudflare D1 is configured but temporarily unreachable.
    ensure_fallback_db()
    connection = sqlite3.connect(LOCAL_FALLBACK_DB)
    with connection:
        for statement in table_statements:
            connection.execute(statement)


def save_charity_aspects(aspects):
    ensure_local_data_dir()
    with LOCAL_CHARITY_ASPECTS_FILE.open("w") as f:
        json.dump(aspects, f, indent=2)


def load_charity_aspects():
    ensure_local_data_dir()
    ensure_data_dir()

    for source in (LOCAL_CHARITY_ASPECTS_FILE, CHARITY_ASPECTS_FILE):
        if source.exists():
            try:
                with source.open() as f:
                    aspects = json.load(f)
                if isinstance(aspects, list) and aspects:
                    cleaned = []
                    seen = set()
                    for aspect in aspects:
                        label = str(aspect).strip()
                        if label and label not in seen:
                            cleaned.append(label)
                            seen.add(label)
                    if cleaned:
                        save_charity_aspects(cleaned)
                        return cleaned
            except json.JSONDecodeError:
                continue

    save_charity_aspects(DEFAULT_CHARITY_ASPECTS)
    return DEFAULT_CHARITY_ASPECTS


def parse_charity_aspects(form, aspects):
    return {aspect: form.get(f"aspect_{slugify(aspect)}") == "on" for aspect in aspects}


def ensure_charity_aspects(charities, aspects):
    for charity in charities:
        current = charity.get("aspects") or {}
        normalized = {}
        for aspect in aspects:
            default_value = aspect.lower() == "website" and bool(charity.get("site_url"))
            normalized[aspect] = bool(current.get(aspect, default_value))
        charity["aspects"] = normalized
    return charities


def deduplicate_charities(charities, aspects):
    deduped = []
    seen = {}

    for charity in charities:
        name = charity.get("name", "").strip()
        site_url = normalize_url(charity.get("site_url", ""))
        description = charity.get("description", "").strip()
        key = (name.lower(), site_url.lower())

        if key in seen:
            existing = seen[key]
            merged_aspects = {}
            existing_aspects = existing.get("aspects") or {}
            new_aspects = charity.get("aspects") or {}

            for aspect in aspects:
                merged_aspects[aspect] = bool(
                    existing_aspects.get(aspect) or new_aspects.get(aspect)
                )

            existing["aspects"] = merged_aspects
            if description and not existing.get("description"):
                existing["description"] = description
            if site_url and not existing.get("site_url"):
                existing["site_url"] = site_url
            if charity.get("logo_url") and not existing.get("logo_url"):
                existing["logo_url"] = charity.get("logo_url")
            continue

        clean_charity = {**charity, "name": name, "description": description, "site_url": site_url}
        deduped.append(clean_charity)
        seen[key] = clean_charity

    ensure_charity_aspects(deduped, aspects)
    return deduped


def migrate_legacy_data(legacy_path, new_path):
    if new_path.exists() or not legacy_path.exists():
        return

    new_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        new_path.write_bytes(legacy_path.read_bytes())
    except OSError:
        return


def load_charities():
    ensure_tables()
    charity_aspects = load_charity_aspects()

    rows = d1_query(
        "SELECT id, name, description, logo_url, site_url, json_aspects FROM charities ORDER BY id"
    )

    if not rows:
        charities_from_disk = load_charities_file()
        if charities_from_disk:
            charities_from_disk = deduplicate_charities(charities_from_disk, charity_aspects)
            save_charities(charities_from_disk)
            rows = d1_query(
                "SELECT id, name, description, logo_url, site_url, json_aspects FROM charities ORDER BY id"
            )

    charities = []
    for row in rows:
        raw_aspects = row.get("json_aspects") if isinstance(row, dict) else None
        try:
            aspects = json.loads(raw_aspects) if raw_aspects else {}
        except json.JSONDecodeError:
            aspects = {}

        charities.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "name": row.get("name", ""),
                "description": row.get("description", ""),
                "logo_url": row.get("logo_url", ""),
                "site_url": row.get("site_url", ""),
                "aspects": aspects,
            }
        )

    cleaned_charities = deduplicate_charities(charities, charity_aspects)
    if len(cleaned_charities) != len(charities):
        save_charities(cleaned_charities)

    return cleaned_charities


def save_charities(charities):
    ensure_tables()
    charity_aspects = load_charity_aspects()
    charities = deduplicate_charities(charities, charity_aspects)

    ensure_local_data_dir()
    with LOCAL_CHARITIES_FILE.open("w") as f:
        json.dump(charities, f, indent=2)

    d1_query("DELETE FROM charities")

    for charity in charities:
        aspects_json = json.dumps(charity.get("aspects") or {})
        d1_query(
            """
            INSERT INTO charities (name, description, logo_url, site_url, json_aspects)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                charity.get("name", ""),
                charity.get("description", ""),
                charity.get("logo_url", ""),
                charity.get("site_url", ""),
                aspects_json,
            ],
        )


def load_books():
    ensure_tables()

    rows = d1_query(
        """
        SELECT id, title, author, description, affiliate_url, cover_url, view_count, scroll_count
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
                SELECT id, title, author, description, affiliate_url, cover_url, view_count, scroll_count
                FROM books
                ORDER BY id
                """
            )
        else:
            return []

    books = []
    for row in rows:
        books.append(
            {
                "id": row.get("id") if isinstance(row, dict) else None,
                "title": row.get("title", ""),
                "author": row.get("author", ""),
                "description": row.get("description", ""),
                "affiliate_url": row.get("affiliate_url", ""),
                "cover_url": row.get("cover_url", ""),
                "view_count": (row.get("view_count", 0) or 0),
                "scroll_count": (row.get("scroll_count", 0) or 0),
            }
        )

    return books


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
            existing["view_count"] = (existing.get("view_count", 0) or 0) + (
                book.get("view_count", 0) or 0
            )
            existing["scroll_count"] = (existing.get("scroll_count", 0) or 0) + (
                book.get("scroll_count", 0) or 0
            )
            if not existing.get("cover_url") and book.get("cover_url"):
                existing["cover_url"] = book.get("cover_url")
            continue

        clean_book = book.copy()
        clean_book["view_count"] = int(clean_book.get("view_count", 0) or 0)
        clean_book["scroll_count"] = int(clean_book.get("scroll_count", 0) or 0)
        seen[key] = clean_book
        deduped.append(clean_book)

    return deduped


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
            INSERT INTO books (title, author, description, affiliate_url, cover_url, view_count, scroll_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                book.get("title", ""),
                book.get("author", ""),
                book.get("description", ""),
                book.get("affiliate_url", ""),
                book.get("cover_url", ""),
                int(book.get("view_count", 0) or 0),
                int(book.get("scroll_count", 0) or 0),
            ],
        )


def pick_featured_books(books, count=3):
    if len(books) <= count:
        return list(range(len(books)))

    weights = [(book.get("view_count", 0) or 0) + 1 for book in books]
    selected_indices = []
    available_indices = list(range(len(books)))

    while len(selected_indices) < count and available_indices:
        choice = random.choices(available_indices, weights=[weights[i] for i in available_indices], k=1)[0]
        selected_indices.append(choice)
        available_indices.remove(choice)

    return selected_indices


def books_with_indices(books):
    return [{**book, "index": idx} for idx, book in enumerate(books)]

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
]


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
        ]
    }


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
    charities = load_charities()
    featured_charities = random.sample(charities, min(3, len(charities))) if charities else []
    books = load_books()
    books = books_with_indices(books)
    return render_template(
        "home.html",
        resources=RESOURCES,
        charities=featured_charities,
        all_charities=charities,
        books=books,
    )


@app.route("/charities")
def charities():
    charities = load_charities()
    charity_aspects = load_charity_aspects()
    return render_template("charities.html", charities=charities, charity_aspects=charity_aspects)


@app.route("/books")
def books():
    book_list = books_with_indices(load_books())
    return render_template("books.html", books=book_list)


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



def build_dataset_summary(charities, books):
    return {
        "charities": [
            {"name": charity.get("name", "Untitled"), "site_url": charity.get("site_url", "")}
            for charity in charities
        ],
        "books": [
            {
                "title": book.get("title", "Untitled"),
                "author": book.get("author", ""),
                "affiliate_url": book.get("affiliate_url", ""),
            }
            for book in books
        ],
    }


def render_admin_page(message=None, save_summary=None, load_summary=None):
    charities = load_charities()
    books = load_books()
    charity_aspects = load_charity_aspects()
    calming_tools = calming_tools_with_counts()
    total_book_interactions = sum(
        (book.get("view_count", 0) or 0) + (book.get("scroll_count", 0) or 0)
        for book in books
    )
    books_with_covers = sum(1 for book in books if book.get("cover_url"))
    books_without_covers = len(books) - books_with_covers
    books_per_row = 4

    return render_template(
        "admin.html",
        charities=charities,
        books=books,
        message=message,
        total_book_interactions=total_book_interactions,
        books_with_covers=books_with_covers,
        books_without_covers=books_without_covers,
        books_per_row=books_per_row,
        calming_tools=calming_tools,
        charity_aspects=charity_aspects,
        save_summary=save_summary,
        load_summary=load_summary,
    )


@app.route("/admin")
def admin():
    message = request.args.get("message")
    return render_admin_page(message=message)


@app.route("/admin/save-data", methods=["POST"])
def snapshot_save():
    charities = load_charities()
    books = load_books()
    save_charities(charities)
    save_books(books)

    save_summary = build_dataset_summary(charities, books)
    return render_admin_page(message="Data saved to the database.", save_summary=save_summary)


@app.route("/admin/load-data", methods=["POST"])
def snapshot_load():
    charities = load_charities()
    books = load_books()
    load_summary = build_dataset_summary(charities, books)

    return render_admin_page(message="Data loaded from the database.", load_summary=load_summary)


@app.route("/admin/charities/aspects", methods=["POST"])
def update_charity_aspects():
    raw_aspects = request.form.get("aspect_list", "")
    aspect_candidates = raw_aspects.replace("\n", ",").split(",")

    cleaned = []
    seen = set()
    for aspect in aspect_candidates:
        label = aspect.strip()
        if label and label not in seen:
            cleaned.append(label)
            seen.add(label)

    if not cleaned:
        cleaned = DEFAULT_CHARITY_ASPECTS

    save_charity_aspects(cleaned)

    charities = load_charities()
    ensure_charity_aspects(charities, cleaned)
    save_charities(charities)

    return redirect(url_for("admin", message="Charity columns updated."))


@app.route("/admin/charities", methods=["POST"])
def add_charity():
    charity_aspects = load_charity_aspects()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    logo_url = normalize_logo_url(request.form.get("logo_url", ""))
    site_url = normalize_url(request.form.get("site_url", ""))
    aspect_values = parse_charity_aspects(request.form, charity_aspects)

    logo_file = request.files.get("logo_file")

    if logo_file and logo_file.filename:
        if not allowed_logo(logo_file.filename):
            return redirect(url_for("admin", message="Logo must be an image file."))
        logo_url = store_logo_file(logo_file)

    if not all([name, description, site_url]) or not logo_url:
        return redirect(url_for("admin", message="Please fill in all fields."))

    charities = load_charities()
    charities.append(
        {
            "name": name,
            "description": description,
            "logo_url": logo_url,
            "site_url": site_url,
            "aspects": aspect_values,
        }
    )
    save_charities(charities)
    return redirect(url_for("admin", message="Charity added successfully."))


@app.route("/admin/charities/<int:charity_index>/delete", methods=["POST"])
def delete_charity(charity_index):
    charities = load_charities()
    charity_id = request.form.get("charity_id")
    target_index = None

    if charity_id:
        try:
            charity_id_int = int(charity_id)
        except ValueError:
            charity_id_int = None
        if charity_id_int is not None:
            for idx, charity in enumerate(charities):
                if charity.get("id") == charity_id_int:
                    target_index = idx
                    break

    if target_index is None and 0 <= charity_index < len(charities):
        target_index = charity_index

    if target_index is not None and 0 <= target_index < len(charities):
        removed = charities.pop(target_index)
        save_charities(charities)
        delete_logo_file(removed.get("logo_url"))
        return redirect(url_for("admin", message="Charity removed."))
    return redirect(url_for("admin", message="Charity not found."))


@app.route("/admin/charities/delete-all", methods=["POST"])
def delete_all_charities():
    save_charities([])
    return redirect(url_for("admin", message="All charities removed."))


@app.route("/admin/charities/<int:charity_index>/update", methods=["POST"])
def update_charity(charity_index):
    charity_aspects = load_charity_aspects()
    charities = load_charities()
    if not (0 <= charity_index < len(charities)):
        return redirect(url_for("admin", message="Charity not found."))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    site_url = normalize_url(request.form.get("site_url", ""))
    logo_url = normalize_logo_url(request.form.get("logo_url", ""))
    logo_file = request.files.get("logo_file")
    aspect_values = parse_charity_aspects(request.form, charity_aspects)

    if logo_file and logo_file.filename:
        if not allowed_logo(logo_file.filename):
            return redirect(url_for("admin", message="Logo must be an image file."))
        new_logo_url = store_logo_file(logo_file)
        delete_logo_file(charities[charity_index].get("logo_url"))
    elif logo_url:
        new_logo_url = logo_url
    else:
        new_logo_url = charities[charity_index].get("logo_url")

    if not all([name, description, site_url, new_logo_url]):
        return redirect(url_for("admin", message="Please complete all fields to update."))

    charities[charity_index] = {
        "name": name,
        "description": description,
        "logo_url": new_logo_url,
        "site_url": site_url,
        "aspects": aspect_values,
    }
    save_charities(charities)
    return redirect(url_for("admin", message="Charity updated."))


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
            "view_count": 0,
            "scroll_count": 0,
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
        "view_count": existing_book.get("view_count", 0),
        "scroll_count": existing_book.get("scroll_count", 0),
    }
    save_books(books)
    return redirect(url_for("admin", message="Book updated."))


@app.route("/books/<int:book_index>/view", methods=["POST"])
def track_book_view(book_index):
    books = load_books()
    if not (0 <= book_index < len(books)):
        return {"success": False, "message": "Book not found."}, 404

    books[book_index]["view_count"] = (books[book_index].get("view_count", 0) or 0) + 1
    save_books(books)
    return {"success": True, "view_count": books[book_index]["view_count"]}


@app.route("/books/<int:book_index>/scroll", methods=["POST"])
def track_book_scroll(book_index):
    books = load_books()
    if not (0 <= book_index < len(books)):
        return {"success": False, "message": "Book not found."}, 404

    books[book_index]["scroll_count"] = (books[book_index].get("scroll_count", 0) or 0) + 1
    save_books(books)
    return {"success": True, "scroll_count": books[book_index]["scroll_count"]}


@app.route("/admin/books/<int:book_index>/reset_views", methods=["POST"])
def reset_book_views(book_index):
    books = load_books()
    if not (0 <= book_index < len(books)):
        return redirect(url_for("admin", message="Book not found."))

    books[book_index]["view_count"] = 0
    books[book_index]["scroll_count"] = 0
    save_books(books)
    return redirect(url_for("admin", message="Book counters reset."))


@app.route("/calming-tools/<slug>/complete", methods=["POST"])
def track_calming_completion(slug):
    counts = load_calming_counts()
    if slug not in counts:
        return {"success": False, "message": "Exercise not found."}, 404

    counts[slug] = (counts.get(slug, 0) or 0) + 1
    save_calming_counts(counts)
    return {"success": True, "completed_count": counts[slug]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
