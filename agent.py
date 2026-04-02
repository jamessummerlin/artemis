#!/usr/bin/env python3
"""Artemis II Mission Update Agent.

Collects updates from NASA, ESA, CSA, and arXiv, then generates
a markdown report in the reports/ directory.
"""

import datetime
import re
import sys
from pathlib import Path

import arxiv
import feedparser
import requests
from bs4 import BeautifulSoup

from sources import Sources

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "report_template.md"
REPORTS_DIR = SCRIPT_DIR / "reports"
REQUEST_TIMEOUT = 15
HEADERS = {"User-Agent": "ArtemisII-UpdateAgent/1.0"}


def fetch_rss_entries(sources: Sources, days_back: int = 7) -> list[dict]:
    """Fetch recent Artemis-related entries from NASA RSS feeds."""
    cutoff = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=days_back)
    entries = []

    for feed_name, url in sources.rss_feeds.items():
        print(f"  Fetching RSS: {feed_name}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published = entry.get("published_parsed")
                if published:
                    pub_dt = datetime.datetime(*published[:6], tzinfo=datetime.timezone.utc)
                    if pub_dt < cutoff:
                        continue

                title = entry.get("title", "")
                summary = entry.get("summary", "")
                text = f"{title} {summary}".lower()

                if any(kw in text for kw in sources.relevance_keywords):
                    entries.append({
                        "source": feed_name,
                        "title": title,
                        "url": entry.get("link", ""),
                        "date": pub_dt.strftime("%Y-%m-%d"),
                        "summary": BeautifulSoup(summary, "html.parser").get_text()[:300],
                    })
        except Exception as e:
            print(f"    Warning: failed to fetch {feed_name}: {e}")

    return entries


def scrape_page_text(url: str) -> str:
    """Fetch a page and return its visible text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"    Warning: failed to scrape {url}: {e}")
        return ""


def extract_status_snippets(sources: Sources) -> dict[str, list[str]]:
    """Scrape status pages and extract Artemis-relevant sentences."""
    snippets: dict[str, list[str]] = {}

    for name, url in sources.scrape_pages.items():
        print(f"  Scraping: {name}")
        text = scrape_page_text(url)
        if not text:
            continue

        sentences = re.split(r'(?<=[.!?])\s+', text)
        relevant = []
        noise_patterns = ["Read Story", "View Image", "Play Video", "Play Story",
                          "Focus on", "More items", "min read", "Top of page"]
        for s in sentences:
            s_lower = s.lower()
            if any(kw in s_lower for kw in sources.relevance_keywords):
                cleaned = s.strip()[:500]
                if len(cleaned) > 40 and not any(n in cleaned for n in noise_patterns):
                    relevant.append(cleaned)

        if relevant:
            snippets[name] = relevant[:5]

    return snippets


def search_arxiv(sources: Sources, max_results: int = 5) -> list[dict]:
    """Search arXiv for recent Artemis II related papers."""
    papers = []
    seen_ids = set()

    for query in sources.arxiv_queries:
        print(f"  arXiv search: {query}")
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )
            client = arxiv.Client()
            for result in client.results(search):
                if result.entry_id in seen_ids:
                    continue
                # Filter: title or abstract must mention an Artemis keyword
                combined = f"{result.title} {result.summary}".lower()
                if not any(kw in combined for kw in sources.relevance_keywords):
                    continue
                seen_ids.add(result.entry_id)
                papers.append({
                    "title": result.title,
                    "authors": ", ".join(a.name for a in result.authors[:3])
                              + ("..." if len(result.authors) > 3 else ""),
                    "url": result.entry_id,
                    "published": result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary[:200],
                })
        except Exception as e:
            print(f"    Warning: arXiv search failed for '{query}': {e}")

    return papers


def format_bullet_list(items: list[str], prefix: str = "- ") -> str:
    if not items:
        return "- No updates found this cycle."
    return "\n".join(f"{prefix}{item}" for item in items)


def build_report(
    rss_entries: list[dict],
    snippets: dict[str, list[str]],
    papers: list[dict],
    sources: Sources,
) -> str:
    """Fill in the report template with collected data."""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")

    # --- Summary ---
    total = len(rss_entries) + sum(len(v) for v in snippets.values()) + len(papers)
    summary = (
        f"Collected {total} relevant items across NASA feeds, agency pages, and arXiv. "
        f"Found {len(rss_entries)} RSS entries, scraped {len(snippets)} pages with relevant content, "
        f"and identified {len(papers)} recent academic papers."
    )

    # --- NASA Updates ---
    nasa_lines = []
    for e in rss_entries:
        nasa_lines.append(f"[{e['title']}]({e['url']}) ({e['date']}) — {e['summary'][:120]}")
    nasa_section = format_bullet_list(nasa_lines)

    # --- Technical & Engineering ---
    tech_lines = []
    for name in ["SLS Overview", "Orion Spacecraft"]:
        if name in snippets:
            for s in snippets[name][:3]:
                tech_lines.append(f"**{name}:** {s}")
    tech_section = format_bullet_list(tech_lines)

    # --- Science ---
    science_lines = []
    for name in ["Artemis Program"]:
        if name in snippets:
            for s in snippets[name][:3]:
                science_lines.append(s)
    science_section = format_bullet_list(science_lines)

    # --- Crew ---
    crew_keywords = ["wiseman", "glover", "koch", "hansen", "crew"]
    crew_lines = []
    for e in rss_entries:
        if any(kw in e["title"].lower() or kw in e["summary"].lower() for kw in crew_keywords):
            crew_lines.append(f"[{e['title']}]({e['url']})")
    for name, slist in snippets.items():
        for s in slist:
            if any(kw in s.lower() for kw in crew_keywords):
                crew_lines.append(s)
    crew_section = format_bullet_list(crew_lines[:5])

    # --- International Partners ---
    partner_lines = []
    for name in ["ESA Artemis", "CSA Artemis"]:
        if name in snippets:
            for s in snippets[name][:3]:
                partner_lines.append(f"**{name}:** {s}")
    partner_section = format_bullet_list(partner_lines)

    # --- Papers ---
    if papers:
        paper_lines = []
        for p in papers:
            paper_lines.append(
                f"- **Title:** {p['title']}\n"
                f"  - **Authors:** {p['authors']}\n"
                f"  - **Source:** [arXiv]({p['url']})\n"
                f"  - **Relevance:** {p['summary'][:150]}"
            )
        papers_section = "\n".join(paper_lines)
    else:
        papers_section = "- No recent papers found this cycle."

    # --- Sources list ---
    all_urls = []
    for e in rss_entries:
        all_urls.append(e["url"])
    for url in sources.scrape_pages.values():
        all_urls.append(url)
    for p in papers:
        all_urls.append(p["url"])
    sources_section = "\n".join(f"{i+1}. {url}" for i, url in enumerate(all_urls))

    # --- Build report ---
    report = f"""# Artemis II Mission Update — {date_str}

## Summary
{summary}

## Mission Status
- **Current Phase:** See official NASA updates below
- **Target Launch Date:** See latest NASA announcements
- **Notable Changes:** See key updates below

## Key Updates

### Official NASA Updates
{nasa_section}

### Technical & Engineering
{tech_section}

### Science & Instruments
{science_section}

### Crew Updates
{crew_section}

### International Partners
{partner_section}

## Academic & Research Papers
{papers_section}

## Upcoming Milestones
- Check NASA Artemis blog for the latest timeline updates.

## Sources
{sources_section}
"""
    return report


def main():
    sources = Sources()
    print("Artemis II Mission Update Agent")
    print("=" * 40)

    print("\n[1/3] Fetching RSS feeds...")
    rss_entries = fetch_rss_entries(sources)

    print("\n[2/3] Scraping status pages...")
    snippets = extract_status_snippets(sources)

    print("\n[3/3] Searching arXiv...")
    papers = search_arxiv(sources)

    print("\nGenerating report...")
    report = build_report(rss_entries, snippets, papers, sources)

    REPORTS_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d_%H") + ".md"
    output_path = REPORTS_DIR / filename
    output_path.write_text(report)

    print(f"\nReport saved to: {output_path}")
    print(f"  RSS entries:  {len(rss_entries)}")
    print(f"  Pages scraped: {len(snippets)}")
    print(f"  arXiv papers: {len(papers)}")


if __name__ == "__main__":
    main()
