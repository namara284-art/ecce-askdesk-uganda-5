# Deploy ECCE AskDesk Uganda to Render

This package is deploy-ready. The backend serves the frontend, so you only need one Render Web Service.

## 1. Create a GitHub repository

1. Go to GitHub.
2. Create a new repository, for example: `ecce-askdesk-uganda`.
3. Upload all files from this folder into the repository.

Make sure these files are at the top level of the repository:
- backend/
- frontend/
- data/
- requirements.txt
- render.yaml
- runtime.txt

## 2. Deploy on Render

1. Go to Render.
2. Create a new Web Service.
3. Connect your GitHub repository.
4. Use these settings:

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Health Check Path:
```text
/api/status
```

5. Click Deploy.

## 3. Open the live site

When deployment finishes, Render will give you a live URL.

Open the URL. The ECCE AskDesk homepage should load directly.

## 4. Test the site

Try:
- Home
- Use the Tool
- FAQs
- Resources
- Feedback
- Support

Then ask:
```text
Who licenses pre-primary schools?
```

## 5. Optional: add resource documents

This lightweight deploy-ready package does not include large policy documents. To activate the Resource Library local downloads, add these files to:

```text
frontend/resources/
```

Use these exact names:
```text
ECCE-Policy-2025-Signed.pdf
BRMS-Pre-Primary-Schools-Uganda-February-2025.docx
```

## 6. Custom domain later

After the site is live, you can connect a custom domain in Render settings.
