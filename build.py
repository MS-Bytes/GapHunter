#!/usr/bin/env python3
"""GapHunter static site builder.

Reads _data/config.json + _data/ideas.json and writes a fully static,
SEO-ready site into the repo root (index.html, ideas/, category/,
sitemap.xml, robots.txt, ...). Python standard library only; Pillow is
optional (used for social share images).

Usage:  python3 build.py           build the site
        python3 build.py --check   only validate the data
"""
import hashlib, html, json, os, re, sys, glob, shutil
from datetime import date, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "_data")
SRC = os.path.join(ROOT, "_src")

TYPES = ["App", "Service", "Web Tool"]
BUDGETS = {"Low": "< $500", "Medium": "$500–3k", "High": "$3k+"}
STATUS = {"early": "Early", "hot": "Hot", "crowded": "Crowded"}
CAT_ICON = {"AI": "🤖", "Health": "🩺", "Finance": "💸", "Education": "📚", "E-commerce": "🛍", "Local Business": "🏪",
            "Creator": "🎬", "Productivity": "⚡", "Agriculture": "🌾", "Energy & EV": "🔋", "Islamic Tech": "🕌",
            "Privacy": "🛡", "Lifestyle": "💍", "Climate": "🌍", "Travel": "✈️", "Gaming": "🎮", "HR & Jobs": "💼",
            "Real Estate": "🏠", "Logistics": "🚚", "Kids & Family": "🧸", "Security": "🔐", "Legal": "⚖️"}
REQUIRED = ["id", "slug", "added", "updated", "title", "pitch", "type", "cat", "gap", "dem", "comp", "diff", "weeks",
            "budget", "status", "why", "problem", "audience", "solution", "whyGap", "money", "stack", "mvp", "risks", "channels"]

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
slugify = lambda s: re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and"))).strip("-")


