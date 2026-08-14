# void-app

Void is a Windows desktop AI assistant with a live system HUD and a local agent that can control your PC.

## Architecture

| Package | Stack | Role |
|---------|-------|------|
| `void-desktop` | Electron + React + Vite + Three.js | Frameless HUD, chat UI, live metrics |
| `void-backend` | FastAPI + Groq + Gemini | Agent, Windows tools, system telemetry |

## Prerequisites

- Windows 10/11
- Python 3.11+
- Node.js 20+

## Backend setup

```bash
cd void-backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set:

- `GROQ_API_KEY` — required for chat and tool planning
- `GEMINI_API_KEY` — required for image attachment analysis

Start the server:

```bash
.\venv\Scripts\python -m uvicorn main:app --reload
```

The API runs at `http://localhost:8000`.

## Desktop setup

```bash
cd void-desktop
npm install
copy .env.example .env
npm run dev
```

Optional: set `VITE_VOID_API_URL` in `void-desktop/.env` if the backend is not on `http://localhost:8000`.

## Features

- Streaming chat with conversation history (persisted in localStorage)
- Image attachments analyzed by Gemini before the agent replies
- 13 Windows tools (open apps, file search, volume, theme, settings, etc.)
- User approval gate for system-changing actions
- Live CPU / GPU / RAM / network metrics over WebSocket

## Project layout

```
void-app/
├── void-backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment configuration
│   ├── models.py            # Request/response models
│   ├── routes/api.py        # HTTP + WebSocket routes
│   └── services/            # Agent, tools, apps, images, metrics
└── void-desktop/
    ├── electron/            # Main + preload
    └── src/                 # React UI
```
