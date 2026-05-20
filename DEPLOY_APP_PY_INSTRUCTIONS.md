# Deploy ECCE AskDesk using app.py

This build avoids the `No module named backend` problem.

## What must appear at the top level of GitHub

When you open the GitHub repository, you must immediately see:

```text
app.py
backend
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

Health Check Path:

```text
/api/status
```

## Very important

Delete the old files from GitHub first, then upload this package. Do not upload the outer folder. Open the unzipped folder, select everything inside it, and upload those files.
