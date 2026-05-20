# ECCE AskDesk Uganda — Render-Safe Deploy Build

This version is adjusted to fix Render dependency installation problems.

Use this version if Render failed with:

`encountered error while generating package metadata`

## Render settings

Build Command:
```bash
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

Start Command:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Health Check Path:
```text
/api/status
```

## Local test

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```
