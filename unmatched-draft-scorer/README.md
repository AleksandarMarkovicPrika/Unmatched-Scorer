# Unmatched Draft Scorer

Score Unmatched rosters, generate balanced random drafts with six generators,
edit matchups, and compare generators' pick rates. The app loads Tabletop
League's hero-matchup data automatically; a GitHub Action refreshes it every day.

Data: [Tabletop League (tabletopleague.com)](https://www.tabletopleague.com)

## How it works

```
every day 04:17 UTC                                         anyone, no sign-in
GitHub Action ──(your API key)──▶ Tabletop League export   ┌──────────────────────────┐
      │                                                     │ <you>.github.io/<repo>/  │
      ├─ validates the CSV (columns, ≥500 matchups) ───────▶│   index.html  (the app)  │
      ├─ commits data/ if it changed                        │   data/…csv   (public)   │
      └─ publishes to GitHub Pages ────────────────────────▶└──────────────────────────┘
```

- Your API key stays a hidden repository secret. It is never in the page or the repo.
- A failed download never breaks the site: the last good data stays published, the
  run turns red, and GitHub emails you.
- The CSV is also a public URL other tools can read:
  `https://<you>.github.io/<repo>/data/hero-matchups-unmatched.csv`

## One-time setup (about 10 minutes)

1. **Create the repo.** On github.com: **+ → New repository**, name it e.g.
   `unmatched-draft-scorer`, set it to **Public**, and create it.
2. **Upload the files.** On the new repo's page choose **uploading an existing file**,
   then drag in everything from this folder, *including* the hidden `.github` folder.
   (On macOS press Cmd+Shift+. in Finder to show it.) Commit.
3. **Turn on Pages.** **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Get your Tabletop League API key.** Sign in at tabletopleague.com and create a
   personal key under **Settings → Data** (it starts with `ttl_user_`).
5. **Find the export URL.** While signed in, open
   <https://www.tabletopleague.com/api/reference>, find the public statistics export
   for **hero matchups** (under `/api/v1/public/hero-stats…`), choose Unmatched, and
   copy the full request URL.
6. **Store both in the repo.** **Settings → Secrets and variables → Actions**:
   - **Secrets** tab → *New repository secret*: name `TTL_API_KEY`, value = your key.
   - **Variables** tab → *New repository variable*: name `TTL_CSV_URL`, value = the URL.
7. **Run it once.** **Actions → Refresh data and publish → Run workflow**. When it turns
   green, your app is live at `https://<you>.github.io/<repo>/`.

The repo already includes a copy of the matchup data, so the site works from step 3 on;
steps 4–7 keep it fresh.

## Good to know

- **Limits.** Tabletop League caps exports at three per 24 hours. The schedule uses
  one a day, which leaves room for two manual runs.
- **Terms.** Their Terms (section 7) allow free non-commercial public use of these
  aggregate stats with the credit line above, which the app shows on every tab. Don't
  sell the data or build a competing service on it.
- **GitHub pauses idle schedules.** If a public repo has no activity for 60 days, GitHub
  disables scheduled workflows and emails you. Daily data commits normally count as
  activity; if it ever gets paused, re-enable it on the Actions tab.
- **Changing the app.** Edit `index.html` and commit; the site republishes automatically.
- **Custom matchups** (Matchups tab) are saved in each visitor's own browser and are
  never overwritten by the refresh.