# ---------------------------------------------------------------- data
def load():
    with open(os.path.join(DATA, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    with open(os.path.join(DATA, "ideas.json"), encoding="utf-8") as f:
        db = json.load(f)
    cfg["siteUrl"] = cfg["siteUrl"].rstrip("/")
    return cfg, db


def validate(db):
    errs, ids, slugs = [], set(), set()
    cats = db.get("categories", [])
    for c in cats:
        if c not in CAT_ICON:
            errs.append(f"category '{c}' has no icon in build.py CAT_ICON")
    datere = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for n, i in enumerate(db["ideas"]):
        tag = f"idea #{n} ({i.get('title', '?')})"
        for k in REQUIRED:
            if k not in i or i[k] in ("", None, []):
                errs.append(f"{tag}: missing '{k}'")
        if errs and errs[-1].startswith(tag):
            continue
        if i["id"] in ids: errs.append(f"{tag}: duplicate id {i['id']}")
        if i["slug"] in slugs: errs.append(f"{tag}: duplicate slug {i['slug']}")
        ids.add(i["id"]); slugs.add(i["slug"])
        if i["slug"] != slugify(i["slug"]): errs.append(f"{tag}: slug must be lowercase-with-dashes")
        if i["type"] not in TYPES: errs.append(f"{tag}: type must be one of {TYPES}")
        if i["cat"] not in cats: errs.append(f"{tag}: category '{i['cat']}' not in categories list")
        if i["budget"] not in BUDGETS: errs.append(f"{tag}: budget must be Low/Medium/High")
        if i["status"] not in STATUS: errs.append(f"{tag}: status must be early/hot/crowded")
        if not (isinstance(i["gap"], int) and 0 <= i["gap"] <= 100): errs.append(f"{tag}: gap must be int 0-100")
        for k in ("dem", "comp", "diff"):
            if not (isinstance(i[k], int) and 1 <= i[k] <= 5): errs.append(f"{tag}: {k} must be int 1-5")
        if not (isinstance(i["weeks"], int) and 1 <= i["weeks"] <= 104): errs.append(f"{tag}: weeks must be int 1-104")
        for k in ("added", "updated"):
            if not datere.match(str(i[k])): errs.append(f"{tag}: {k} must be YYYY-MM-DD")
        for k in ("money", "mvp", "risks", "channels"):
            if not isinstance(i[k], list): errs.append(f"{tag}: {k} must be a list")
    for t in db.get("trends", []):
        if not (0 <= t.get("stage", -1) <= 1 and 1 <= t.get("demand", 0) <= 5 and t.get("label") and t.get("query")):
            errs.append(f"trend {t}: needs label, query, stage 0-1, demand 1-5")
    if not datere.match(db["meta"].get("lastUpdated", "")): errs.append("meta.lastUpdated must be YYYY-MM-DD")
    return errs


# ---------------------------------------------------------------- helpers
def weeks_label(w):
    if w <= 8: return f"{w} week" + ("s" if w > 1 else "")
    m = round(w / 4.3)
    return f"{m} month" + ("s" if m > 1 else "")
def earn_score(i): return i["dem"] * 3 + (5 - i["comp"]) * 2 + {"Low": 0, "Medium": 1, "High": 2}[i["budget"]]
def earn_label(i):
    s = earn_score(i)
    return "Very high" if s >= 21 else "High" if s >= 17 else "Medium" if s >= 13 else "Modest"
def ring_color(g): return "var(--neon)" if g >= 80 else "var(--violet)" if g >= 65 else "var(--amber)"
def nice_date(s): return datetime.strptime(s, "%Y-%m-%d").strftime("%-d %b %Y")
def idea_url(i): return f"/ideas/{i['slug']}/"
def cat_url(c): return f"/category/{slugify(c)}/"
def clip(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def ring(g, size=62, cls=""):
    r = size / 2 - 5
    c = 2 * 3.14159265 * r
    off = c * (1 - g / 100)
    return (f'<div class="ring {cls}" role="img" aria-label="Gap score {g} out of 100"><svg width="{size}" height="{size}" aria-hidden="true">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="var(--surface2)" stroke-width="5"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{ring_color(g)}" stroke-width="5" stroke-linecap="round" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}"/></svg><b>{g}</b></div>')


def bars(n): return '<span class="bars" aria-hidden="true">' + "".join(f'<i class="{"f" if k <= n else ""}"></i>' for k in range(1, 6)) + "</span>"
def meters(i):
    return ('<div class="meters">'
            f'<div class="meter m-dem"><span>Demand</span>{bars(i["dem"])}<span class="sr">{i["dem"]} of 5</span></div>'
            f'<div class="meter m-comp"><span>Competition</span>{bars(i["comp"])}<span class="sr">{i["comp"]} of 5</span></div>'
            f'<div class="meter m-diff"><span>Difficulty</span>{bars(i["diff"])}<span class="sr">{i["diff"]} of 5</span></div></div>')


BM_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'


def tags(i, new=False):
    t = i["type"].replace(" ", "")
    return (f'<div class="tags"><span class="tag t-{t}">{e(i["type"])}</span><span class="tag">{CAT_ICON.get(i["cat"], "✨")} {e(i["cat"])}</span>'
            f'<span class="status st-{i["status"]}">{STATUS[i["status"]]}</span>{"<span class=\"status st-new\">New</span>" if new else ""}</div>')


def data_attrs(i, new):
    search = " ".join([i["title"], i["pitch"], i["cat"], i["type"], i["why"], i["stack"]]).lower()
    return (f'data-id="{i["id"]}" data-url="{idea_url(i)}" data-title="{e(i["title"])}" data-type="{e(i["type"])}" data-cat="{e(i["cat"])}" '
            f'data-gap="{i["gap"]}" data-diff="{i["diff"]}" data-weeks="{i["weeks"]}" data-budget="{i["budget"]}" data-earn="{earn_score(i)}" '
            f'data-added="{i["added"]}" data-pk="{1 if i.get("pk") else 0}" data-new="{1 if new else 0}" data-search="{e(search)}"')


def card(i, new=False, heading="h3"):
    return (f'<article class="card glass" {data_attrs(i, new)}>'
            f'<div class="card-top">{tags(i, new)}<button class="bm" data-bm="{i["id"]}" aria-label="Save {e(i["title"])}" aria-pressed="false">{BM_SVG}</button></div>'
            f'<{heading}><a class="card-link" href="{idea_url(i)}">{e(i["title"])}</a></{heading}><p class="pitch">{e(i["pitch"])}</p>'
            f'<div class="score-row">{ring(i["gap"])}{meters(i)}</div>'
            f'<div class="why"><b>Why now?</b> {e(i["why"])}</div>'
            f'<div class="card-foot"><span>⏱ MVP: {weeks_label(i["weeks"])}</span><span>💰 {BUDGETS[i["budget"]]}</span><span>📈 {earn_label(i)}</span></div></article>')


# ---------------------------------------------------------------- minify
def min_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    return css.replace(";}", "}").strip()


def min_js(js):
    out = []
    for line in js.splitlines():
        s = line.strip()
        if not s or s.startswith("//") or (s.startswith("/*") and s.endswith("*/")):
            continue
        out.append(s)
    return "\n".join(out)


def min_html(h):
    return re.sub(r"\n\s+", "\n", h).replace("\n\n", "\n")


# ---------------------------------------------------------------- shell
FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Sora:wght@700;800&display=swap"
LOGO = ('<span class="logo-mark"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4M11 8v6M8 11h6"/></svg></span>')


def head(cfg, css, title, desc, path, ogimg, jsonld, extra=""):
    url = cfg["siteUrl"] + path
    og = cfg["siteUrl"] + ogimg
    tw = f'<meta name="twitter:site" content="{e(cfg["twitter"])}">' if cfg.get("twitter") else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>' for x in jsonld)
    return f"""<!DOCTYPE html>
<html lang="{cfg['language']}" data-theme="dark" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#07060f">
<meta property="og:type" content="{'article' if path.startswith('/ideas/') else 'website'}">
<meta property="og:site_name" content="{e(cfg['siteName'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">{tw}
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{e(cfg['siteName'])} — new ideas" href="/feed.xml">
<script>try{{var t=localStorage.getItem("gh_theme");if(t)document.documentElement.dataset.theme=JSON.parse(t)}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{FONT_URL}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{FONT_URL}"></noscript>
<style>{css}</style>
{ld}{extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div id="progress"></div>"""


def header(cfg, home=True):
    p = "" if home else "/"
    return f"""<header><div class="wrap nav">
<a href="/" class="logo" aria-label="{e(cfg['siteName'])} home">{LOGO}{e(cfg['siteName'])}</a>
<nav class="nav-links" id="navLinks" aria-label="Main"><a href="{p}#explore">Explore</a><a href="{p}#generator">Generator</a><a href="{p}#radar">Trend Radar</a><a href="{p}#calculator">Calculator</a><a href="{p}#faq">FAQ</a></nav>
<div class="nav-actions">
<button class="icon-btn" id="savedBtn" aria-label="Saved ideas">{BM_SVG}<span class="badge-count" id="savedCount" hidden>0</span></button>
<button class="icon-btn" id="themeBtn" aria-label="Toggle light and dark theme"><svg id="themeIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"></svg></button>
<button class="icon-btn menu-btn" id="menuBtn" aria-label="Menu" aria-expanded="false" aria-controls="navLinks"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
</div></div></header>"""


def footer(cfg, cats, js):
    year = date.today().year
    soc = cfg.get("social", {})
    catlinks = "".join(f'<a href="{cat_url(c)}">{e(c)} ideas</a>' for c in cats[:8])
    social = "".join(f'<a href="{e(u)}" rel="noopener" target="_blank">{n}</a>' for n, u in (("X / Twitter", soc.get("x")), ("YouTube", soc.get("youtube")), ("LinkedIn", soc.get("linkedin"))) if u)
    return f"""<footer><div class="wrap"><div class="foot">
<div><a href="/" class="logo">{LOGO}{e(cfg['siteName'])}</a><p>Discover what the market needs before it's crowded. New gap ideas every Monday for makers, freelancers and first-time founders.</p></div>
<div><h2>Explore</h2><a href="/#explore">All ideas</a><a href="/#generator">Idea generator</a><a href="/#radar">Trend radar</a><a href="/#calculator">Revenue calculator</a><a href="/feed.xml">RSS feed</a></div>
<div><h2>Categories</h2>{catlinks}</div>
<div><h2>Follow</h2>{social}</div>
</div><div class="copy"><span>© {year} {e(cfg['siteName'])}. All rights reserved.</span><span>Ideas and scores are editorial estimates for inspiration — not financial or legal advice.</span></div></div></footer>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="Saved ideas"><div class="drawer-head"><h2 style="font-size:1.1rem">🔖 Saved ideas</h2><button class="icon-btn" id="drawerClose" aria-label="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>
<div class="drawer-body" id="drawerBody"></div><div class="drawer-foot"><button class="btn btn-primary btn-sm" id="exportBtn" style="flex:1;justify-content:center">Copy as Markdown</button><button class="btn btn-ghost btn-sm" id="clearSaved">Clear</button></div></aside>
<dialog id="copyDialog"><h2 style="font-size:1.2rem">Copy this text</h2><p style="color:var(--muted)">Automatic copy was blocked. Select all and copy.</p><textarea readonly></textarea><form method="dialog"><button class="btn btn-ghost btn-sm">Close</button></form></dialog>
<button class="icon-btn" id="toTop" aria-label="Back to top"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg></button>
<div id="toast" role="status" aria-live="polite"></div>
<script src="{js}" defer></script>
</body></html>"""


# ---------------------------------------------------------------- pages
def radar_svg(trends):
    W, H, top, bot = 900, 380, 50, 350
    zw = W / 4
    zones = [("Emerging", "var(--neon)"), ("Rising", "var(--violet)"), ("Peak", "var(--amber)"), ("Saturated", "var(--red)")]
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="radarTitle"><title id="radarTitle">Trend radar: trends placed from emerging to saturated</title>']
    for k, (name, col) in enumerate(zones):
        s.append(f'<rect x="{k*zw+4}" y="{top-34}" width="{zw-8}" height="{bot-top+40}" rx="16" fill="{col}" fill-opacity=".06"/>'
                 f'<text x="{k*zw+zw/2}" y="{top-12}" text-anchor="middle" fill="{col}" font-family="Sora,sans-serif" font-weight="700" font-size="15">{name}</text>')
    s.append(f'<line x1="20" y1="{bot+14}" x2="{W-20}" y2="{bot+14}" stroke="var(--border)" stroke-width="2"/>'
             f'<text x="20" y="{bot+28}" fill="var(--muted)" font-size="11">Head start ←</text><text x="{W-20}" y="{bot+28}" text-anchor="end" fill="var(--muted)" font-size="11">→ Crowded</text>')
    for k, t in enumerate(trends):
        x = 30 + t["stage"] * (W - 60)
        y = top + 30 + (k * 97) % (bot - top - 60)
        r = 10 + t["demand"] * 5
        col = zones[min(3, int(t["stage"] * 4))][1]
        s.append(f'<g class="bubble" data-q="{e(t["query"])}" tabindex="0" role="button" aria-label="{e(t["label"])} — show ideas"><title>{e(t["label"])} · demand {t["demand"]}/5</title>'
                 f'<circle cx="{x:.0f}" cy="{y}" r="{r}" fill="{col}" fill-opacity=".22" stroke="{col}" stroke-width="2"/>'
                 f'<text x="{x:.0f}" y="{y + r + 14}" text-anchor="middle" fill="var(--muted)" font-size="11">{e(t["label"])}</text></g>')
    s.append("</svg>")
    return "".join(s)


GEN = {
    "aud": {"AI": ["small clinics", "freelancers", "local shops", "content creators"], "Health": ["elderly parents", "busy doctors", "new mothers", "clinic receptionists"],
            "Finance": ["freelancers", "shopkeepers", "overseas families", "students"], "Education": ["Matric students", "private schools", "home tutors", "parents of toddlers"],
            "E-commerce": ["Instagram sellers", "clothing brands", "home bakers", "COD stores"], "Local Business": ["salons", "pharmacies", "plumbers & electricians", "restaurants"],
            "Creator": ["YouTubers", "TikTokers", "podcasters", "Urdu bloggers"], "Productivity": ["remote teams", "solo founders", "agencies", "students"],
            "Agriculture": ["small farmers", "dairy owners", "fruit traders", "agri dealers"], "Energy & EV": ["solar owners", "EV drivers", "factory owners", "housing societies"],
            "Islamic Tech": ["Hifz students", "Muslim travellers", "halal investors", "madrasas"], "Privacy": ["women creators", "small businesses", "families", "journalists"],
            "Lifestyle": ["wedding families", "new homeowners", "pet owners", "gym-goers"]},
    "fmt": {"coding": ["SaaS dashboard", "Chrome extension", "mobile app", "API service", "AI agent"],
            "nocode": ["WhatsApp bot", "Glide/Softr app", "Notion template + community", "Make/Zapier automation", "AI chatbot widget"],
            "marketing": ["done-for-you service", "curated marketplace", "paid community", "agency package", "paid newsletter"]},
    "twist": {"Low": ["in Roman Urdu", "for WhatsApp only", "on pay-per-use", "with a free tier"],
              "Medium": ["powered by AI agents", "with voice-first UX", "with local payments (JazzCash/Easypaisa)", "with offline mode"],
              "High": ["with a two-sided marketplace", "with custom AI models", "with a hardware + app combo", "as a white-label platform"]},
}

FAQ = [
    ("What is GapHunter?", "GapHunter is a free directory of app, service and web-tool ideas where demand is high but good solutions are still rare. Each idea comes with a problem statement, MVP plan, monetization models and a 7-day validation checklist."),
    ("How is the Gap Score calculated?", "The Gap Score (0–100) is an editorial estimate that weighs how strong the demand is against how much supply and competition already exists, plus how timely the idea is. It is a prioritisation aid, not verified market data — always validate before building."),
    ("How often are new ideas added?", "New ideas are researched and added every Monday. Existing ideas are re-checked too: when competition grows, an idea moves from Early to Hot to Crowded."),
    ("Can I build one of these ideas?", "Yes. Every idea is free to use. Pick one that fits your skills and budget, run the 7-day validation checklist, and launch the MVP features listed on its page."),
    ("Why focus on 2027 and beyond?", "The best returns go to people who build before a market gets crowded. We look for new technology, rule changes and behaviour shifts that open gaps over the next 12–24 months."),
]


def page_index(cfg, db, css, js, cats):
    ideas = sorted(db["ideas"], key=lambda i: -i["gap"])
    new_ids = set(db["meta"].get("lastBatch", []))
    new_ideas = [i for i in ideas if i["id"] in new_ids]
    iotw = new_ideas[0] if new_ideas else ideas[0]
    upd = db["meta"]["lastUpdated"]
    early = sum(1 for i in ideas if i["status"] == "early")
    title = f"{cfg['siteName']}: Startup & App Ideas for 2027 and Beyond"
    desc = cfg["description"]
    counts = {c: sum(1 for i in ideas if i["cat"] == c) for c in cats}
    pk = sum(1 for i in ideas if i.get("pk"))
    jsonld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["siteName"], "url": cfg["siteUrl"] + "/", "description": desc,
         "potentialAction": {"@type": "SearchAction", "target": cfg["siteUrl"] + "/?q={search_term_string}", "query-input": "required name=search_term_string"}},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "Market-gap ideas", "numberOfItems": len(ideas),
         "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": cfg["siteUrl"] + idea_url(i), "name": i["title"]} for n, i in enumerate(ideas[:30])]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    ticker = "".join(f'<a class="tick" href="/?q={e(t["query"])}" data-q="{e(t["query"])}"><em>↗</em>{e(t["label"])}</a>' for t in db["trends"])
    chips = '<button class="chip on" data-v="all" aria-pressed="true">All categories</button>'
    if new_ideas: chips += f'<button class="chip" data-v="new" aria-pressed="false">🆕 New this week ({len(new_ideas)})</button>'
    chips += f'<button class="chip" data-v="pk" aria-pressed="false">🇵🇰 Pakistan / South Asia ({pk})</button>'
    chips += "".join(f'<button class="chip" data-v="{e(c)}" aria-pressed="false">{CAT_ICON[c]} {e(c)} ({counts[c]})</button>' for c in cats if counts[c])
    cat_opts = "".join(f'<option value="{e(c)}">{CAT_ICON[c]} {e(c)}</option>' for c in cats)
    words = ["apps the market is begging for.", "services with more demand than supply.", "web tools built on the newest AI.", "gaps nobody has filled — yet."]
    newlist = ("<p style='margin-top:18px;font-weight:600'>🆕 Added this week:</p><div class='new-list'>" + "".join(f'<a href="{idea_url(i)}">{e(i["title"])}</a>' for i in new_ideas) + "</div>") if new_ideas else ""
    faq = "".join(f'<details class="glass"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQ)

    body = f"""{header(cfg)}
<main id="main">
<section class="hero"><div class="wrap">
<span class="eyebrow">Ideas for 2027 &amp; beyond</span>
<h1>Build It <span class="grad">Before Everyone Else</span></h1>
<p class="sub">Find <span class="typed" id="typed" data-words='{e(json.dumps(words))}'>{words[0]}</span><br>High demand. Low supply. Your window is open now.</p>
<span class="updated">🔄 Updated every Monday · last update {nice_date(upd)}</span>
<form class="search glass" id="heroSearch" role="search" action="/" method="get"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
<label class="sr" for="heroQ">Search ideas</label><input id="heroQ" name="q" placeholder="Search ideas… e.g. WhatsApp, solar, Urdu AI"><button class="btn btn-primary btn-sm" type="submit">Search</button></form>
<div class="hero-cta"><a href="#explore" class="btn btn-primary">Explore ideas →</a><a href="#generator" class="btn btn-ghost">✨ Generate an idea</a></div>
<div class="stats reveal"><div class="stat glass"><b data-count="{len(ideas)}" data-plus="1">{len(ideas)}+</b><span>Ideas listed</span></div><div class="stat glass"><b data-count="{len([c for c in cats if counts[c]])}">{len([c for c in cats if counts[c]])}</b><span>Categories</span></div><div class="stat glass"><b data-count="{early}">{early}</b><span>Early-stage gaps</span></div></div>
</div></section>
<div class="ticker" aria-label="Trending topics"><div class="ticker-track">{ticker}<span aria-hidden="true" style="display:contents">{ticker.replace('class="tick"', 'class="tick" tabindex="-1"')}</span></div></div>

<section style="padding-bottom:10px"><div class="wrap"><div class="iotw glass reveal">
<div><span class="eyebrow">💡 Idea of the week</span><h2><a href="{idea_url(iotw)}">{e(iotw['title'])}</a></h2><p>{e(iotw['pitch'])}</p><div class="why" style="margin-top:16px"><b>Why now?</b> {e(iotw['why'])}</div>{newlist}</div>
<div class="iotw-side" data-id="{iotw['id']}" data-url="{idea_url(iotw)}" data-title="{e(iotw['title'])}" data-type="{e(iotw['type'])}" data-cat="{e(iotw['cat'])}" data-gap="{iotw['gap']}">{ring(iotw['gap'], 84, 'lg')}{tags(iotw)}
<div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-primary btn-sm" href="{idea_url(iotw)}">See full playbook →</a><button class="btn btn-ghost btn-sm" data-bm="{iotw['id']}" data-label="1">🔖 Save idea</button></div></div>
</div></div></section>

<section id="explore"><div class="wrap">
<div class="sec-head"><span class="eyebrow">Idea explorer</span><h2>Opportunities waiting for a <span class="grad">builder</span></h2><p>Filter by type, category, budget and launch time. Open any idea for the full playbook: problem, MVP, money model and a 7-day validation plan.</p></div>
<div class="filters glass">
<div class="f-row"><div class="seg" id="typeSeg" role="group" aria-label="Idea type"><button class="on" data-v="all" aria-pressed="true">All</button><button data-v="App" aria-pressed="false">📱 Apps</button><button data-v="Service" aria-pressed="false">🤝 Services</button><button data-v="Web Tool" aria-pressed="false">🛠 Web tools</button></div>
<div class="f-search grow"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><label class="sr" for="q">Filter ideas</label><input id="q" placeholder="Live search…" type="search"></div></div>
<div class="chips" id="catChips" role="group" aria-label="Category">{chips}</div>
<div class="f-row">
<label class="sr" for="fDiff">Difficulty</label><select id="fDiff"><option value="all">Any difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select>
<label class="sr" for="fBudget">Budget</label><select id="fBudget"><option value="all">Any budget</option><option value="Low">Under $500</option><option value="Medium">$500 – $3k</option><option value="High">$3k+</option></select>
<label class="sr" for="fTime">Launch time</label><select id="fTime"><option value="all">Any launch time</option><option value="2">≤ 2 weeks</option><option value="4">≤ 1 month</option><option value="12">≤ 3 months</option><option value="99">3+ months</option></select>
<label class="sr" for="fSort">Sort</label><select id="fSort"><option value="gap">Sort: Gap Score</option><option value="new">Sort: Newest</option><option value="easy">Sort: Easiest to build</option><option value="earn">Sort: Earning potential</option></select>
<button class="btn btn-ghost btn-sm" id="resetBtn" type="button">Reset</button></div></div>
<p class="result-meta" id="resultMeta" aria-live="polite">{len(ideas)} ideas</p>
<div class="grid" id="grid">{''.join(card(i, i['id'] in new_ids) for i in ideas)}</div>
<div class="empty" id="emptyState" hidden><div style="font-size:3rem">🔭</div><h3>No ideas match</h3><p>Try a different filter or search term.</p><button class="btn btn-ghost" id="emptyReset" type="button">Reset filters</button></div>
<div class="more"><button class="btn btn-ghost" id="moreBtn" type="button" hidden>Show more ideas</button></div>
<p class="disclaim">ⓘ Gap Score, demand, competition and earning labels are <b>editorial estimates</b> to help you prioritise — not verified market statistics. Always validate before you build.</p>
</div></section>

<section id="generator" class="lazy"><div class="wrap">
<div class="sec-head reveal"><span class="eyebrow">Idea generator</span><h2>Spin up a <span class="grad">fresh combo</span></h2><p>Pick your skill, budget and interest. The generator mixes an audience, a format and a twist — then points you to the closest real gap.</p></div>
<div class="gen"><form class="gen-form glass" id="genForm">
<div class="field"><label for="gSkill">Your skill</label><select id="gSkill"><option value="coding">Coding</option><option value="nocode">No-code</option><option value="marketing">Marketing / sales</option></select></div>
<div class="field"><label for="gBudget">Budget</label><select id="gBudget"><option value="Low">Under $500</option><option value="Medium">$500 – $3k</option><option value="High">$3k+</option></select></div>
<div class="field"><label for="gCat">Interest</label><select id="gCat">{''.join(f'<option value="{e(c)}">{CAT_ICON[c]} {e(c)}</option>' for c in cats if c in GEN['aud'])}</select></div>
<button class="btn btn-primary" type="submit" style="justify-content:center">🎰 Generate idea</button></form>
<div class="gen-stage glass"><div class="reels"><div class="reel" id="r1"><small>Audience</small><b>?</b></div><div class="reel" id="r2"><small>Format</small><b>?</b></div><div class="reel" id="r3"><small>Twist</small><b>?</b></div></div>
<div class="gen-out" id="genOut" aria-live="polite"><p>Press <b>Generate idea</b> to get your combo.</p></div></div></div>
</div></section>

<section id="radar" class="lazy"><div class="wrap">
<div class="sec-head reveal"><span class="eyebrow">Trend radar</span><h2>Catch the wave <span class="grad">early</span></h2><p>Trends move from Emerging → Rising → Peak → Saturated. The further left, the bigger your head start. Bubble size shows estimated demand. Tap a bubble to see matching ideas.</p></div>
<div class="radar-box glass">{radar_svg(db['trends'])}
<div class="radar-legend"><span><i style="background:var(--neon)"></i>Best window</span><span><i style="background:var(--violet)"></i>Growing</span><span><i style="background:var(--amber)"></i>Peak</span><span><i style="background:var(--red)"></i>Crowded</span><span>· Placement is an editorial estimate, reviewed weekly</span></div></div>
</div></section>

<section id="calculator" class="lazy"><div class="wrap">
<div class="sec-head reveal"><span class="eyebrow">Opportunity calculator</span><h2>What could this <span class="grad">earn?</span></h2><p>Quick back-of-the-napkin maths. Move the sliders and watch monthly revenue update.</p></div>
<div class="calc"><div class="calc-in glass">
<div class="range-row"><div class="top"><label for="cCur">Currency</label><select id="cCur" style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:2px 8px"><option value="$">USD ($)</option><option value="Rs ">PKR (Rs)</option><option value="€">EUR (€)</option></select></div></div>
<div class="range-row"><div class="top"><label for="cPrice">Price per customer / month</label><b id="cPriceV"></b></div><input type="range" id="cPrice" min="1" max="200" value="15"></div>
<div class="range-row"><div class="top"><label for="cUsers">Visitors / users per month</label><b id="cUsersV"></b></div><input type="range" id="cUsers" min="100" max="100000" step="100" value="5000"></div>
<div class="range-row"><div class="top"><label for="cConv">Conversion to paid</label><b id="cConvV"></b></div><input type="range" id="cConv" min="0.5" max="20" step="0.5" value="3"></div>
<div class="range-row"><div class="top"><label for="cMonths">Months of growth</label><b id="cMonthsV"></b></div><input type="range" id="cMonths" min="1" max="24" value="6"></div></div>
<div class="calc-out glass"><span class="eyebrow">Estimated monthly revenue</span><div class="big grad" id="cMonthly">$0</div>
<div class="kpis"><div class="kpi"><span>Paying customers</span><b id="cPaying">0</b></div><div class="kpi"><span>Yearly run-rate</span><b id="cYearly">$0</b></div></div>
<p class="disclaim" style="margin:0">Assumes paying customers stay subscribed (no churn). Use it to compare ideas, not as a forecast.</p></div></div>
</div></section>

<section id="how" class="lazy"><div class="wrap">
<div class="sec-head reveal"><span class="eyebrow">How to use {e(cfg['siteName'])}</span><h2>From idea to income in <span class="grad">4 steps</span></h2></div>
<div class="steps"><div class="step glass"><div class="ic">🔍</div><h3>Find</h3><p>Filter for a high Gap Score and the “Early” label that fits your skill and budget.</p></div><div class="step glass"><div class="ic">🧪</div><h3>Validate</h3><p>Run the 7-day checklist on the idea page. Get 10 real “yes, I’d pay” signals.</p></div><div class="step glass"><div class="ic">⚙️</div><h3>Build</h3><p>Ship only the listed MVP features with the suggested stack. Launch in weeks, not months.</p></div><div class="step glass"><div class="ic">🚀</div><h3>Launch</h3><p>Use the listed channels to win your first 100 users — and charge from day one.</p></div></div>
</div></section>

<section id="faq" class="faq lazy"><div class="wrap" style="max-width:860px">
<div class="sec-head reveal"><span class="eyebrow">FAQ</span><h2>Questions, <span class="grad">answered</span></h2></div>{faq}
</div></section>

<section id="submit" class="lazy"><div class="wrap two">
<div class="reveal"><span class="eyebrow">Community</span><h2 style="font-size:clamp(1.8rem,4vw,2.6rem);margin:12px 0">Spotted a gap? <span class="grad">Add it.</span></h2><p style="color:var(--muted)">Your idea appears instantly in the explorer with a “Community” tag. It is saved only in your browser.</p></div>
<form class="submit-form glass" id="submitForm">
<div class="field"><label for="sTitle">Idea title</label><input id="sTitle" required maxlength="80" placeholder="e.g. WhatsApp bot for tailors"></div>
<div class="field"><label for="sType">Type</label><select id="sType"><option>App</option><option>Service</option><option>Web Tool</option></select></div>
<div class="field"><label for="sCat">Category</label><select id="sCat">{cat_opts}</select></div>
<div class="field"><label for="sProb">Problem it solves</label><textarea id="sProb" rows="3" required maxlength="400" placeholder="Who is struggling, and with what?"></textarea></div>
<div class="field"><label for="sWhy">Why now?</label><input id="sWhy" maxlength="200" placeholder="New tech, rule change, behaviour shift…"></div>
<button class="btn btn-primary" type="submit" style="justify-content:center">Add my idea</button></form>
</div></section>

<section id="newsletter" style="padding-top:10px"><div class="wrap"><div class="news glass reveal">
<span class="eyebrow">Weekly drop</span><h2>Get <span class="grad">new gap ideas</span> every Monday</h2><p>Fresh opportunities, trend signals and launch tactics. No spam.</p>
<form id="newsForm"{f' action="{e(cfg["newsletterAction"])}" method="post" target="_blank"' if cfg.get('newsletterAction') else ''}><label class="sr" for="newsEmail">Email</label><input type="email" id="newsEmail" name="email" required placeholder="you@email.com" autocomplete="email"><button class="btn btn-primary" type="submit">Subscribe</button></form>
<p id="newsMsg" style="margin-top:14px;font-size:.88rem" aria-live="polite"></p></div></div></section>
</main>
<script type="application/json" id="catIcons">{json.dumps(CAT_ICON, ensure_ascii=False)}</script>
<script type="application/json" id="genData">{json.dumps(GEN, ensure_ascii=False)}</script>
{footer(cfg, cats, js)}"""
    return head(cfg, css, title, desc, "/", "/og/site.jpg", jsonld) + body


def page_idea(cfg, db, css, js, cats, i, prev, nxt, related):
    url = idea_url(i)
    title = clip(f"{i['title']}: {i['type']} Idea for 2027", 58) + f" | {cfg['siteName']}"
    desc = clip(f"{i['pitch']} Gap Score {i['gap']}/100, MVP in {weeks_label(i['weeks'])}, budget {BUDGETS[i['budget']]}.", 158)
    og = f"/og/{i['slug']}.jpg" if os.path.exists(os.path.join(ROOT, "og", f"{i['slug']}.jpg")) else "/og/site.jpg"
    jsonld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": i["title"], "description": i["pitch"], "image": cfg["siteUrl"] + og,
         "datePublished": i["added"], "dateModified": i["updated"], "mainEntityOfPage": cfg["siteUrl"] + url, "articleSection": i["cat"],
         "keywords": ", ".join([i["cat"], i["type"], "startup idea", "business idea 2027", "market gap"]),
         "author": {"@type": "Organization", "name": cfg["siteName"], "url": cfg["siteUrl"] + "/"},
         "publisher": {"@type": "Organization", "name": cfg["siteName"], "logo": {"@type": "ImageObject", "url": cfg["siteUrl"] + "/apple-touch-icon.png"}}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Ideas", "item": cfg["siteUrl"] + "/"},
            {"@type": "ListItem", "position": 2, "name": i["cat"], "item": cfg["siteUrl"] + cat_url(i["cat"])},
            {"@type": "ListItem", "position": 3, "name": i["title"], "item": cfg["siteUrl"] + url}]},
    ]
    full = cfg["siteUrl"] + url
    share = html.escape(f"💡 {i['title']} — {i['pitch']} {full}")
    from urllib.parse import quote
    sq = quote(f"💡 {i['title']} — {i['pitch']} {full}")
    brief = (f"## {i['title']}\n{i['pitch']}\n\n- Type: {i['type']} | Category: {i['cat']}\n- Gap Score (est.): {i['gap']}/100 | Status: {STATUS[i['status']]}\n"
             f"- MVP time: {weeks_label(i['weeks'])} | Budget: {BUDGETS[i['budget']]}\n- Why now: {i['why']}\n\n**Problem:** {i['problem']}\n**Audience:** {i['audience']}\n"
             f"**Solution:** {i['solution']}\n**Monetization:** {', '.join(i['money'])}\n**Stack:** {i['stack']}\n**MVP:**\n" + "\n".join("- " + m for m in i["mvp"]) + f"\n\nSource: {full}")
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    checklist = "".join(f'<label><input type="checkbox"><span><b>{e(v["day"])}:</b> {e(v["task"])}</span></label>' for v in db["validation"])
    rel = "".join(f'<a class="glass" href="{idea_url(r)}"><b>{e(r["title"])}</b><small>{e(r["type"])} · {e(r["cat"])} · Gap {r["gap"]}</small></a>' for r in related)
    pager = (f'<div class="pager">{f"<a class=\"btn btn-ghost btn-sm\" href=\"{idea_url(prev)}\" rel=\"prev\">← {e(prev["title"])}</a>" if prev else "<span></span>"}'
             f'{f"<a class=\"btn btn-ghost btn-sm\" href=\"{idea_url(nxt)}\" rel=\"next\">{e(nxt["title"])} →</a>" if nxt else ""}</div>')
    body = f"""{header(cfg, home=False)}
<main id="main"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Ideas</a> / <a href="{cat_url(i['cat'])}">{e(i['cat'])}</a> / <span aria-current="page">{e(i['title'])}</span></nav>
<div class="idea-hero"><div>{tags(i)}<h1>{e(i['title'])}</h1><p class="pitch">{e(i['pitch'])}</p></div>{ring(i['gap'], 84, 'lg')}</div>
<div class="kpis k4" style="margin-top:18px"><div class="kpi"><span>Gap Score*</span><b style="color:{ring_color(i['gap'])}">{i['gap']}/100</b></div><div class="kpi"><span>MVP time</span><b>{weeks_label(i['weeks'])}</b></div><div class="kpi"><span>Budget</span><b>{BUDGETS[i['budget']]}</b></div><div class="kpi"><span>Earning potential*</span><b>{earn_label(i)}</b></div></div>
<div class="idea-body"><article>
<div class="why" style="margin-bottom:18px"><b>Why now?</b> {e(i['why'])}</div>
<div class="block glass"><h2>😣 The problem</h2><p>{e(i['problem'])}</p></div>
<div class="block glass"><h2>🎯 Who it's for</h2><p>{e(i['audience'])}</p></div>
<div class="block glass"><h2>💡 The solution</h2><p>{e(i['solution'])}</p></div>
<div class="block glass"><h2>🕳 Why the gap exists</h2><p>{e(i['whyGap'])}</p></div>
<div class="block glass"><h2>🛠 MVP features — build in this order</h2><ol>{li(i['mvp'])}</ol></div>
<div class="block glass"><h2>💰 How it makes money</h2><div class="pills">{''.join(f'<span>{e(m)}</span>' for m in i['money'])}</div></div>
<div class="block glass"><h2>🧱 Suggested tech stack</h2><p>{e(i['stack'])}</p></div>
<div class="block glass checklist"><h2>🧪 7-day validation checklist</h2>{checklist}</div>
<div class="block glass"><h2>📣 Getting the first 100 users</h2><ul>{li(i['channels'])}</ul></div>
<div class="block glass"><h2>⚠️ Risks to watch</h2><ul>{li(i['risks'])}</ul></div>
<p class="disclaim">* Scores are editorial estimates for prioritising ideas, not verified market data. Added {nice_date(i['added'])} · reviewed {nice_date(i['updated'])}.</p>
{pager}
</article>
<aside><div class="block glass" data-id="{i['id']}" data-url="{url}" data-title="{e(i['title'])}" data-type="{e(i['type'])}" data-cat="{e(i['cat'])}" data-gap="{i['gap']}">
<h2>At a glance</h2>{meters(i)}
<div class="side-actions"><button class="btn btn-primary" data-copy="#brief" type="button">📋 Copy idea brief</button><button class="btn btn-ghost" data-bm="{i['id']}" data-label="1" type="button">🔖 Save idea</button>
<a class="btn btn-ghost" href="https://wa.me/?text={sq}" target="_blank" rel="noopener">Share on WhatsApp</a><a class="btn btn-ghost" href="https://twitter.com/intent/tweet?text={sq}" target="_blank" rel="noopener">Post on X</a><a class="btn btn-ghost" href="https://www.linkedin.com/sharing/share-offsite/?url={quote(full)}" target="_blank" rel="noopener">Share on LinkedIn</a></div></div></aside>
</div>
<section style="padding:10px 0 60px"><h2 style="font-size:1.5rem;margin-bottom:16px">Related ideas</h2><div class="related">{rel}</div>
<p style="margin-top:22px"><a class="btn btn-primary btn-sm" href="/#explore">Browse all ideas →</a></p></section>
</div></main>
<script type="text/plain" id="brief">{e(brief)}</script>
{footer(cfg, cats, js)}"""
    return head(cfg, css, title, desc, url, og, jsonld) + body


