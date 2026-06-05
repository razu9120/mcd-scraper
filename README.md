# mcd-scraper

Automatically collects McDonald's Japan information daily from the official
website ([mcdonalds.co.jp](https://www.mcdonalds.co.jp/)) and stores it as
Obsidian notes.

## What it collects

| Topic | Source | Data |
|---|---|---|
| Happy Set | [family/happyset](https://www.mcdonalds.co.jp/family/happyset/) | Current/next toy & book lineup, wave schedule, images |
| New Products | [company/news](https://www.mcdonalds.co.jp/company/news/2026/) | News release titles, dates, links |
| Rewards | [shop/rewards](https://www.mcdonalds.co.jp/shop/rewards/) | Program rules, notes, FAQ |

## Note structure

```
daily/YYYY-MM-DD.md                  # Daily summary across all topics
topics/happy-set/YYYY-MM-DD.md
topics/new-products/YYYY-MM-DD.md
topics/rewards/YYYY-MM-DD.md
```

## Automation

GitHub Actions runs `scripts/fetch_mcd.py` daily at **JST 03:00** (UTC 18:00)
and pushes the generated notes to `main`. Manual runs are available via
`workflow_dispatch`.

The script uses only the Python standard library — no dependencies, no API keys,
completely free.

## Manual execution

```bash
python3 scripts/fetch_mcd.py
```

Or use the `/fetch-all-mcd` skill from Claude Code.

## Design

See [DESIGN.md](DESIGN.md) for the full system design and [CLAUDE.md](CLAUDE.md)
for note format rules.
