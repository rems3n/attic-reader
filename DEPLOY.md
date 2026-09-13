# Deploying Attic Reader

Backend → Railway (Docker). Frontend → Vercel. No auth, no storage.

## Backend (Railway)
1. New project → Deploy from GitHub repo → root directory `backend`.
   `backend/railway.json` selects the Dockerfile and `/health` check.
2. Add a **Volume** mounted at `/data` (HF model cache, ~400 MB; keeps cold starts fast).
3. Variables:
   ```
   ENABLE_KOKORO=true
   KOKORO_VOICE=im_nicola
   KOKORO_LANG_CODE=i
   KOKORO_SPEED=0.92
   ENABLE_MMS=false
   ALLOW_ESPEAK_FALLBACK=false
   HF_HOME=/data/hf-cache
   CORS_ORIGINS=https://<your-vercel-domain>,http://localhost:3000
   ```
4. Plan: ≥2 GB RAM. First request downloads Kokoro (~330 MB) then caches on the volume.
5. Verify: `curl https://<railway-url>/health` → `{"status":"ok"}`, and
   `GET /api/tts/status` shows `kokoro-attic available:true`.

## Frontend (Vercel)
1. Import the repo, root directory `frontend`.
2. Env var: `NEXT_PUBLIC_API_BASE_URL=https://<railway-url>` (no trailing slash).
3. Deploy, then put the Vercel domain into `CORS_ORIGINS` on Railway and redeploy the backend.

## Smoke test
Open the Vercel URL on a phone → paste `ὁ Δικαιόπολις αὐτουργός ἐστιν.` → Generate → audio plays; the player shows the Kokoro provider name (not "unknown").
