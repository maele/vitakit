# VitaKit — the open-source CV studio

A free, privacy-friendly CV builder. Write on the left, watch the page update
on the right, hit **PDF** and you're done. No accounts, no paywalls, no watermarks —
your data stays on your machine (browser autosave + plain JSON files on the server).

## Features (v0.2)
- Split editor with **live A4 preview** (debounced server-side rendering)
- **All the sections that matter**: experience, industry experience, projects,
  education, certifications, skills, tools, languages, interests, **references**
- **Print-to-PDF** via the browser's native print pipeline
- Autosave to `localStorage` + shareable server links (`/c/<id>`)
- JSON **import / export** (your CV is portable forever)
- Reorderable entries, bullet-line syntax (`- item`), language level picker
- Accent colour picker, "CV strength" meter, zoom, sample data, mobile Edit/Preview tabs

## Quickstart
```bash
git clone <your-repo> vitakit && cd vitakit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py          # → http://127.0.0.1:5000
