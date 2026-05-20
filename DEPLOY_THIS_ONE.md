# Deploy this fixed build

This build fixes the Internal Server Error by using a clean root-level `app.py`.

## GitHub structure

When you open GitHub, you must immediately see:

```text
app.py
frontend
data
requirements.txt
render.yaml
runtime.txt
Procfile
```

## Render settings

Build Command:

```bash
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

Start Command:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port $PORT
```

Leave Pre-deploy Command empty.

Leave Root Directory empty.

## After upload

In Render, redeploy. If available, choose Clear build cache and deploy.
