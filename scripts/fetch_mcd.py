#!/usr/bin/env python3
"""Fetch McDonald's Japan info (Happy Set / New Products / Rewards) and
generate Obsidian notes.

Uses only the Python standard library — no external dependencies, no API keys.

Output:
    topics/happy-set/YYYY-MM-DD.md
    topics/new-products/YYYY-MM-DD.md
    topics/rewards/YYYY-MM-DD.md
    daily/YYYY-MM-DD.md
"""

import html
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://www.mcdonalds.co.jp"
HAPPYSET_URL = f"{BASE_URL}/family/happyset/"
REWARDS_URL = f"{BASE_URL}/shop/rewards/"

JST = timezone(timedelta(hours=9))
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Max news items per note
NEWS_LIMIT = 15


def fetch(url: str) -> str:
    """Fetch a URL and return the decoded HTML, or '' on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as e:
        print(f"WARN: failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def clean(text: str) -> str:
    """Unescape HTML entities and collapse whitespace."""
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def absolutize(url: str) -> str:
    """Make a protocol-relative or root-relative URL absolute."""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return BASE_URL + url
    return url


# ---------------------------------------------------------------------------
# Happy Set
# ---------------------------------------------------------------------------

def parse_happyset_cards(section_html: str) -> list[dict]:
    """Extract toy/book cards (title, link, image) from a page section."""
    cards = []
    for m in re.finditer(
        r"<div class='container-card[^']*'>(.*?)</h3>", section_html, re.S
    ):
        block = m.group(1)
        link = re.search(r"<a href='([^']+)' class='container-card-link'>", block)
        img = re.search(r"<img data-src='([^']+)'", block)
        title = re.search(r"class='container-card-title[^']*'>([^<]+)$", block)
        if title:
            cards.append(
                {
                    "title": clean(title.group(1)),
                    "url": absolutize(link.group(1)) if link else HAPPYSET_URL,
                    "image": absolutize(img.group(1)) if img else "",
                }
            )
    return cards


def fetch_happyset() -> dict:
    """Scrape the Happy Set top page (current + next lineup) and the
    detail page (wave periods)."""
    page = fetch(HAPPYSET_URL)
    data = {"current": [], "next": [], "next_heading": "", "waves": []}
    if not page:
        return data

    # Current lineup: between the first '今回のハッピーセット' h2 and the next section
    cur = re.search(
        r"<h2>今回のハッピーセット</h2>(.*?)(?=<h2[ >])", page, re.S
    )
    if cur:
        data["current"] = parse_happyset_cards(cur.group(1))

    # Next lineup: heading like '6/12(金)からのハッピーセット'
    nxt = re.search(
        r"<h2>([^<]*からのハッピーセット)</h2>(.*?)(?=<h2[ >])", page, re.S
    )
    if nxt:
        data["next_heading"] = clean(nxt.group(1))
        data["next"] = parse_happyset_cards(nxt.group(2))

    # Wave periods (第１弾 5/15(金)～5/28(木) etc.) live on the detail page
    detail = fetch(f"{HAPPYSET_URL}detail01/")
    if detail:
        text = re.sub(r"<style.*?</style>", "", detail, flags=re.S)
        text = re.sub(r"<script.*?</script>", "", text, flags=re.S)
        text = clean(re.sub(r"<[^>]+>", " ", text))
        for m in re.finditer(
            r"(第\S+弾)\s*(\d+/\d+\s*\([^)]+\)\s*[～〜]\s*\d+/\d+\s*\([^)]+\))", text
        ):
            data["waves"].append({"wave": m.group(1), "period": clean(m.group(2))})
    return data


# ---------------------------------------------------------------------------
# New Products (news releases)
# ---------------------------------------------------------------------------

def fetch_news(year: int) -> list[dict]:
    """Scrape the news release index for the given year."""
    page = fetch(f"{BASE_URL}/company/news/{year}/")
    items = []
    if not page:
        return items
    for m in re.finditer(
        r"<a href='(/company/news/%d/[^']+)'[^>]*>\s*<span[^>]*>\s*"
        r"<span[^>]*>([\d.]+)</span>\s*<span[^>]*>(.*?)</span>" % year,
        page,
        re.S,
    ):
        url, date_str, title = m.groups()
        items.append(
            {
                "url": absolutize(url),
                "date": clean(date_str),  # e.g. 2026.05.08
                "title": clean(title),
            }
        )
    # Newest first (page lists newest-first already, but sort to be safe)
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


# ---------------------------------------------------------------------------
# Rewards
# ---------------------------------------------------------------------------

def fetch_rewards() -> dict:
    """Scrape the My McDonald's Rewards page: headline, FAQ items, notes."""
    page = fetch(REWARDS_URL)
    data = {"headline": "", "faq": [], "notes": []}
    if not page:
        return data

    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    if h1:
        data["headline"] = clean(re.sub(r"<[^>]+>", " ", h1.group(1)))

    # FAQ block: questions listed between 'よくあるご質問' and '注意事項'
    faq_m = re.search(r"よくあるご質問</h2>(.*?)注意事項</h2>", page, re.S)
    if faq_m:
        block = faq_m.group(1)
        for q in re.finditer(r"<a href='([^']+)'[^>]*>(.*?)</a>", block, re.S):
            text = clean(re.sub(r"<[^>]+>", " ", q.group(2)))
            if text and "その他" not in text:
                data["faq"].append({"q": text, "url": absolutize(q.group(1))})

    # Notes (注意事項): ※-prefixed list items
    notes_m = re.search(r"注意事項</h2>(.*)", page, re.S)
    if notes_m:
        text = re.sub(r"<script.*?</script>", "", notes_m.group(1), flags=re.S)
        text = clean(re.sub(r"<[^>]+>", " ", text))
        for note in re.findall(r"※([^※]+?)(?=※|ご不明な点|$)", text):
            note = clean(note)
            if note and len(note) > 5:
                data["notes"].append(note)
    return data


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def frontmatter(date: str, topic: str) -> str:
    return (
        f"---\n"
        f"date: {date}\n"
        f"topic: {topic}\n"
        f"tags: [mcd-scraper, auto-generated]\n"
        f"---\n\n"
    )


