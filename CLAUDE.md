# mcd-scraper

Automated repository that collects McDonald's Japan information daily (Happy Set,
New Products, Rewards) from the official website and stores it as Obsidian notes.

## Note structure

- Daily summaries: `daily/YYYY-MM-DD.md`
- Topic notes: `topics/{happy-set,new-products,rewards}/YYYY-MM-DD.md`

## Scraping targets

| Topic | Source URL | Data collected |
|---|---|---|
| Happy Set | `https://www.mcdonalds.co.jp/family/happyset/` | Toy/book series name, period, detail URL, image URL |
| New Products | `https://www.mcdonalds.co.jp/company/news/{YYYY}/` | News title, publish date, source URL |
| Rewards | `https://www.mcdonalds.co.jp/shop/rewards/` | Program headline, FAQ items, notes (rules, expiry, limits) |

## Note format rules

- Frontmatter must include `date`, `topic`, and `tags: [mcd-scraper, auto-generated]`
- Write summaries in English (keep original Japanese product/series names as-is)
- Source links must be full URLs (no shortened links)
- If a note for the same date already exists, overwrite it
- All dates are calculated in JST (Asia/Tokyo)

## Automation

- GitHub Actions runs daily at JST 03:00 (UTC 18:00) via `.github/workflows/fetch-mcd.yml`
- The script `scripts/fetch_mcd.py` uses only the Python standard library — no
  external dependencies, no API keys
- Commit message format: `auto: fetch mcd-scraper YYYY-MM-DD`

## Manual execution

- Run `python3 scripts/fetch_mcd.py` locally, or
- Use the `/fetch-all-mcd` skill from Claude Code