def page_category(cfg, db, css, js, cats, c, items):
    url = cat_url(c)
    title = f"{c} Startup & App Ideas for 2027 | {cfg['siteName']}"
    desc = clip(f"{len(items)} high-demand, low-competition {c.lower()} ideas for 2027 and beyond — apps, services and web tools with MVP plans, money models and validation steps.", 158)
    jsonld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": cfg["siteUrl"] + url,
               "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": cfg["siteUrl"] + idea_url(i)} for n, i in enumerate(items)]}},
              {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Ideas", "item": cfg["siteUrl"] + "/"},
                  {"@type": "ListItem", "position": 2, "name": c, "item": cfg["siteUrl"] + url}]}]
    others = "".join(f'<a class="chip" href="{cat_url(o)}">{CAT_ICON[o]} {e(o)}</a>' for o in cats if o != c and any(i["cat"] == o for i in db["ideas"]))
    body = f"""{header(cfg, home=False)}
<main id="main"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Ideas</a> / <span aria-current="page">{e(c)}</span></nav>
<section style="padding:30px 0 20px"><span class="eyebrow">{CAT_ICON[c]} {e(c)}</span><h1 style="font-size:clamp(2rem,5vw,3.2rem);margin:12px 0">{e(c)} ideas for <span class="grad">2027 &amp; beyond</span></h1>
<p style="color:var(--muted);max-width:680px">{len(items)} market-gap opportunities in {e(c.lower())}, sorted by Gap Score. Each one includes the problem, an MVP feature list, money models and a 7-day validation plan.</p></section>
<div class="grid" id="catGrid">{''.join(card(i, heading='h2') for i in items)}</div>
<section style="padding:50px 0 60px"><h2 style="font-size:1.3rem;margin-bottom:14px">Other categories</h2><div class="chips" style="flex-wrap:wrap">{others}</div></section>
</div></main>
{footer(cfg, cats, js)}"""
    return head(cfg, css, title, desc, url, "/og/site.jpg", jsonld) + body


