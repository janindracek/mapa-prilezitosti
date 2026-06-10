# RUNBOOK — hosting, redeploy & annual refresh (M7)

Operational guide for the live deployment. The *what/why* lives in `README.md` (§2 architecture, §8 pipeline). This is the *how-to-operate*.

---

## 0. What's deployed

- **One FastAPI service** (Render, `render.yaml`) — serves the API **and** the built React SPA from a single process (`api/server_full.py` mounts `ui/dist/` at `/`). No split frontend/backend.
- **Serving layer** (`data/serving/*.parquet`, ~43 MB) is *not* in the repo (gitignored). It is published as a **GitHub Release asset** (`serving.tar.gz`, marked *latest*) and the deploy downloads it.
- **Insights** (`/insights`): live Claude when `ANTHROPIC_API_KEY` is set; otherwise a deterministic Czech fallback (no network call, no error). See §5.

```
LOCAL (once/year)                         GitHub                         Render
rebuild-all.command → data/serving/  ──►  Release asset  ──►  build.sh downloads → builds UI → runs API
                    release-serving.sh     serving.tar.gz      (one process serves API + SPA)
```

---

## 1. First-time hosting setup (Render) — one-time, Jan's account

The repo is public; Render deploys from GitHub on push.

1. **Publish the serving layer first** (the deploy needs it):
   ```
   double-click rebuild-all.command          # regenerates data/serving/ (needs raw BACI locally)
   bash deploy/release-serving.sh            # uploads serving.tar.gz to a GitHub Release, marked latest
   ```
2. **Create the Render service** → New → Blueprint → pick this repo. Render reads `render.yaml`:
   - plan `free`, Python `3.12.7`, build `./deploy/build.sh`, start `uvicorn … --port $PORT`, health `/health`.
3. **Env vars** (Render dashboard → Environment): `PYTHON_VERSION`, `TRADE_UNITS_SCALE` come from `render.yaml`. Leave **`ANTHROPIC_API_KEY` unset** for the first deploy (insights run in fallback — fine for the infra check). Add it later as a **Secret** to turn on live Claude (§5).
4. **Deploy.** Watch the build log: deps → serving download (~40 MB) → `npm ci && npm run build` → API validate.
5. **Smoke-test the live URL:**
   ```
   ./_finalization/verify-deploy.command https://<service>.onrender.com
   ```
   All 7 checks must pass (§4). Then open the URL: the dashboard (Přehled / Analytika), not JSON.
6. **Bump the tier.** Once green, Render dashboard → Settings → Instance Type → **Starter** ($7/mo: no sleep, no cold start). Free works but sleeps after 15 min idle (~30 s first-click cold start) and is RAM-tight (~250–400 MB RSS vs 512 MB cap).

---

## 2. Redeploy (code change, no data change)

`ui/dist` is built on deploy; the serving layer is unchanged.

```
git push            # to the branch Render tracks (e.g. main)
```
Render auto-deploys. Or dashboard → **Manual Deploy → Deploy latest commit**. Then re-run `verify-deploy.command` against the URL.

> No serving re-upload needed unless the data changed (§3).

---

## 3. Annual refresh (new BACI year, or methodology change)

The heavy ETL runs **locally** (needs raw BACI in `data/parquet/`, `data/raw/`); only the small serving layer ships.

```
1. Update the BACI inputs locally (drop the new year into data/parquet/ etc.).
2. double-click rebuild-all.command
   → reruns 00→01→02→05→03b→04b→06b→07, asserts serving == ETL (9/9 integrity checks).
   Must end "✅ rebuild-all OK".
3. bash deploy/release-serving.sh
   → packages data/serving/ → new Release tag serving-YYYY-MM-DD, asset serving.tar.gz marked latest.
4. Trigger a redeploy (git push, or Render Manual Deploy). build.sh pulls the NEW latest asset.
5. ./_finalization/verify-deploy.command https://<service>.onrender.com  → all green.
```

Notes:
- `release-serving.sh` is **idempotent per day** — re-running clobbers the same-day asset.
- Old releases are left in place as history; only *latest* is fetched. Prune manually if desired (`gh release delete serving-YYYY-MM-DD`).
- Refresh cadence: roughly once a year, or whenever the statistical logic changes (README §1).

---

## 4. Smoke-test (`verify-deploy.command`)

```
./_finalization/verify-deploy.command [BASE_URL]
```
No arg → tests `http://127.0.0.1:8000` (a local prod build via `build-ui.command`). Asserts:

| # | Endpoint | Pass condition |
|---|----------|----------------|
| 1 | `GET /health` | `status: ok` |
| 2 | `GET /map_v2?hs6=870323&year=2023&metric=cz_share_in_partner_import` | ≥200 importers (full universe 226; per-product varies) |
| 3 | `GET /top_signals?country=DEU` | ≥1 signal (two-tier selection, ≤10, balanced types) |
| 4 | `GET /signals/all?limit=5` | total ≥50k (full ~108k set) |
| 5 | `GET /insights?importer=DEU&hs6=870323&year=2023` | non-empty Czech text |
| 6 | `GET /` | SPA HTML (`id="root"`) — **not** JSON |
| 7 | `GET /world.json` | 200 (bundled map geometry) |

---

## 5. Insights — live Claude vs fallback

- **Fallback (no key):** `/insights` returns deterministic Czech text. `_llm_generate` returns `None` immediately when `ANTHROPIC_API_KEY` is unset — no network call, no error.
- **Live Claude:** set `ANTHROPIC_API_KEY` (Render Secret) — `INSIGHTS_USE_LLM` defaults to on. Model via `INSIGHTS_MODEL` (default `claude-opus-4-8`). Key is **server-side only**, never shipped to the client.
- Rotating/removing the key transparently degrades to fallback.

> **Open (Jan):** the fallback currently *restates* dashboard numbers, which Jan finds low-value. Desired end state: AI-driven text, and on failure show a transparent "AI nedostupné" notice rather than a number-restating paragraph. Tracked as the one M7 follow-up; deliberately deferred until the infra deploy is verified green.

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Build fails at "Downloading serving layer" | No latest Release with `serving.tar.gz`. Run `deploy/release-serving.sh`. |
| `latest/download` 404 right after publish | ~20 s redirect propagation lag; `build.sh` resolves via the API to avoid it. Re-deploy if it raced. |
| Root URL shows `{"status":"ok"}` | A `/` route is shadowing the SPA. M7 removed the duplicate in `server_cors.py`; don't re-add one. |
| API boots but endpoints 500 / no data | Serving layer didn't extract. Check build log for the download + `du -sh data/serving`. |
| `ImportError: dotenv` | `python-dotenv` missing from `requirements.txt` (M7 added it). |
| pyarrow build-from-source / wheel error | Python must be 3.12 (`render.yaml`); pyarrow is pinned `==21.0.0` (has a cp312 wheel). |
| Insights paragraph restates the dashboard | Expected fallback (no key). Set `ANTHROPIC_API_KEY`, or see §5 open item. |
| First click slow (~30 s) on Free | Free tier sleeps after 15 min idle. Bump to Starter (§1.6). |