def render_happyset(date: str, hs: dict) -> str:
    md = frontmatter(date, "happy-set")
    md += f"# Happy Set - {date}\n\n"
    md += "## Summary\n\n"
    cur_names = ", ".join(c["title"] for c in hs["current"]) or "(none found)"
    md += (
        f"Current Happy Set lineup: {cur_names}. "
        f"Source: [Happy Set official page]({HAPPYSET_URL})\n\n"
    )

    md += "## Current Lineup\n\n"
    if hs["current"]:
        md += "| Item | Link | Image |\n|---|---|---|\n"
        for c in hs["current"]:
            img = f"[image]({c['image']})" if c["image"] else "-"
            md += f"| {c['title']} | [detail]({c['url']}) | {img} |\n"
        md += "\n"
    else:
        md += "No items found.\n\n"

    if hs["waves"]:
        md += "## Schedule\n\n"
        md += "| Wave | Period |\n|---|---|\n"
        for w in hs["waves"]:
            md += f"| {w['wave']} | {w['period']} |\n"
        md += "\n"

    if hs["next"]:
        md += f"## Next Lineup ({hs['next_heading']})\n\n"
        md += "| Item | Link | Image |\n|---|---|---|\n"
        for c in hs["next"]:
            img = f"[image]({c['image']})" if c["image"] else "-"
            md += f"| {c['title']} | [detail]({c['url']}) | {img} |\n"
        md += "\n"

    md += f"## Source\n\n- [ハッピーセット 本・おもちゃ紹介]({HAPPYSET_URL})\n"
    return md


