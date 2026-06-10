# World Cup 2026 Pool Tracker

A tiny website to track a draft pool for the 2026 World Cup. No logins — it's just
information. One person enters everyone's drafted countries and updates results
(or lets the API do it); everyone else views standings and the schedule.

## Scoring (flat, no goals) — the source of truth

Defined in `app/scoring.py`:

- **Group stage:** Win = 3, Draw = 1, Loss = 0 (goals ignored)
- **Knockout: +4 for every round a team reaches**, cumulative —
  reach Round of 32 (qualify) +4, R16 +4, QF +4, SF +4, Final +4, **Champion +4**
- 3rd-place playoff scores nothing.

So a champion earns its group points + 24; a finalist + 20; a semifinalist + 16.
A player's score = the sum of their drafted countries' points. (Verified by
`app/test_scoring.py`.)

## What's included
- Real 2026 field: 12 groups, all 72 group fixtures (with dates), and the knockout
  bracket skeleton (teams fill in as it resolves).
- **Standings** page — ranked; tap a player to see each team's points + breakdown.
- **Schedule** page — Live / Upcoming / Completed.
- **Admin** page — add players, enter their picks, update match results, run API sync.

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload --app-dir app      # http://localhost:8000
```
Uses a local SQLite file (`pool.db`) automatically.

## Deploy: GitHub → Railway (one service)
1. **Push to GitHub:** create a new repo and push this folder.
2. **Railway:** New Project → *Deploy from GitHub repo* → pick the repo.
   Railway auto-detects Python and runs the start command in `railway.json`.
3. **Add a database:** in the project, *New → Database → PostgreSQL*. Railway sets
   `DATABASE_URL` automatically — the app uses it (and keeps your data across deploys).
4. **Optional env vars** (Settings → Variables):
   - `FOOTBALL_API_KEY` — a free key from football-data.org to auto-pull fixtures/scores.
   - `ADMIN_KEY` — if set, the admin write actions require this key (enter it once on the
     Admin page). Leave unset to keep admin open (fine for a private pool).
5. Open the Railway URL. Go to **/admin.html** to add players and their picks.

## Daily use
- **Manual:** on Admin, set each finished match's score + status = FINISHED. For knockout
  matches, pick the two teams and (for shootouts) the winner. Standings update instantly.
- **API:** click **Sync from API** (needs `FOOTBALL_API_KEY`). Any match you edited by hand
  is marked *manual* and will never be overwritten by a sync.

## How points are awarded mechanically
A team "reaches" a knockout round simply by appearing in a match of that round, so as you
fill in the bracket (by hand or via sync) the +4s are awarded automatically. Champion is the
winner of the Final.
