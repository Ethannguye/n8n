# Social Factory — AI Video → Many Social Networks

**Status: working local demo + guarded Upload-Post publishing connector.** 2026-11-20.

A small, inspectable starter project for creating one vertical video and distributing it to many social channels. Built separately from the upstream tools; no third-party code is copied or passed off as ours.

**What actually works now**

- ✅ Local dashboard with per-platform selection for **14 upload targets**
- ✅ Make a downloadable **9-second MP4 preview** (3 original slides, 540×960, silent) from a topic *without* accounts, cloud credits, or paid keys
- ✅ Save review jobs in SQLite; preview, download and explicitly approve them
- ✅ Optionally call an **OpenAI-compatible** `/v1/chat/completions` gateway for script writing (FreeLLMAPI can be used when configured)
- ✅ Optional MoneyPrinterTurbo **CLI adapter** with its documented `mpt cli --video-script … --stop-at video` interface — requires installation, configured models, stock footage and TTS providers; **not tested end-to-end**
- ✅ Upload-Post **video multipart API adapter** following published API docs. Has a mandatory approval step, `ENABLE_LIVE_PUBLISH=true` opt-in, and `PUBLISH` confirmation. **No live social-account upload has been performed.**
- ✅ Distinguishes a successful provider submission from confirmed final publication; it does *not* fabricate post URLs, metrics, or platform access

**Not built / not promised yet**: a complete hosted SaaS, 100% automatic unattended publication, voiceovers or stock footage in offline demo, n8n workflows, Postiz-based publication, social logins/OAuth, automatic analytics, retries, Reddit posting, and revenue guarantees.

## Quick start (recommended for first test)

### Option A: Python on Windows/Mac/Linux

Requirements: **Python 3.11+** and `ffmpeg` in `PATH`.

```bash
cd social-factory
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765**. Select networks, enter a topic and press **Generate demo video**. You can preview, download and approve the video. Publication intentionally stays disabled.

### Option B: Docker

```bash
cd social-factory
docker compose up --build
```

Open **http://localhost:8765**. Port is bound to localhost by default.

### Check the API (optional)

- Health: http://localhost:8765/health
- Swagger: http://localhost:8765/api/docs
- Jobs: http://localhost:8765/api/jobs
- Available platforms: http://localhost:8765/api/platforms

## Live AI scripts via FreeLLMAPI (optional)

1. Install and start the upstream [`freellmapi`](https://github.com/tashfeenahmed/freellmapi) project separately.
2. Connect a provider API key within that application's interface.
3. Copy `.env.example` to `.env` and set the correct gateway URL, key and model (example URL: `OPENAI_BASE_URL=http://127.0.0.1:3001/v1`). Use the exact port, token and model shown by your gateway.
4. Restart Social Factory. No cloud model is bundled, and no free quota is promised.

Never commit `.env`, OAuth tokens, cookies or private credentials. API keys are only read on the server, never typed into this browser.

## Full video rendering via MoneyPrinterTurbo (optional; adapter needs testing)

Install the official upstream project separately (Python 3.11 recommended):

```bash
pip install mpt
mpt webui
mpt cli --help
```

Configure its LLM, footage and TTS in its official WebUI or `config.toml`, then set `RENDER_ENGINE=mpt` in this project's `.env` and restart. The CLI adapter invokes `mpt cli --video-script <generated script> --stop-at video` and looks for an MP4 path in the JSON output. Versions may differ; test on your machine before enabling any live post. The production renderer is **not installed** in this project's Docker image.

## Real posting through Upload-Post (use with care)

The uploader supports **YouTube, TikTok, Instagram, Facebook Page Reels, X, Threads, LinkedIn, Pinterest, Bluesky, Mastodon, Telegram, Discord, WordPress, Google Business Profile** according to its video API documentation, but **each platform may impose different media constraints, permissions and availability**. An account appearing in the UI **does not mean it is connected** or automatically usable. The API currently reports Reddit video posting as unavailable; it is excluded.