def page_404(cfg, css, js, cats):
    body = f"""{header(cfg, home=False)}<main id="main"><div class="wrap" style="text-align:center;padding:120px 20px">
<h1 style="font-size:clamp(3rem,10vw,6rem)" class="grad">404</h1><p style="color:var(--muted);margin:10px 0 24px">This gap is real — the page doesn't exist.</p><a class="btn btn-primary" href="/">Back to all ideas</a></div></main>{footer(cfg, cats, js)}"""
    return head(cfg, css, f"Page not found | {cfg['siteName']}", "Page not found.", "/404.html", "/og/site.jpg", []).replace(
        '<meta name="robots" content="index,follow,max-image-preview:large">', '<meta name="robots" content="noindex">') + body


# ---------------------------------------------------------------- images
def make_images(cfg, ideas):
    os.makedirs(os.path.join(ROOT, "og"), exist_ok=True)
    fav = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/>'
           '<stop offset=".5" stop-color="#8b5cf6"/><stop offset="1" stop-color="#39f5a0"/></linearGradient></defs><rect width="64" height="64" rx="16" fill="url(#g)"/>'
           '<g fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"><circle cx="29" cy="29" r="15"/><path d="m48 48-8-8M29 22v14M22 29h14"/></g></svg>')
    open(os.path.join(ROOT, "favicon.svg"), "w").write(fav)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  (Pillow not installed — skipping share images)")
        return
    fonts = glob.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf", recursive=True) + glob.glob("/usr/share/fonts/**/DejaVuSans.ttf", recursive=True)
    fb = fonts[0] if fonts else None
    fr = next((f for f in fonts if f.endswith("DejaVuSans.ttf")), fb)
    F = lambda p, s: ImageFont.truetype(p, s) if p else ImageFont.load_default()

    def base(w, h):
        img = Image.new("RGB", (w, h), (7, 6, 15))
        px = img.load()
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                a = max(0, 1 - ((x / w) ** 2 + (y / h) ** 2) ** .5 * 1.1)
                b = max(0, 1 - (((x - w) / w) ** 2 + ((y - h) / h) ** 2) ** .5 * 1.3)
                c = (int(7 + 72 * a + 20 * b), int(6 + 40 * a + 90 * b), int(15 + 150 * a + 60 * b))
                for dx in (0, 1):
                    for dy in (0, 1):
                        if x + dx < w and y + dy < h: px[x + dx, y + dy] = c
        return img

    def logo(dr, x, y, s):
        dr.rounded_rectangle([x, y, x + s, y + s], radius=s // 4, fill=(139, 92, 246))
        r = s * .26; cx = x + s * .45; cy = y + s * .45
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=max(2, s // 12))
        dr.line([cx + r * .7, cy + r * .7, x + s * .78, y + s * .78], fill="white", width=max(2, s // 12))

    def wrap(dr, text, font, maxw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if dr.textlength(t, font=font) <= maxw: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
        return lines

    def og_card(path, heading, sub, badge):
        img = base(1200, 630); dr = ImageDraw.Draw(img)
        logo(dr, 70, 60, 56); dr.text((142, 68), cfg["siteName"], font=F(fb, 38), fill="white")
        if badge:
            bw = dr.textlength(badge, font=F(fb, 28)) + 40
            dr.rounded_rectangle([1130 - bw, 64, 1130, 114], radius=25, fill=(57, 245, 160)); dr.text((1150 - bw, 73), badge, font=F(fb, 28), fill=(4, 17, 10))
        y = 190
        for ln in wrap(dr, heading, F(fb, 68), 1060)[:3]:
            dr.text((70, y), ln, font=F(fb, 68), fill="white"); y += 82
        for ln in wrap(dr, sub, F(fr, 32), 1060)[:2]:
            dr.text((70, y + 16), ln, font=F(fr, 32), fill=(190, 186, 220)); y += 44
        dr.text((70, 560), "Ideas for 2027 & beyond · updated every Monday", font=F(fr, 26), fill=(57, 245, 160))
        img.save(path, "JPEG", quality=82, optimize=True, progressive=True)

    site = os.path.join(ROOT, "og", "site.jpg")
    if not os.path.exists(site):
        og_card(site, "Build It Before Everyone Else", "High-demand, low-supply app, service and web-tool ideas.", "")
    touch = os.path.join(ROOT, "apple-touch-icon.png")
    if not os.path.exists(touch):
        img = Image.new("RGB", (180, 180), (79, 70, 229)); logo(ImageDraw.Draw(img), 0, 0, 180); img.save(touch, optimize=True)
    for i in ideas:
        p = os.path.join(ROOT, "og", f"{i['slug']}.jpg")
        if not os.path.exists(p):
            og_card(p, i["title"], i["pitch"], f"Gap {i['gap']}")


# ---------------------------------------------------------------- feeds
def sitemap(cfg, db, cats):
    upd = db["meta"]["lastUpdated"]
    urls = [("/", upd, "1.0", "weekly")] + [(cat_url(c), upd, "0.7", "weekly") for c in cats if any(i["cat"] == c for i in db["ideas"])]
    urls += [(idea_url(i), i["updated"], "0.8", "monthly") for i in db["ideas"]]
    body = "".join(f"<url><loc>{cfg['siteUrl']}{u}</loc><lastmod>{m}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>" for u, m, p, f in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def rss(cfg, db):
    items = sorted(db["ideas"], key=lambda i: (i["added"], i["id"]), reverse=True)[:30]
    rfc = lambda s: datetime.strptime(s, "%Y-%m-%d").strftime("%a, %d %b %Y 08:00:00 +0000")
    body = "".join(f"<item><title>{e(i['title'])}</title><link>{cfg['siteUrl']}{idea_url(i)}</link><guid>{cfg['siteUrl']}{idea_url(i)}</guid>"
                   f"<pubDate>{rfc(i['added'])}</pubDate><category>{e(i['cat'])}</category><description>{e(i['pitch'])}</description></item>" for i in items)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{e(cfg["siteName"])} — new market-gap ideas</title>'
            f'<link>{cfg["siteUrl"]}/</link><description>{e(cfg["description"])}</description><language>en</language>'
            f'<lastBuildDate>{rfc(db["meta"]["lastUpdated"])}</lastBuildDate>{body}</channel></rss>\n')


HTACCESS = r"""# GapHunter — generated by build.py
Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
RewriteRule ^(_src|_data|\.git|\.github)(/|$) - [F,L]
RewriteRule ^(build\.py|README\.md)$ - [F,L]
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/xml application/rss+xml application/javascript application/json image/svg+xml application/manifest+json
</IfModule>
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/html "access plus 0 seconds"
ExpiresByType application/javascript "access plus 1 year"
ExpiresByType image/png "access plus 30 days"
ExpiresByType image/jpeg "access plus 30 days"
ExpiresByType image/svg+xml "access plus 30 days"
ExpiresByType application/xml "access plus 1 hour"
ExpiresByType application/rss+xml "access plus 1 hour"
</IfModule>
<IfModule mod_headers.c>
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set X-Frame-Options "SAMEORIGIN"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
<FilesMatch "\.html$">
Header set Cache-Control "public, max-age=0, must-revalidate"
</FilesMatch>
<FilesMatch "app\.[0-9a-f]+\.js$">
Header set Cache-Control "public, max-age=31536000, immutable"
</FilesMatch>
</IfModule>
"""


# ---------------------------------------------------------------- main
def write(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    cfg, db = load()
    errs = validate(db)
    if errs:
        print("✗ Data errors:\n  " + "\n  ".join(errs))
        sys.exit(1)
    print(f"✓ Data valid: {len(db['ideas'])} ideas, {len(db['trends'])} trends")
    if "--check" in sys.argv:
        return
    if "yourdomain.com" in cfg["siteUrl"]:
        print("! WARNING: set siteUrl in _data/config.json to your real subdomain for correct SEO links")

    cats = db["categories"]
    css = min_css(open(os.path.join(SRC, "styles.css"), encoding="utf-8").read())
    js_src = min_js(open(os.path.join(SRC, "app.js"), encoding="utf-8").read())
    h = hashlib.sha1(js_src.encode()).hexdigest()[:10]
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for old in glob.glob(os.path.join(ROOT, "assets", "app.*.js")):
        os.remove(old)
    write(f"assets/app.{h}.js", js_src)
    js = f"/assets/app.{h}.js"

    make_images(cfg, db["ideas"])

    # clean generated folders so removed ideas disappear
    for d in ("ideas", "category"):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    live = {f"{i['slug']}.jpg" for i in db["ideas"]} | {"site.jpg"}
    for f in glob.glob(os.path.join(ROOT, "og", "*.*")):
        if os.path.basename(f) not in live: os.remove(f)

    write("index.html", min_html(page_index(cfg, db, css, js, cats)))
    by_gap = sorted(db["ideas"], key=lambda i: -i["gap"])
    for n, i in enumerate(by_gap):
        same = [r for r in by_gap if r["cat"] == i["cat"] and r["id"] != i["id"]]
        related = (same + [r for r in by_gap if r["type"] == i["type"] and r["id"] != i["id"] and r not in same])[:3]
        prev = by_gap[n - 1] if n > 0 else None
        nxt = by_gap[n + 1] if n + 1 < len(by_gap) else None
        write(f"ideas/{i['slug']}/index.html", min_html(page_idea(cfg, db, css, js, cats, i, prev, nxt, related)))
    for c in cats:
        items = [i for i in by_gap if i["cat"] == c]
        if items:
            write(f"category/{slugify(c)}/index.html", min_html(page_category(cfg, db, css, js, cats, c, items)))
    write("404.html", min_html(page_404(cfg, css, js, cats)))
    write("sitemap.xml", sitemap(cfg, db, cats))
    write("feed.xml", rss(cfg, db))
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /_src/\nDisallow: /_data/\n\nSitemap: {cfg['siteUrl']}/sitemap.xml\n")
    write(".htaccess", HTACCESS)
    write("manifest.webmanifest", json.dumps({"name": cfg["siteName"], "short_name": cfg["siteName"], "start_url": "/", "display": "standalone",
                                              "background_color": "#07060f", "theme_color": "#07060f",
                                              "icons": [{"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}, {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}]}, indent=1))
    kb = os.path.getsize(os.path.join(ROOT, "index.html")) // 1024
    print(f"✓ Built: index.html ({kb} KB), {len(db['ideas'])} idea pages, {sum(1 for c in cats if any(i['cat']==c for i in db['ideas']))} category pages, sitemap, feed, og images")


if __name__ == "__main__":
    main()
