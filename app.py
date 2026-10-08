"""VitaKit — an open-source CV studio.

v0.2: full section set — experience, education, projects, certifications,
skills, tools, languages, industries, interests, references.
Run:  python app.py
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MAX_PAYLOAD_BYTES = 300 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")

BASIC_KEYS = ("name", "title", "email", "phone", "location", "website", "summary")

# (section, field-keys, max items) — list-of-object sections
LIST_SPECS = (
    ("experience",     ("role", "company", "start", "end", "details"), 40),
    ("education",      ("degree", "school", "start", "end", "details"), 20),
    ("projects",       ("name", "link", "details"), 20),
    ("certifications", ("name", "issuer", "year"), 20),
    ("references",     ("name", "role", "organization", "email", "phone"), 10),
    ("languages",      ("name", "level"), 12),
    ("socials",        ("label", "url"), 12),
)
# (section, max items) — list-of-string sections (comma / newline separated)
STR_LIST_SPECS = (("skills", 60), ("tools", 60), ("industries", 40), ("interests", 30))

DEFAULT_ACCENT = "#0E7C66"


def blank_cv() -> dict:
    return {
        "meta": {"accent": DEFAULT_ACCENT},
        "basics": {k: "" for k in BASIC_KEYS},
        **{src: [] for src, _, _ in LIST_SPECS},
        **{name: [] for name, _ in STR_LIST_SPECS},
    }


SAMPLE_CV = {
    "meta": {"accent": DEFAULT_ACCENT},
    "basics": {
        "name": "Alex Rivera",
        "title": "Senior Product Designer",
        "email": "alex.rivera@example.com",
        "phone": "+351 912 555 032",
        "location": "Lisbon, Portugal",
        "website": "alexrivera.design",
        "summary": (
            "Product designer with eight years of experience shaping B2B and consumer "
            "tools. I lead with research, sweat the details, and build design systems "
            "that let teams move fast without losing coherence."
        ),
    },
    "experience": [
        {
            "role": "Senior Product Designer",
            "company": "Northwind Labs",
            "start": "Mar 2021",
            "end": "Present",
            "details": (
                "- Led the redesign of the analytics suite, lifting weekly active usage by 34%\n"
                "- Built and documented a 120-component design system adopted by five product teams\n"
                "- Run continuous discovery interviews with 20+ customers per quarter"
            ),
        },
        {
            "role": "Product Designer",
            "company": "Fern & Field",
            "start": "Jun 2018",
            "end": "Feb 2021",
            "details": (
                "- Owned end-to-end design for a marketplace serving 40k monthly buyers\n"
                "- Shipped an onboarding flow that cut time-to-first-purchase from 9 to 3 minutes\n"
                "- Partnered with engineering to reach WCAG 2.1 AA across the storefront"
            ),
        },
        {
            "role": "UI Designer",
            "company": "Studio Kelp",
            "start": "Sep 2016",
            "end": "May 2018",
            "details": (
                "- Delivered brand and web design for 25+ early-stage clients\n"
                "- Introduced component libraries that halved design-to-dev handoff time"
            ),
        },
    ],
    "education": [
        {
            "degree": "BA (Hons) Communication Design",
            "school": "Lisbon School of Arts",
            "start": "2012",
            "end": "2016",
            "details": "Graduated with distinction; thesis on typography for screens.",
        },
        {
            "degree": "Interaction Design Specialization",
            "school": "UC San Diego (Coursera)",
            "start": "2019",
            "end": "2019",
            "details": "",
        },
    ],
    "projects": [
        {
            "name": "OpenShelf",
            "link": "github.com/arivera/openshelf",
            "details": (
                "- Open-source catalogue tool for community libraries\n"
                "- Designed and built the MVP with two contributors; 1.2k stars on GitHub"
            ),
        },
        {
            "name": "Design Lisbon Meetup",
            "link": "designlisbon.pt",
            "details": "- Co-organiser of a monthly 120-person design community meetup",
        },
    ],
    "certifications": [
        {"name": "NN/g UX Certification", "issuer": "Nielsen Norman Group", "year": "2022"},
        {"name": "Google UX Design Professional Certificate", "issuer": "Google", "year": "2020"},
    ],
    "skills": [
        "Figma", "Design systems", "Prototyping", "User research", "Usability testing",
        "HTML & CSS", "Accessibility", "Motion design", "Workshop facilitation",
    ],
    "tools": ["Figma", "FigJam", "Miro", "Notion", "Jira", "Linear", "Maze", "Framer"],
    "languages": [
        {"name": "Portuguese", "level": "Native"},
        {"name": "English", "level": "Fluent"},
        {"name": "Spanish", "level": "Professional"},
    ],
    "socials": [
        {"label": "GitHub",   "url": "github.com/arivera"},
        {"label": "LinkedIn", "url": "linkedin.com/in/alexrivera"},
        {"label": "Dribbble", "url": "dribbble.com/arivera"},
    ],
    "industries": ["SaaS", "Fintech", "E-commerce", "Marketplaces", "EdTech"],
    "interests": ["Analog photography", "Trail running", "Typography", "Ceramics"],
    "references": [
        {
            "name": "Sofia Almeida",
            "role": "Head of Design",
            "organization": "Northwind Labs",
            "email": "sofia.almeida@northwind.example",
            "phone": "+351 912 000 111",
        },
        {
            "name": "Marcus Chen",
            "role": "Product Lead",
            "organization": "Fern & Field",
            "email": "marcus.chen@fernfield.example",
            "phone": "",
        },
    ],
}


# --------------------------------------------------------------------------
# Sanitising / persistence
# --------------------------------------------------------------------------

def _clip(value: object, limit: int = 4000) -> str:
    if value is None:
        return ""
    return str(value)[:limit].strip()


def normalize_cv(raw: object) -> dict:
    """Coerce arbitrary input into a safe, well-formed CV dict."""
    raw = raw if isinstance(raw, dict) else {}
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    basics = raw.get("basics") if isinstance(raw.get("basics"), dict) else {}

    cv = blank_cv()

    accent = _clip(meta.get("accent"), 12)
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", accent or "#"):
        cv["meta"]["accent"] = accent

    for key in BASIC_KEYS:
        cv["basics"][key] = _clip(basics.get(key))

    for src, keys, cap in LIST_SPECS:
        items = raw.get(src)
        if isinstance(items, list):
            for item in items[:cap]:
                if isinstance(item, dict):
                    cv[src].append({k: _clip(item.get(k)) for k in keys})

    for name, cap in STR_LIST_SPECS:
        value = raw.get(name)
        if isinstance(value, str):
            value = re.split(r"[,\n]", value)
        if isinstance(value, list):
            cv[name] = [s for s in (_clip(x, 60) for x in value[:cap + 20]) if s][:cap]

    return cv


def cv_path(cv_id: str) -> Path:
    return DATA_DIR / f"{cv_id}.json"


def load_cv(cv_id: str | None) -> dict | None:
    if not cv_id or not ID_RE.match(cv_id):
        return None
    path = cv_path(cv_id)
    if not path.exists():
        return None
    try:
        return normalize_cv(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None


def save_cv(cv_id: str, cv: dict) -> None:
    cv_path(cv_id).write_text(
        json.dumps(cv, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def request_json() -> dict:
    if request.content_length and request.content_length > MAX_PAYLOAD_BYTES:
        abort(400, "Payload too large")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Invalid JSON")
    return data


# --------------------------------------------------------------------------
# Template filters
# --------------------------------------------------------------------------

@app.template_filter("bullets")
def bullets_filter(text: str):
    """Return a bullet list if every non-empty line starts with '-'."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if lines and all(ln.startswith("-") for ln in lines):
        return [ln.lstrip("-").strip() for ln in lines]
    return None


