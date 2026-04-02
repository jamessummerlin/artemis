"""Source configuration for Artemis II Mission Update Agent."""

from dataclasses import dataclass, field


@dataclass
class Sources:
    """URLs and search parameters for gathering Artemis II updates."""

    # NASA RSS feeds
    rss_feeds: dict[str, str] = field(default_factory=lambda: {
        "NASA Breaking News": "https://www.nasa.gov/news-release/feed/",
        "NASA Blogs": "https://blogs.nasa.gov/artemis/feed/",
    })

    # Pages to scrape for status updates
    scrape_pages: dict[str, str] = field(default_factory=lambda: {
        "Artemis Program": "https://www.nasa.gov/mission/artemis-ii/",
        "SLS Overview": "https://www.nasa.gov/humans-in-space/space-launch-system/",
        "Orion Spacecraft": "https://www.nasa.gov/humans-in-space/orion-spacecraft/",
        "ESA Artemis": "https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Orion",
        "CSA Artemis": "https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/artemis-missions.asp",
    })

    # arXiv search queries
    arxiv_queries: list[str] = field(default_factory=lambda: [
        "Artemis II",
        "Orion spacecraft lunar",
        "Space Launch System SLS",
    ])

    # Keywords to filter relevant content from RSS/scraped pages
    relevance_keywords: list[str] = field(default_factory=lambda: [
        "artemis",
        "orion",
        "sls",
        "space launch system",
        "lunar",
        "moon",
        "gateway",
        "wiseman",
        "glover",
        "koch",
        "hansen",
    ])