def render_news(date: str, year: int, items: list[dict]) -> str:
    md = frontmatter(date, "new-products")
    md += f"# New Products & News - {date}\n\n"
    md += "## Summary\n\n"
    md += (
        f"Latest {min(len(items), NEWS_LIMIT)} news releases from McDonald's "
        f"Japan ({len(items)} total in {year}). "
        f"Source: [News releases]({BASE_URL}/company/news/{year}/)\n\n"
    )
    md += "## Latest Releases\n\n"
    if items:
        for it in items[:NEWS_LIMIT]:
            md += f"- **{it['date']}** — {it['title']} ([source]({it['url']}))\n"
    else:
        md += "No news items found.\n"
    md += f"\n## Source\n\n- [ニュースリリース]({BASE_URL}/company/news/{year}/)\n"
    return md


def render_rewards(date: str, rw: dict) -> str:
    md = frontmatter(date, "rewards")
    md += f"# My McDonald's Rewards - {date}\n\n"
    md += "## Summary\n\n"
    headline = rw["headline"] or "My McDonald's Rewards program info"
    md += f"{headline}. Source: [Rewards official page]({REWARDS_URL})\n\n"
    if rw["notes"]:
        md += "## Rules & Notes\n\n"
        for n in rw["notes"]:
            md += f"- {n}\n"
        md += "\n"
    if rw["faq"]:
        md += "## FAQ\n\n"
        for f in rw["faq"]:
            md += f"- [{f['q']}]({f['url']})\n"
        md += "\n"
    md += f"## Source\n\n- [Myマクドナルド リワード]({REWARDS_URL})\n"
    return md


def render_daily(date: str, hs: dict, news: list[dict], rw: dict) -> str:
    md = frontmatter(date, "daily")
    md += f"# McDonald's Japan Daily - {date}\n\n"

    md += "## Happy Set\n\n"
    if hs["current"]:
        names = ", ".join(c["title"] for c in hs["current"])
        md += f"- Current lineup: {names}\n"
        for w in hs["waves"]:
            md += f"- {w['wave']}: {w['period']}\n"
        if hs["next_heading"]:
            nxt = ", ".join(c["title"] for c in hs["next"])
            md += f"- Next ({hs['next_heading']}): {nxt}\n"
    else:
        md += "- No data\n"
    md += f"\n→ [[topics/happy-set/{date}|details]]\n\n"

    md += "## New Products & News\n\n"
    if news:
        for it in news[:5]:
            md += f"- **{it['date']}** — {it['title']} ([source]({it['url']}))\n"
    else:
        md += "- No data\n"
    md += f"\n→ [[topics/new-products/{date}|details]]\n\n"

    md += "## Rewards\n\n"
    md += f"- {rw['headline'] or 'No data'}\n"
    md += f"- Notes: {len(rw['notes'])} items / FAQ: {len(rw['faq'])} items\n"
    md += f"\n→ [[topics/rewards/{date}|details]]\n"
    return md


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    now = datetime.now(JST)
    date = now.strftime("%Y-%m-%d")
    year = now.year

    print(f"Fetching McDonald's Japan info for {date} (JST)...")

    hs = fetch_happyset()
    print(f"  happy-set: {len(hs['current'])} current / {len(hs['next'])} next "
          f"/ {len(hs['waves'])} waves")

    news = fetch_news(year)
    print(f"  news: {len(news)} items")

    rw = fetch_rewards()
    print(f"  rewards: {len(rw['notes'])} notes / {len(rw['faq'])} faq")

    outputs = {
        REPO_ROOT / "topics" / "happy-set" / f"{date}.md": render_happyset(date, hs),
        REPO_ROOT / "topics" / "new-products" / f"{date}.md": render_news(date, year, news),
        REPO_ROOT / "topics" / "rewards" / f"{date}.md": render_rewards(date, rw),
        REPO_ROOT / "daily" / f"{date}.md": render_daily(date, hs, news, rw),
    }
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"  wrote {path.relative_to(REPO_ROOT)}")

    print("Done.")


if __name__ == "__main__":
    main()
