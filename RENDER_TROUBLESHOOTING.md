# Render Troubleshooting

If Render says `encountered error while generating package metadata` or `build failed`, the issue is usually dependency installation.

Use these exact Render settings:

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

If the build still fails, confirm `runtime.txt` contains `python-3.12.8`, then in Render click Manual Deploy > Clear build cache and deploy.
