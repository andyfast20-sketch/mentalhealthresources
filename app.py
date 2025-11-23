import json
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_DIR = Path("data")
CHARITIES_FILE = DATA_DIR / "charities.json"


DEFAULT_CHARITIES = [
    {
        "name": "Mind (UK)",
        "description": "Providing advice and empowering people experiencing mental health problems through helplines, advocacy, and community programs.",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Mind.svg/320px-Mind.svg.png",
        "site_url": "https://www.mind.org.uk/",
    },
    {
        "name": "NAMI",  # National Alliance on Mental Illness
        "description": "Education, support groups, and advocacy to build better lives for individuals and families affected by mental illness.",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/NAMI-Logo.svg/320px-NAMI-Logo.svg.png",
        "site_url": "https://www.nami.org/",
    },
    {
        "name": "The Trevor Project",
        "description": "Crisis intervention and suicide prevention services for LGBTQ+ young people, available 24/7 via phone, chat, and text.",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/The_Trevor_Project_logo.svg/320px-The_Trevor_Project_logo.svg.png",
        "site_url": "https://www.thetrevorproject.org/",
    },
]


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_charities():
    ensure_data_dir()
    if CHARITIES_FILE.exists():
        try:
            with CHARITIES_FILE.open() as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    save_charities(DEFAULT_CHARITIES)
    return DEFAULT_CHARITIES.copy()


def save_charities(charities):
    ensure_data_dir()
    with CHARITIES_FILE.open("w") as f:
        json.dump(charities, f, indent=2)

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
        "title": "Tension & Release",
        "description": "Relax each muscle group with a short squeeze and soften sequence.",
        "steps": [
            "Start at your hands: squeeze for five seconds, then release.",
            "Move to shoulders, face, and legs with the same pattern.",
            "Notice the warmth and heaviness after each release.",
        ],
    },
    {
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
]

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
    return render_template("home.html", resources=RESOURCES, charities=charities)


@app.route("/charities")
def charities():
    charities = load_charities()
    return render_template("charities.html", charities=charities)


@app.route("/resources")
def resources():
    return render_template("resources.html", resources=RESOURCES)


@app.route("/calming-tools")
def calming_tools():
    return render_template("calming_tools.html", tools=CALMING_TOOLS)


@app.route("/community")
def community():
    return render_template("community.html", highlights=COMMUNITY_HIGHLIGHTS)


@app.route("/admin")
def admin():
    charities = load_charities()
    message = request.args.get("message")
    return render_template("admin.html", charities=charities, message=message)


@app.route("/admin/charities", methods=["POST"])
def add_charity():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    site_url = request.form.get("site_url", "").strip()

    if not all([name, description, logo_url, site_url]):
        return redirect(url_for("admin", message="Please fill in all fields."))

    charities = load_charities()
    charities.append(
        {
            "name": name,
            "description": description,
            "logo_url": logo_url,
            "site_url": site_url,
        }
    )
    save_charities(charities)
    return redirect(url_for("admin", message="Charity added successfully."))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
