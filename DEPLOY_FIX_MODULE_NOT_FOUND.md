# Fix for ModuleNotFoundError: No module named 'backend'

This error means Render cannot see the `backend` folder from the root of your GitHub repository.

## Correct GitHub structure

When you open the GitHub repository, you must immediately see:

```text
backend
frontend
data
requirements.txt
render.yaml
runtime.txt
Procfile
```

Do not upload one big folder that contains these files inside it.

## Correct Render Start Command

Use:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Correct Build Command

Use:

```bash
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

## After fixing GitHub

Go to Render:

Manual Deploy > Clear build cache and deploy
