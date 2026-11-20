"""Optional external providers. Neither is required for the offline demo."""
import os
from pathlib import Path

import requests


class ProviderError(RuntimeError):
    pass


def make_script(topic: str, language: str = 'English') -> str:
    """Use an OpenAI-compatible gateway if configured, else a labeled demo template.

    No promises that an upstream free model is available; free-tier quotas vary.
    """
    base = os.getenv('OPENAI_BASE_URL', '').strip().rstrip('/')
    key = os.getenv('OPENAI_API_KEY', '').strip()
    model = os.getenv('OPENAI_MODEL', '').strip()
    if not (base and key and model):
        return (f'What can we learn about {topic}?\n\n'
                f'Here are three questions to explore: What is it? Why does it matter? '
                f'What should someone check before trying it?\n\n'
                f'Add verified facts and your own examples before publishing. '
                f'(Demo template; language selected: {language}.)')
    if not base.startswith(('https://', 'http://localhost:', 'http://127.0.0.1:', 'http://host.docker.internal:')):
        raise ProviderError('OPENAI_BASE_URL must be HTTPS or local.')
    try:
        resp = requests.post(
            base + '/chat/completions',
            headers={'Authorization': f'Bearer {key}'},
            json={'model': model, 'messages': [
                {'role': 'system', 'content': 'Write an original factual 70-100 word vertical-video script. No invented facts, quotes, or sources. If uncertain, clearly say so. No promotion of spam or clickbait.'},
                {'role': 'user', 'content': f'Language: {language}. Topic: {topic}. Give a concise hook, 3 substantive points, and an ending.'}
            ], 'temperature': 0.55},
            timeout=50,
        )
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        if not content or not content.strip():
            raise ProviderError('LLM returned empty text')
        return content.strip()
    except (requests.RequestException, KeyError, IndexError, ValueError) as ex:
        raise ProviderError(f'Script generation failed: {type(ex).__name__}: {str(ex)[:200]}') from ex


def publish_upload_post(*, video: Path, platforms: list[str], title: str,
                        description: str, job_id: str) -> dict:
    """Official multipart API. Never call until manual review AND opt-in are complete."""
    key = os.getenv('UPLOAD_POST_API_KEY', '').strip()
    user = os.getenv('UPLOAD_POST_USER', '').strip()
    if not key or not user:
        raise ProviderError('UPLOAD_POST_API_KEY and UPLOAD_POST_USER are required')
    if 'facebook' in platforms and not os.getenv('FACEBOOK_PAGE_ID', '').strip():
        raise ProviderError('FACEBOOK_PAGE_ID is required for Facebook Reels')
    if 'pinterest' in platforms and not os.getenv('PINTEREST_BOARD_ID', '').strip():
        raise ProviderError('PINTEREST_BOARD_ID is required for Pinterest')
    fields = [ ('user', user), ('title', title[:100]), ('description', description[:2100]),
               ('external_id', job_id), ('request_id', job_id), ('async_upload', 'true') ]
    fields.extend(('platform[]', p) for p in platforms)
    if 'facebook' in platforms:
        fields.extend([('facebook_page_id', os.getenv('FACEBOOK_PAGE_ID')), ('facebook_media_type', 'REELS')])
    if 'pinterest' in platforms:
        fields.append(('pinterest_board_id', os.getenv('PINTEREST_BOARD_ID')))
    # Idempotency key helps protect against accidental duplicate posts on retries.
    with video.open('rb') as f:
        try:
            resp = requests.post(
                'https://api.upload-post.com/api/upload',
                headers={'Authorization': f'Apikey {key}', 'Idempotency-Key': job_id},
                data=fields, files={'video': (video.name, f, 'video/mp4')}, timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get('success', False):
                raise ProviderError(f'Upload-Post reported failure: {str(data)[:400]}')
            return data
        except requests.RequestException as ex:
            raise ProviderError(f'Upload-Post request failed: {type(ex).__name__} ({getattr(ex.response,"status_code", "unknown")})') from ex
