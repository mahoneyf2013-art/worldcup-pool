# Putting your World Cup Pool site online — step by step

No experience needed. You'll do three things: (1) put the code on **GitHub** (a free
code-storage website), (2) tell **Railway** (a free hosting website) to run it, and
(3) add a database so your data is saved. Budget ~20 minutes. Take it slow; you can't
break anything.

You will need: an email address, and the folder on your computer at
`Downloads\April Forecast\wc-pool-site`.

---

## PART 1 — Put the code on GitHub

**1.1** Go to **https://github.com** and click **Sign up**. Make a free account
(email, password, username). Verify your email when it asks.

**1.2** Once logged in, look at the **top-right corner** for a small **"+"** icon.
Click it, then click **"New repository"**.
(A "repository", or "repo", is just a folder of code on GitHub.)

**1.3** On the new-repository page:
- **Repository name:** type `worldcup-pool` (any name is fine, no spaces).
- Choose **Private** (only you can see it) — recommended. Public is also fine.
- Do **NOT** tick "Add a README" or any other box. Leave them unchecked.
- Click the green **"Create repository"** button.

**1.4** You'll land on a mostly-empty page with some instructions. Ignore the code
instructions. Find the line that says **"uploading an existing file"** (it's a blue
link in a sentence like *"…or upload an existing file"*) and click it.
- If you don't see that link, look for an **"Add file"** button (top of the file list)
  and choose **"Upload files"**.

**1.5** Now open your computer's **File Explorer** and go to:
`Downloads\April Forecast\wc-pool-site`

Inside you'll see these items: an **`app`** folder, a **`web`** folder, and several
loose files (`README.md`, `requirements.txt`, `Procfile`, `railway.json`, `.gitignore`,
`DEPLOY_GUIDE.md`, plus a couple of test files).

**1.6** Select **everything inside** that `wc-pool-site` folder (click the first item,
hold **Shift**, click the last, so they're all highlighted — including the `app` and
`web` folders). **Drag all of it** onto the GitHub upload page (the big dashed box that
says *"Drag files here"*).
- Wait until it finishes uploading. You should see `app/…`, `web/…`, and the loose files
  listed. (It's important the files land at the **top level** — not inside an extra
  `wc-pool-site` folder.)

**1.7** Scroll down and click the green **"Commit changes"** button. ("Commit" just
means "save".) Your code is now on GitHub. 🎉

---

## PART 2 — Deploy on Railway

**2.1** Go to **https://railway.com** (formerly railway.app) and click **Login**.
Choose **"Login with GitHub"** and approve when it asks — this links the two accounts so
Railway can read your code.

**2.2** Click **"New Project"** (a big button on your dashboard).

**2.3** Choose **"Deploy from GitHub repo"**.
- The first time, it'll ask permission to access your GitHub repos. Click
  **"Configure GitHub App"** / **"Install"** and allow access (you can pick "All
  repositories" or just `worldcup-pool`). Then come back.

**2.4** Pick your **`worldcup-pool`** repo from the list.
- Railway starts building automatically. You'll see logs scrolling. Wait 1–3 minutes.
  It's fine if it finishes with a small warning — we still need to add the database next.

---

## PART 3 — Add the database (so your data is saved)

Without this, your players and results would disappear whenever the app restarts.

**3.1** In your project (the canvas with boxes/"services"), click the **"+ New"** or
**"Create"** button (usually top-right or by right-clicking the canvas).

**3.2** Choose **"Database"** → **"Add PostgreSQL"**. A new "Postgres" box appears.

**3.3** Now connect it to your app. Click on your **app service** (the box named after
your repo, *not* the Postgres one). Open its **"Variables"** tab.

**3.4** Click **"New Variable"**. 
- For the **name**, type: `DATABASE_URL`
- Click in the **value** box and type two open curly braces: `${{`
  — a little menu pops up. Choose **Postgres**, then choose **DATABASE_URL**.
  The value should end up looking like `${{Postgres.DATABASE_URL}}`.
- Click **Add**. 

**3.5** Railway will redeploy the app automatically (watch for it to finish). Your data
will now persist.

---

## PART 4 — Get your web address

**4.1** Click your **app service** → **"Settings"** tab → scroll to **"Networking"**
(sometimes "Public Networking").

**4.2** Click **"Generate Domain"**. Railway gives you a URL like
`worldcup-pool-production.up.railway.app`. Click it — your site is live!

**4.3** Bookmark that URL. Share it with your friends — they can all view standings and
the schedule. (No login needed for anyone.)

---

## PART 5 — Optional extras

**Auto-updating scores (free):**
1. Go to **https://www.football-data.org**, click **Get free API token**, register.
   They email you a long code (your "token").
2. In Railway → app service → **Variables** → **New Variable**:
   name `FOOTBALL_API_KEY`, value = that token. Add it.
3. On your site's **Admin** page, click **"Sync from API"** to pull scores.
   (If a match isn't covered or looks wrong, just type the result in by hand — manual
   entries are never overwritten by the sync.)

**Lock the Admin page (so only you can edit):**
1. In Railway → app service → **Variables** → **New Variable**:
   name `ADMIN_KEY`, value = any password you choose (e.g. `pool2026`). Add it.
2. On your site's **Admin** page, type that same password into the **"Admin key"** box
   and click **"Save key"**. Now only someone with the key can add players or edit results.
   (Everyone can still view standings/schedule freely.)

---

## PART 6 — Set up your pool

1. Go to **`your-url/admin.html`** (add `/admin.html` to the end of your Railway URL).
2. Under **Players & picks**, type a player's name → **Add player**. Repeat for everyone.
3. For each player, use the dropdowns to pick the countries they drafted →
   **Save picks**.
4. As games finish, update them under **Match results** (or use Sync). Standings update
   instantly.

That's it — you're done!

---

## If something goes wrong

- **Build failed / app won't start:** open the app service → **Deployments** → click the
  latest → read the log. Most common cause is files uploaded into an extra nested folder
  in Step 1.6. Fix: in GitHub, make sure `requirements.txt` and the `app` folder are at
  the **top level** of the repo (not inside `worldcup-pool/wc-pool-site/...`).
- **Site loads but standings are empty:** that's normal until you add players on
  `/admin.html`.
- **"Admin key required" error:** you set an `ADMIN_KEY` in Railway but didn't enter it on
  the Admin page. Type it into the "Admin key" box and click Save key.
- **Data disappeared after a change:** the Postgres database (Part 3) wasn't linked.
  Re-check that the app service has a `DATABASE_URL` variable pointing to Postgres.
- **Button names look different:** GitHub and Railway tweak their layouts often. The
  *words* might move, but the steps are the same — look for the closest match.

Stuck on a specific step? Tell me which number and what you see on screen, and I'll
walk you through it.
