# Deployment Guide for ECCE AskDesk v0.2

## Simple online demo path

Backend: Render
Frontend: Netlify or Vercel

### Backend on Render
1. Upload this folder to GitHub.
2. Create a Render Web Service.
3. Build command: pip install -r requirements.txt
4. Start command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
5. Deploy and copy the backend URL.

### Frontend
1. Open frontend/index.html.
2. Replace:
const API="http://127.0.0.1:8000";
with your Render backend URL.
3. Upload the frontend folder to Netlify or Vercel.

## Before public deployment
- Replace demo admin token.
- Move data to PostgreSQL or Supabase.
- Add admin authentication.
- Add privacy notice.
- Get MoES/delegated technical review for public release.
