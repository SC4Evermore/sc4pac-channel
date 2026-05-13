#!/usr/bin/env python3
"""
SC4Evermore Coverage Report Generator

Generates a single-page HTML coverage report comparing SC4Evermore downloads
against packages covered by this sc4pac channel.

Usage:
    python scripts/scan-coverage.py

Output:
    docs/coverage-report/index.html

Requirements:
    Python 3.6+ (stdlib only — no pip installs needed)
"""

import json
import os
import urllib.request
from datetime import datetime, timezone


SC4E_API_URL        = "https://www.sc4evermore.com/latest-modified-downloads.php"
SC4E_CHANNEL_URL    = "https://sc4evermore.github.io/sc4pac-channel/json/sc4pac-channel-contents.json"
SC4PAC_CHANNEL_URL  = "https://memo33.github.io/sc4pac/channel/sc4pac-channel-contents.json"

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR   = os.path.join(REPO_ROOT, "docs", "coverage-report")
OUTPUT_FILE  = os.path.join(OUTPUT_DIR, "index.html")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def fetch_sc4e_files():
    print(f"Fetching {SC4E_API_URL} ...")
    req = urllib.request.Request(
        SC4E_API_URL,
        headers={"User-Agent": "sc4pac-coverage-scanner/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    files = data.get("files", [])
    print(f"  {len(files)} files fetched")
    return files


def fetch_channel_data(url):
    print(f"Fetching {url} ...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "sc4pac-coverage-scanner/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    pkgs = data.get("packages", [])
    print(f"  {len(pkgs)} packages in channel")
    return data


def build_version_map(channel_data):
    """Return a dict mapping SC4E file ID (str) -> version string."""
    version_map = {}
    for pkg in channel_data.get("packages", []):
        versions = pkg.get("versions", [])
        pkg_version = versions[0] if versions else ""
        for sc4e_id in pkg.get("externalIds", {}).get("sc4e", []):
            version_map[str(sc4e_id)] = pkg_version
    return version_map


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------
def h(text):
    """Minimal HTML escape."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(sc4e_files, covered_ids, channel_data, local_version_map, upstream_version_map):
    total         = len(sc4e_files)
    covered_count = sum(1 for f in sc4e_files if str(f["id"]) in covered_ids)
    missing_count = total - covered_count
    coverage_pct  = (covered_count / total * 100) if total > 0 else 0.0
    pct_str       = f"{coverage_pct:.1f}"
    generated     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    channel_pkgs  = channel_data.get("stats", {}).get("totalPackageCount", len(channel_data.get("packages", [])))

    # Sort all files by numeric ID descending (highest ID = most recently added)
    sorted_files = sorted(sc4e_files, key=lambda f: int(f["id"]), reverse=True)

    rows = []
    for f in sorted_files:
        file_id = str(f["id"])
        title = h(f.get("title", "Unknown").strip())
        alias = f.get("alias", "")
        url = h(f"https://www.sc4evermore.com/index.php/downloads/download/{file_id}-{alias}" if alias else f.get("downloadUrl", "#"))
        modified = (f.get("modified") or "")[:10]
        sc4e_version = h(f.get("release", ""))
        is_covered = file_id in covered_ids
        sc4pac_ver = h(local_version_map.get(file_id) or upstream_version_map.get(file_id, "")) if is_covered else "&mdash;"
        rows.append(
            f'<tr class="{"covered" if is_covered else "missing"}">'
            f'<td class="status-cell {"covered" if is_covered else "missing"}"></td>'
            f'<td><a href="{url}" target="_blank" rel="noopener">{title} ↗</a></td>'
            f'<td>{h(file_id)}</td>'
            f'<td>{h(modified)}</td>'
            f'<td>{sc4e_version}</td>'
            f'<td>{sc4pac_ver}</td>'
            f"</tr>"
        )

    rows_html = "\n        ".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SC4E Coverage Report</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.blue.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/sortable-base.min.css">
  <link rel="stylesheet" href="coverage.css">
</head>
<body>
  <nav>
    <ul>
      <li><h1><a href="index.html" style="text-decoration: none; color: inherit;">SC4E Channel Coverage Report</a></h1></li>
    </ul>
  </nav>
  <main>

    <h1>SC4Evermore Channel Coverage Report</h1>
    <p class="meta">Generated: {generated}</p>

    <h2>Summary</h2>
    <div class="summary-grid">
      <div class="stat-card">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Total SC4E Files</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:var(--covered-fg)">{covered_count}</div>
        <div class="stat-label">Covered by Channel</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:var(--missing-fg)">{missing_count}</div>
        <div class="stat-label">Not Yet in Channel</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{pct_str}%</div>
        <div class="stat-label">Coverage</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{channel_pkgs}</div>
        <div class="stat-label">Channel Packages</div>
      </div>
    </div>

    <h2>All SC4E Files</h2>
    <table class="striped sortable asc files-table">
      <thead>
        <tr>
          <th class="no-sort"></th>
          <th>Title</th>
          <th>ID</th>
          <th>Last Modified</th>
          <th>SC4E Version</th>
          <th>sc4pac Channel</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

  </main>
  <script src="https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/dist/sortable.min.js"></script>
  <a class="back-to-top" href="#" aria-label="Back to top">↑</a>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    sc4e_files      = fetch_sc4e_files()
    channel_data    = fetch_channel_data(SC4E_CHANNEL_URL)
    upstream_data   = fetch_channel_data(SC4PAC_CHANNEL_URL)

    local_version_map    = build_version_map(channel_data)
    upstream_version_map = build_version_map(upstream_data)
    covered_ids          = set(local_version_map.keys()) | set(upstream_version_map.keys())

    print(f"\nAnalysis:")
    print(f"  > sc4e uploaded files    : {len(sc4e_files)}")
    print(f"  > covered (sc4e channel) : {len(local_version_map)}")
    print(f"  > covered (main channel) : {len(upstream_version_map)}")
    print(f"  > covered (total)        : {len(covered_ids)}")
    print(f"  > missing packages       : {len(sc4e_files) - len(covered_ids)}")

    html = generate_report(sc4e_files, covered_ids, channel_data, local_version_map, upstream_version_map)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nReport written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
