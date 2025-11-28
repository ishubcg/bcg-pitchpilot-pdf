# PitchDeck Recommender (Static Frontend + FastAPI Backend)

## Structure
```
pitchdeck-tool/
├─ backend/                # FastAPI API (catalog + generate)
│  ├─ app.py
│  ├─ recommender.py
│  ├─ requirements.txt
│  └─ product_folder/      # put your skeleton.pptx + product decks here
└─ frontend-static/        # Static web (Tailwind + vanilla JS)
   ├─ index.html
   └─ app.js
```

## Run backend
```bash
cd backend
python -m venv .venv
# activate venv (Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

## Run frontend (static)
Open `frontend-static/index.html` in Live Server (VS Code extension) or any static file server.
Alternatively, start a simple server:
```bash
cd frontend-static
python -m http.server 5173
# open http://localhost:5173
```
> The frontend calls the backend at http://localhost:8000

## Inputs
- Industry (dropdown from `/api/catalog`)
- Annual budget in INR
- Bandwidth (Mbps)
- Products already sold (toggle chips)

## Output
Browser downloads **final_recommended_pitch.pptx** built from:
- `skeleton.pptx` (cover first, next steps last)
- recommended product decks (excluding already sold)

## Notes
This mirrors your static reference app style (Tailwind + vanilla JS), but wires to an API for generating the final deck server-side.
