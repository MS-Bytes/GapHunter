# GapHunter

Static, SEO-ready website of market-gap ideas (apps, services, web tools) for 2027 and beyond.
New ideas are added automatically every Monday.

## How it works
- `_data/ideas.json` — all ideas, trends and the validation checklist (the only content file).
- `_data/config.json` — site URL, name, optional social profile links (empty = hidden).
- `_src/styles.css`, `_src/app.js` — design and front-end code.
- `build.py` — generates the site: `index.html`, `ideas/<slug>/`, `category/<slug>/`,
  `sitemap.xml`, `feed.xml`, `robots.txt`, `.htaccess`, share images in `og/`.
- `_src/WEEKLY_UPDATE.md` — the playbook the Monday scheduled task follows.

Generated files are committed, so the server just serves the repo as-is.

## Edit by hand
1. Change `_data/ideas.json` (or config).
2. Run `python3 build.py` (needs Python 3.10+; Pillow optional for share images).
3. Commit and push.

## First-time setup
1. In `_data/config.json` set `siteUrl` to your real subdomain, e.g. `https://ideas.example.com`,
   then run `python3 build.py` and push.
2. Hostinger hPanel → Websites → Manage → Advanced → **GIT**:
   - Repository: `https://github.com/MS-Bytes/GapHunter.git`, branch `main`,
     directory: the subdomain folder (e.g. `public_html/ideas`, must be empty).
   - Private repo: copy the SSH key Hostinger shows into GitHub → repo → Settings → Deploy keys,
     and use the SSH URL `git@github.com:MS-Bytes/GapHunter.git`.
   - Turn on **Auto Deployment**, copy the webhook URL, and add it in GitHub → Settings →
     Webhooks (content type `application/json`, push events).
3. Enable SSL for the subdomain.
4. Submit `https://<subdomain>/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
