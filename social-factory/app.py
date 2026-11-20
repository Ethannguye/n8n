"""Social Factory MVP: preview-first cross-post workflow.

Web dashboard requires local access. Live publishing requires explicit environment
opt-in, manual approval, and a publish confirmation. Never expose port publicly.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / '.env')
from provider import make_script, publish_upload_post, ProviderError
from renderer import render_demo, render_mpt

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.getenv('SOCIAL_FACTORY_OUTPUT', str(ROOT / 'output'))).expanduser()
if not OUTPUT.is_absolute(): OUTPUT = ROOT / OUTPUT
OUTPUT.mkdir(parents=True, exist_ok=True)
DB = OUTPUT / 'jobs.sqlite3'
PLATFORMS = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))['upload_post_video']
LOCK = Lock()
app = FastAPI(title='Social Factory', version='0.1.0', docs_url='/api/docs')


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, topic TEXT NOT NULL, '
              'language TEXT NOT NULL, script TEXT NOT NULL, video TEXT NOT NULL, '
              'platforms TEXT NOT NULL, status TEXT NOT NULL, last_result TEXT NOT NULL, '
              'created_at TEXT NOT NULL)')
    return c


def get_job(jid):
    with conn() as c:
        row = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
    if not row: raise HTTPException(404, 'Job not found')
    data = dict(row)
    data['platforms'] = json.loads(data['platforms'])
    if data['last_result']:
        try: data['last_result'] = json.loads(data['last_result'])
        except ValueError: pass
    data['video_url'] = f'/api/jobs/{jid}/video'
    return data


class GenerateInput(BaseModel):
    topic: str = Field(min_length=5, max_length=160)
    language: str = Field(default='English', max_length=30)
    platforms: list[str] = Field(default_factory=lambda: ['youtube', 'tiktok', 'instagram'])


class PublishInput(BaseModel):
    confirm: str


@app.get('/', response_class=HTMLResponse)
def homepage():
    return (ROOT / 'index.html').read_text(encoding='utf-8')


@app.get('/health')
def health():
    return {'ok': True, 'version': '0.1.0', 'render_engine': os.getenv('RENDER_ENGINE', 'demo'),
            'live_publishing_enabled': os.getenv('ENABLE_LIVE_PUBLISH', '').lower() == 'true'}


@app.get('/api/platforms')
def platforms():
    return {'upload_post_video': PLATFORMS, 'additional': json.loads((ROOT / 'catalog.json').read_text())['additional_postiz_candidates'],
            'reddit_note': 'Upload-Post video endpoint documents Reddit posting as temporarily unavailable.'}


@app.get('/api/jobs')
def jobs():
    with conn() as c:
        ids = [r['id'] for r in c.execute('SELECT id FROM jobs ORDER BY created_at DESC LIMIT 30').fetchall()]
    return [get_job(jid) for jid in ids]


@app.post('/api/jobs')
def generate(item: GenerateInput):
    selected = list(dict.fromkeys(item.platforms))
    if not selected or any(p not in PLATFORMS for p in selected):
        raise HTTPException(422, 'Select at least one currently supported Upload-Post video platform')
    jid = uuid.uuid4().hex
    try:
        script = make_script(item.topic.strip(), item.language.strip())
        engine = os.getenv('RENDER_ENGINE', 'demo').strip().lower()
        if engine == 'demo':
            dst = render_demo(item.topic.strip(), script, OUTPUT / f'{jid}.mp4')
        elif engine == 'mpt':
            dst = render_mpt(script)
        else:
            raise ValueError('RENDER_ENGINE must be demo or mpt')
    except (RuntimeError, ValueError, ProviderError) as exc:
        raise HTTPException(502, str(exc)[:600])
    with LOCK, conn() as c:
        c.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                  (jid, item.topic.strip(), item.language, script, str(dst),
                   json.dumps(selected), 'review_required', '', datetime.now(timezone.utc).isoformat()))
    return get_job(jid)


@app.get('/api/jobs/{jid}/video')
def video(jid: str):
    row = get_job(jid)
    path = Path(row['video'])
    if not path.is_file(): raise HTTPException(404, 'Rendered file missing')
    return FileResponse(path, media_type='video/mp4', filename=f'{jid}.mp4')


@app.post('/api/jobs/{jid}/approve')
def approve(jid: str):
    row = get_job(jid)
    if row['status'] != 'review_required':
        raise HTTPException(409, 'Only pending jobs can be approved')
    with LOCK, conn() as c:
        c.execute('UPDATE jobs SET status=? WHERE id=?', ('approved', jid))
    return get_job(jid)


@app.post('/api/jobs/{jid}/publish')
def publish(jid: str, data: PublishInput):
    row = get_job(jid)
    if row['status'] != 'approved':
        raise HTTPException(409, 'Manual approval required before publishing')
    if data.confirm != 'PUBLISH':
        raise HTTPException(400, 'Enter exactly PUBLISH to confirm')
    if os.getenv('ENABLE_LIVE_PUBLISH', 'false').lower() != 'true':
        raise HTTPException(403, 'Live publishing is DISABLED. Set ENABLE_LIVE_PUBLISH=true in .env to opt in.')
    with LOCK, conn() as c:
        # Reserve status before remote request to prevent double-click duplicate publications.
        res = c.execute("UPDATE jobs SET status='submitting' WHERE id=? AND status='approved'", (jid,))
        if res.rowcount != 1: raise HTTPException(409, 'Publish already submitted')
    try:
        result = publish_upload_post(video=Path(row['video']), platforms=row['platforms'],
                         title=row['topic'], description=row['script'], job_id=jid)
        with LOCK, conn() as c:
            c.execute('UPDATE jobs SET status=?,last_result=? WHERE id=?',
                      ('submitted_check_provider', json.dumps(result), jid))
    except (ProviderError, OSError) as exc:
        # Do not auto-retry: network timeout may mean the upload already happened.
        with LOCK, conn() as c:
            c.execute('UPDATE jobs SET status=?,last_result=? WHERE id=?',
                      ('needs_manual_status_check', json.dumps({'error': str(exc)}), jid))
        raise HTTPException(502, f'{exc}. Do NOT retry until you check provider job status.')
    return get_job(jid)
