# Deploying Attic Reader

Backend → Railway (Docker). Frontend → Railway now, Vercel optional. No auth, no storage.
Repo: https://github.com/rems3n/attic-reader

## Current deployment (2026-09-13)

Railway project `attic-reader` (workspace "remsen's Projects"), environment `production`,
both services deploy from branch `claude/attic-reader-handoff-wvfavt` on every push.

| Service | Root dir | Public URL | Notes |
|---|---|---|---|
| `backend` | `backend` | https://backend-production-d55b3.up.railway.app | Dockerfile, volume `hf-cache` at `/data`, `PORT=8000`, healthcheck `/health` |
| `web` | `frontend` | https://web-production-a1ef.up.railway.app | Dockerfile, `PORT=3000`, `NEXT_PUBLIC_API_BASE_URL` → backend URL |

Backend `CORS_ORIGINS=https://web-production-a1ef.up.railway.app,http://localhost:3000`.
Switching the branch to `main` later: Railway service → Settings → Source → Branch.

To move the frontend to Vercel instead, follow the Vercel section below, then add the
Vercel domain to `CORS_ORIGINS` and delete the `web` service on Railway.

## Backend (Railway) — dashboard walkthrough

1. https://railway.app → **New Project → Deploy from GitHub repo** → pick
   `rems3n/attic-reader` (authorize the Railway GitHub app if asked).
2. Open the new service → **Settings**:
   - **Source → Root Directory**: `backend`
     (`backend/railway.json` then selects the Dockerfile and the `/health` check).
   - **Source → Branch**: the branch you want deployed (`main` after merge).
   - **Networking → Generate Domain** → note it, e.g.
     `https://attic-reader-production.up.railway.app`.
   - **Resources**: at least **2 GB RAM** (Kokoro + torch ≈ 1.2 GB resident).
3. **Volumes** (service → right-click / `+ Volume`): mount path `/data`.
   HF model cache (~330 MB Kokoro + voice) lives there, so restarts are fast.
4. **Variables** (paste as raw editor):
   ```
   ENABLE_KOKORO=true
   KOKORO_VOICE=im_nicola
   KOKORO_LANG_CODE=i
   KOKORO_SPEED=0.92
   ENABLE_MMS=false
   ALLOW_ESPEAK_FALLBACK=false
   HF_HOME=/data/hf-cache
   OCR_PREPROCESS=opencv
   CORS_ORIGINS=http://localhost:3000
   ```
   (`CORS_ORIGINS` gets the Vercel domain added in step 7.)
5. Deploy. The Dockerfile installs the **CPU** torch wheel (image ≈ 1.5 GB;
   the default wheel would be 4+ GB). First synthesis downloads Kokoro to
   the volume (30–60 s), later ones take a few seconds per paragraph.
6. Verify:
   ```bash
   curl https://<railway-domain>/health            # {"status":"ok"}
   curl https://<railway-domain>/api/tts/status    # kokoro-attic available:true enabled:true
   ```

## Frontend (Vercel, optional alternative to the Railway `web` service)

1. https://vercel.com/new → **Import** `rems3n/attic-reader`.
2. **Root Directory**: `frontend` (Edit → pick the folder). Framework preset
   auto-detects Next.js.
3. **Environment Variables**:
   `NEXT_PUBLIC_API_BASE_URL` = `https://<railway-domain>` (no trailing slash).
4. Deploy → note the domain, e.g. `https://attic-reader.vercel.app`.
5. Optional: Settings → Git → Production Branch = `main`.

## Wire CORS (step 7)

On Railway set
`CORS_ORIGINS=https://<vercel-domain>,http://localhost:3000`
(add the `*-git-*.vercel.app` preview domain too if you use previews),
then **Redeploy** the backend.

## Smoke test

```bash
B=https://<railway-domain>
curl -s $B/health
curl -s $B/api/tts/status | python -m json.tool
curl -s -X POST $B/api/segment -H 'content-type: application/json' \
  -d '{"text":"ὁ Δικαιόπολις αὐτουργός ἐστιν. τί ποιεῖ;"}'
curl -s -X POST $B/api/synthesize -H 'content-type: application/json' \
  -d '{"text":"ὁ Δικαιόπολις αὐτουργός ἐστιν.","speed":1}' -o test.wav -D - | grep -i x-tts-provider
# expect: X-TTS-Provider: kokoro-attic ; test.wav plays
```

Then on the phone: open the Vercel URL → paste
`ὁ Δικαιόπολις αὐτουργός ἐστιν. τί ποιεῖ;` → **Generate neural audio** →
two sentences appear, the badge reads "Kokoro · direct Classical Attic
phonemes", tapping a sentence plays it, **Play all** advances with highlight.
Share → **Add to Home Screen** installs it as a standalone app.

## Costs

- Railway: no free tier for always-on services; Hobby is $5/month including
  $5 of usage. A 2 GB service idling ~24/7 runs roughly $5–10/month.
  Sleeping the service between uses lowers it (Settings → App Sleeping).
- Vercel Hobby: free for personal use.
