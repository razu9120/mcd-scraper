---
name: fetch-all-mcd
description: Fetch the latest McDonald's Japan info (Happy Set, New Products, Rewards) and generate Obsidian notes
disable-model-invocation: true
allowed-tools: Bash(python3 *) Bash(git *)
---

# fetch-all-mcd

Fetch the latest McDonald's Japan information (Happy Set, New Products, Rewards)
and generate Obsidian notes — the same process GitHub Actions runs daily, for
local manual execution and debugging.

## Steps

1. Run the fetch script from the repository root:

   ```bash
   python3 scripts/fetch_mcd.py
   ```

   This generates/overwrites:
   - `topics/happy-set/YYYY-MM-DD.md`
   - `topics/new-products/YYYY-MM-DD.md`
   - `topics/rewards/YYYY-MM-DD.md`
   - `daily/YYYY-MM-DD.md`

2. Verify the script printed item counts for all three topics (a count of 0
   may indicate the page structure changed — inspect before committing).

3. Commit and push:

   ```bash
   git add daily topics
   git commit -m "auto: fetch mcd-scraper $(TZ=Asia/Tokyo date +%Y-%m-%d)"
   git push
   ```

## Notes

- Uses only the Python standard library — no installs, no API keys.
- Existing notes for the same date are overwritten.
- All dates are JST (Asia/Tokyo).