@app.template_filter("anyfield")
def anyfield_filter(items: list):
    return [it for it in items if any(str(v).strip() for v in it.values())]


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/")
def editor_new():
    return render_template("index.html", cv=SAMPLE_CV, cv_id=None,
                           sample=SAMPLE_CV, blank=blank_cv())


@app.get("/e/<cv_id>")
def editor_existing(cv_id: str):
    cv = load_cv(cv_id)
    if cv is None:
        return redirect(url_for("editor_new"))
    return render_template("index.html", cv=cv, cv_id=cv_id,
                           sample=SAMPLE_CV, blank=blank_cv())


@app.get("/c/<cv_id>")
def view(cv_id: str):
    cv = load_cv(cv_id)
    if cv is None:
        abort(404)
    return render_template("cv_document.html", cv=cv, standalone=True, cv_id=cv_id)


@app.post("/api/render")
def api_render():
    data = request_json()
    cv = normalize_cv(data.get("cv", data))
    return render_template("cv_document.html", cv=cv, standalone=False, cv_id=None)


@app.post("/api/save")
def api_save():
    data = request_json()
    cv = normalize_cv(data.get("cv"))
    cv_id = data.get("id") if isinstance(data.get("id"), str) else None
    if not cv_id or not ID_RE.match(cv_id):
        cv_id = uuid.uuid4().hex[:12]
    save_cv(cv_id, cv)
    return jsonify({
        "id": cv_id,
        "url": f"/c/{cv_id}",
        "editUrl": f"/e/{cv_id}",
    })


@app.get("/api/cv/<cv_id>")
def api_get(cv_id: str):
    cv = load_cv(cv_id)
    if cv is None:
        abort(404)
    return jsonify(cv)


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5051)
