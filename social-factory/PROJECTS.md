# GitHub projects researched for Social Factory

Last reviewed: 2026-11-20. Links point to upstream authors. These are references, **not vendored source**.

| Project | GitHub | Main use | License from repository | Decision |
|---|---|---|---|---|
| MoneyPrinterTurbo | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | AI video scripts, footage, voice, subtitles | MIT | **Chosen** video engine; optional CLI adapter |
| FreeLLMAPI | [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) | OpenAI-compatible LLM gateway across provider free tiers | MIT | **Chosen** optional script gateway (external instance) |
| Postiz | [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) | Publish/schedule to many social and content channels | AGPL-3.0 | **Top candidate** for self-hosted distributor; NOT integrated yet |
| OpenPost | [getopenpost/openpost](https://github.com/getopenpost/openpost) | Multi-network posting with queue and automation | AGPL-3.0 | Alternative to Postiz |
| Postflare | [FerdiKT/postflare](https://github.com/FerdiKT/postflare) | Cloudflare Workers/D1/R2 social scheduling | AGPL-3.0 | Alternative if using Cloudflare; many provider integrations beta |
| OpenPublish | [azeemkafridi/openpublish](https://github.com/azeemkafridi/openpublish) | Self-host cross-publishing and network-specific drafts | AGPL-3.0 | Alternative to Postiz |
| Crossposter | [apoorvdarshan/crossposter](https://github.com/apoorvdarshan/crossposter) | Lightweight local cross-poster | Check upstream | Alternative for local experiments |
| n8n | [n8n-io/n8n](https://github.com/n8n-io/n8n) | Schedule and orchestrate API calls | Sustainable Use License (check current) | Optional orchestrator; not required by MVP |

## Supported network types across candidate products

Publishing destinations reported by one or more candidate projects include: YouTube, TikTok, Instagram, Facebook Pages, X, Threads, LinkedIn personal/pages, Pinterest, Bluesky, Mastodon, Telegram, Discord, Reddit, WordPress, Google Business Profile, Medium, Dev.to, Hashnode, Tumblr, Slack, Twitch, Kick, Nostr, VK, Lemmy, Farcaster, MeWe, Dribbble and others. **These are candidates, not 30 confirmed live connections.** Individual APIs, provider implementations and account approvals can differ.

## Licensing & maintenance choices

- MIT (MoneyPrinterTurbo, FreeLLMAPI): permissive, retain notices when redistributing original code.
- AGPL-3.0 (Postiz, OpenPost, Postflare, OpenPublish): network-use and source-sharing obligations can apply to modified versions. Review terms before deployment, especially SaaS/commercial services.
- Never commit API tokens, session cookies or OAuth secrets.
- Avoid private unofficial APIs that circumvent platform controls or expose accounts to bans.
- Record upstream pinned commits before dependency upgrades. Shallow clones are optional for local evaluation, not part of this repository.
- Don't assume project support for a platform is equivalent to approved video uploading. Some targets are text- or image-oriented; check the provider's current API, codec limits and account requirements.

## Implementation priorities

1. **Now:** local preview + approval queue + guarded Upload-Post adapter (completed).
2. **Next:** test MPT full renderer and one provider-controlled social account; add status polling (planned).
3. **Next:** connect Postiz or Upload-Post to n8n scheduler; add per-network captions and video transcoding (planned).
4. **Later:** platform analytics, compliance tags, commercial-use review, multi-user auth (not built).
