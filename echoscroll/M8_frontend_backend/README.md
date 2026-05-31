# M8 · Frontend + Backend (skeleton)

Self-contained React + FastAPI skeleton for the EchoScroll web application
(see proposal §3.3.1). All endpoints are **stubs** returning plausible fake
data; wire them to M1-M7 later.

## Run backend

```bash
cd M8_frontend_backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Backend listens on `http://localhost:8000`. On startup it creates
`/tmp/echoscroll/stub.wav` (a 10 s 220 Hz sine) and the upload / audio dirs.

Endpoints:

| Method | Path              | Purpose                                              |
| ------ | ----------------- | ---------------------------------------------------- |
| POST   | `/upload`         | multipart image + metadata → `painting_id`           |
| POST   | `/generate`       | painting_id → audio URL, V-A, descriptors, RAG hits  |
| POST   | `/edit/va`        | V-A retarget → new audio URL                         |
| POST   | `/edit/prompt`    | colloquial prompt → descriptors + audio URL          |
| POST   | `/edit/humming`   | multipart wav → MIDI contour, tonal center, cents    |
| GET    | `/audio/{id}`     | serves the stub wav                                  |
| GET    | `/preview/{id}`   | serves the uploaded painting                         |
| WS     | `/ws/preview`     | streams stage-by-stage generation progress events    |

## Run frontend

```bash
cd M8_frontend_backend/frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`. Vite proxies `/upload`, `/generate`,
`/edit/*`, `/audio/*`, `/preview/*` and `/ws/*` to the backend on port 8000,
so no CORS or env-var setup is required for the local demo.

## Layout

```
M8_frontend_backend/
├── backend/
│   ├── main.py          FastAPI app + stubbed routes
│   ├── schemas.py       Pydantic request/response models
│   └── requirements.txt
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── types.ts
        └── components/
            ├── UploadPanel.tsx
            ├── VAPanel.tsx
            ├── WaveformView.tsx
            ├── PromptBox.tsx
            ├── HummingRecorder.tsx
            └── styles.css
```

## Wiring to M1-M7

Each stub route is marked with `# TODO: wire to M*` in `backend/main.py`.
Replace the body of the route, keeping the Pydantic response shape intact,
and the frontend will work unchanged.
