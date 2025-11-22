from flask import Flask, render_template

app = Flask(__name__)

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

@app.route("/")
def index():
    return render_template("index.html", resources=RESOURCES)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
