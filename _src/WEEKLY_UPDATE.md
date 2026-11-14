# Weekly update playbook (run every Monday)

You are updating GapHunter, a static site of market-gap ideas for 2027 and beyond.
Repo: `MS-Bytes/GapHunter` (branch `main`). All content lives in `_data/ideas.json`;
`python3 build.py` regenerates the site. Do the whole job without asking questions.

## 1. Get the repo
- If `/home/claude/gaphunter` is not a working clone, attach the repo (`MS-Bytes/GapHunter`,
  push access) and clone it with `git clone --depth 1`. Otherwise `git pull --ff-only`.
- Read `_data/ideas.json`. Note every existing title, slug and the highest `id`.

## 2. Research (8–12 web searches)
Look for developments from roughly the last 30 days that open new gaps for 2027+:
new AI models/APIs and price drops, platform policy changes (WhatsApp, Meta, Google, app stores),
new regulations, payment/fintech changes, consumer behaviour shifts, and specifically
Pakistan / South Asia market news. Prefer original sources (company blogs, official
announcements, reputable news).

## 3. Add exactly 5 new ideas
- Not duplicates (or near-duplicates) of existing titles.
- Mix of `App`, `Service`, `Web Tool`; at least 2 with `"pk": true`.
- `why` must point to a concrete recent development you actually found. Never invent
  statistics, user counts or market sizes. Scores are editorial estimates.
- Write in plain English, your own words — never copy sentences from sources.
- Fill every field exactly like existing ideas:
  `id` (previous max + 1, +2…), `slug` (lowercase-with-dashes, unique), `added` and `updated`
  (today, YYYY-MM-DD), `title`, `pitch` (one sentence), `type`, `cat` (from `categories`),
  `gap` (0–100 int), `dem`/`comp`/`diff` (1–5 int), `weeks` (int), `budget` (Low/Medium/High),
  `status` (usually `early`), `pk` (bool), `why`, `problem`, `audience`, `solution`, `whyGap`,
  `money` [list], `stack`, `mvp` [4–6 items, in build order], `risks` [list], `channels` [list].
- A new category is allowed only if none fits; add it to `categories` AND add an emoji for it
  in `CAT_ICON` inside `build.py`.

## 4. Re-check 5 existing ideas
Pick the 5 with the oldest `updated` date. Search for new competitors or changes.
If the evidence supports it, adjust `status` (early → hot → crowded), `comp` and `gap`.
Set their `updated` to today either way.

## 5. Update trends
In `trends`: move trends that clearly progressed right (`stage` +0.03 to +0.10), add up to 2 new
trends from this week's research, remove any with `stage` > 0.97. Keep 12–20 trends.

## 6. Meta
Set `meta.lastUpdated` to today and `meta.lastBatch` to the list of the 5 new ids.

## 7. Build and verify
Run `python3 build.py`. It must print `✓ Data valid` and `✓ Built`. If it reports data errors,
fix the JSON and run again. Do not edit generated files by hand.

## 8. Publish
```
git add -A
git commit -m "Weekly update YYYY-MM-DD: +5 ideas"
git -c push.negotiate=true push origin main
```
(Use the commit attribution lines your session requires.)

## 9. Report
Send the owner a short message in Roman Urdu: the 5 new idea titles, any status changes,
and confirmation that the push succeeded. If anything failed, say exactly what.