1. Create an account with [Upload-Post](https://www.upload-post.com/), connect each network, make an API key and note your Upload-Post profile (`user`).
2. Copy `.env.example` to `.env`; set `UPLOAD_POST_API_KEY`, `UPLOAD_POST_USER`; include `FACEBOOK_PAGE_ID` if Facebook is selected, and `PINTEREST_BOARD_ID` if Pinterest is selected.
3. Start with **one connected test account**, ideally private/test visibility if the platform provides it. Read provider documentation for additional per-platform privacy, disclosure and video requirements.
4. Explicitly set `ENABLE_LIVE_PUBLISH=true` and restart. Preview your clip. Click **Approve** only after checking facts, copyright and synthetic-media declarations.
5. Click **Publish (live only)**, type `PUBLISH`. The server calls `POST https://api.upload-post.com/api/upload` with a unique idempotency key.
6. Confirm status in Upload-Post's own dashboard. The job state `submitted_check_provider` means *accepted by provider*, not proof the content is public on all accounts.

**Do not retry after an ambiguous timeout.** The backend moves the job to `needs_manual_status_check` because a remote publication may have begun. The provider supports polling via request ID, but automated status polling is not implemented in this MVP.

**Safety:** Do not expose port 8765 to the internet; this proof-of-concept has no login/authentication. Only run it on your own machine or protected internal network. Do not use unattended posting or bot accounts to evade rate limits, account controls, brand disclosure or synthetic-media policies.

## Platforms & limitations

| Channel | Demo selection | Real provider path | Notes |
|---|---|---|---|
| YouTube Shorts | ✅ | Upload-Post | Connect YouTube channel; titles required |
| TikTok | ✅ | Upload-Post | Account permissions/privacy, some plans restrict uploads |
| Instagram Reels | ✅ | Upload-Post | Connect eligible account |
| Facebook Page Reels | ✅ | Upload-Post | `FACEBOOK_PAGE_ID` required |
| X | ✅ | Upload-Post | Video eligibility and API/publisher terms |
| Threads | ✅ | Upload-Post | Connect eligible account |
| LinkedIn | ✅ | Upload-Post | Video post support and permissions |
| Pinterest | ✅ | Upload-Post | `PINTEREST_BOARD_ID` required |
| Bluesky | ✅ | Upload-Post | Video length/size restrictions |
| Mastodon | ✅ | Upload-Post | Instance-specific restrictions |
| Telegram | ✅ | Upload-Post | Bot/channel permissions |
| Discord | ✅ | Upload-Post | Server/channel permissions |
| WordPress | ✅ | Upload-Post | Site access and video handling |
| Google Business Profile | ✅ | Upload-Post | Business profile rules |
| Reddit | ❌ | None | Upload-Post currently reports 503 for Reddit. Explore Postiz once approved |
| 15+ other platforms | Catalog only | Postiz alternatives | Not wired to publisher in this starter |

**Note:** Not all networks accept the same aspect ratio, file, duration, sound, caption or synthetic-content metadata. One source MP4 can feed many channels, but per-platform conversion may be required by the provider.

## Project layout

```
social-factory/
├── app.py                  # Dashboard API, local review state, guardrails
├── index.html              # Responsive web dashboard
├── renderer.py             # Offline 9-second preview + optional MPT CLI adapter
├── provider.py             # Optional LLM + real Upload-Post adapter
├── catalog.json            # Network/provider and curated project list
├── PROJECTS.md             # Evaluated GitHub projects, licenses and links
├── .env.example            # Configuration template, no credentials
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── scripts/clone-references.sh  # OPTIONAL clone upstream repos locally
├── tests/
└── output/                 # SQLite + rendered MP4s (gitignored)
```

## Third-party source management

See [PROJECTS.md](PROJECTS.md) for links to the independently maintained upstream repositories. We **do not copy their entire contents** into this repo. Running `bash scripts/clone-references.sh` makes shallow clones under `third_party/` locally (gitignored). Review licenses and dependency/security changes before running third-party software. Especially, AGPL-3.0 products have obligations when modified and offered over a network.

## Why not automatically copy 7 repositories into one GitHub project?

They have overlapping purposes, different frameworks, large sizes, and different licenses. Bundling several full applications leads to complex updates and potential license conflicts. This repo uses **one thin workflow** and links out to the upstream projects. We can later select a **single** publishing backend (Postiz or Upload-Post) and one video engine.

## Development / tests

```bash
pip install pytest httpx
pytest -q
```

## Official documents checked

- [MoneyPrinterTurbo source and official CLI](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md)
- [FreeLLMAPI source](https://github.com/tashfeenahmed/freellmapi)
- [Upload-Post quickstart](https://docs.upload-post.com/quickstart)
- [Upload-Post video API](https://docs.upload-post.com/api/upload-video/)
- [Postiz source](https://github.com/gitroomhq/postiz-app)

Built as a proof of concept; don't infer an endorsement or partnership from any linked upstream project.
