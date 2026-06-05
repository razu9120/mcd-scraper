# mcd-scraper System Design

**Decisions finalized**
- Execution: GitHub Actions (daily at JST 3:00 = UTC 18:00)
- Push target: `main` branch
- Notifications: none
- Data granularity: summary + link to source

---

## 1. Note Structure

- [x] Decide folder structure

  ```
  mcd-scraper/
  ├── daily/
  │   └── YYYY-MM-DD.md          # Daily summary across all categories
  ├── topics/
  │   ├── happy-set/
  │   │   └── YYYY-MM-DD.md      # Happy Set toy info
  │   ├── new-products/
  │   │   └── YYYY-MM-DD.md      # New product announcements
  │   └── rewards/
  │       └── YYYY-MM-DD.md      # Reward catalog & rules
  ├── scripts/
  │   └── fetch_mcd.py
  ├── .claude/
  │   └── skills/
  │       └── fetch-all-mcd/
  │           └── SKILL.md
  ├── .github/
  │   └── workflows/
  │       └── fetch-mcd.yml
  ├── CLAUDE.md
  ├── DESIGN.md
  └── README.md
  ```

- [x] Define YAML frontmatter schema

  ```yaml
  ---
  date: YYYY-MM-DD
  topic: happy-set | new-products | rewards
  tags: [mcd-scraper, auto-generated]
  ---
  ```

- [x] Define note heading template

  ```markdown
  # {Topic} - YYYY-MM-DD

  ## Summary
  (2-3 sentence overview)

  ## Details
  - **Title** — one-line description ([source]({url}))
  - ...
  ```

---

## 2. Rules (CLAUDE.md)

- [x] Define scraping targets and data to collect

  | Topic | Source URL | Data to collect |
  |---|---|---|
  | Happy Set | `mcdonalds.co.jp/family/happyset/` | Toy series name, period, image URL |
  | New Products | `mcdonalds.co.jp/company/news/` | Product name, launch date, description, source URL |
  | Rewards | `mcdonalds.co.jp/shop/rewards/` | Point rules, exchange catalog, expiry rules |

- [x] Define note quality rules
  - Write summaries in English
  - Always include the full source page URL (no URL shorteners)
  - Overwrite existing notes if the same date already exists

- [x] Define commit message format
  - Format: `auto: fetch mcd-scraper YYYY-MM-DD`

---

## 3. Script (`scripts/fetch_mcd.py`)

- [x] Implement Happy Set scraper
  - Target: `mcdonalds.co.jp/family/happyset/`
  - Data: toy series name, start date, end date, image URL
- [x] Implement New Products scraper
  - Target: `mcdonalds.co.jp/company/news/`
  - Data: product name, launch date, description, source URL
- [x] Implement Rewards scraper
  - Target: `mcdonalds.co.jp/shop/rewards/`
  - Data: point rules, exchange catalog items, expiry rules
- [x] Generate `topics/happy-set/YYYY-MM-DD.md`
- [x] Generate `topics/new-products/YYYY-MM-DD.md`
- [x] Generate `topics/rewards/YYYY-MM-DD.md`
- [x] Generate `daily/YYYY-MM-DD.md` (combined summary of all categories)
- [x] Test locally: `python3 scripts/fetch_mcd.py`
- [x] Confirm all 4 markdown files are generated correctly

---

## 4. GitHub Actions Workflow (`.github/workflows/fetch-mcd.yml`)

- [x] Create workflow file

  ```yaml
  name: Fetch MCD Info

  on:
    schedule:
      - cron: '0 18 * * *'   # Daily UTC 18:00 = JST 03:00
    workflow_dispatch:        # Allow manual runs

  permissions:
    contents: write

  jobs:
    fetch:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Fetch MCD info
          run: python3 scripts/fetch_mcd.py

        - name: Commit and push
          run: |
            git config user.name  "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add -A
            git diff --cached --quiet || git commit -m "auto: fetch mcd-scraper $(TZ=Asia/Tokyo date +%Y-%m-%d)"
            git push
  ```

- [x] Confirm no secrets or API keys are required

---

## 5. Claude Code Skill (`.claude/skills/fetch-all-mcd/`)

- [x] Create `SKILL.md`

  ```yaml
  ---
  name: fetch-all-mcd
  description: Fetch the latest McDonald's Japan info (Happy Set, New Products, Rewards) and generate Obsidian notes
  disable-model-invocation: true
  allowed-tools: WebFetch Write Bash(python3 *) Bash(git *)
  ---
  ```

  - Action: run `scripts/fetch_mcd.py`, then git commit & push the generated notes

---

## 6. Cost

**Completely free**
- GitHub Actions: unlimited for public repositories
- Scraping target: `mcdonalds.co.jp` (public pages, no auth required)
- Libraries: Python standard library only (`urllib`, `html.parser`) — no installs needed
- API keys: none required

---

## 7. Implementation Steps

- [x] **Step 1** Create folder structure, `DESIGN.md`, and `CLAUDE.md`
- [x] **Step 2** Implement `scripts/fetch_mcd.py` and verify locally
- [x] **Step 3** Create `.github/workflows/fetch-mcd.yml`
- [x] **Step 4** Create `.claude/skills/fetch-all-mcd/SKILL.md`
- [ ] **Step 5** Push to GitHub and verify with a manual `workflow_dispatch` run
- [ ] **Step 6** Open generated notes in Obsidian and confirm formatting
- [ ] **Step 7** Confirm scheduled runs fire correctly at JST 3:00 daily
