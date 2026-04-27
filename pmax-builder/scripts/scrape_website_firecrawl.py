#!/usr/bin/env python3
"""Scrape a business website using Firecrawl.

Fetches the homepage, then maps the site and tries to pull additional
context pages (services, about, amenities, etc.) that help when building
ad copy, extracting addresses, or enriching campaign context.

Usage:
    python scrape_website_firecrawl.py --url https://example.com
    python scrape_website_firecrawl.py --url https://example.com --output scrape.json
    python scrape_website_firecrawl.py --url https://example.com \
        --extra-keywords amenities,features,menu

Prerequisites:
    - FIRECRAWL_API_KEY environment variable (set in .env or shell)
      Get a key at firecrawl.dev
    - pip install firecrawl-py python-dotenv
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# Default keyword buckets to look for when mapping a site.
# Each tuple is (bucket_name, keywords_to_match_in_url).
DEFAULT_PAGE_KEYWORDS = [
    ('services', ['services', 'service', 'repairs', 'repair']),
    ('about', ['about', 'about-us', 'company', 'who-we-are']),
    ('amenities', ['amenities', 'features', 'features-and-amenities']),
    ('floor_plans', ['floor-plan', 'floorplan', 'floor-plans', 'floorplans']),
    ('contact', ['contact', 'contact-us', 'get-in-touch']),
]


def _get_firecrawl_app():
    """Initialize a Firecrawl client from FIRECRAWL_API_KEY."""
    try:
        from firecrawl import Firecrawl
    except ImportError:
        raise ValueError(
            "firecrawl package not installed. Run: pip install firecrawl-py"
        )

    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY environment variable not set. "
            "Add it to a .env file at project root, or export it as an env var."
        )
    return Firecrawl(api_key=api_key)


def _extract_markdown(scrape_result) -> Optional[str]:
    """Handle both dict and object return shapes from Firecrawl."""
    md = getattr(scrape_result, 'markdown', None)
    if md:
        return md
    if isinstance(scrape_result, dict):
        return scrape_result.get('markdown')
    return None


def _extract_metadata(scrape_result) -> Dict[str, Any]:
    meta = getattr(scrape_result, 'metadata', None)
    if meta:
        return meta if isinstance(meta, dict) else getattr(meta, '__dict__', {})
    if isinstance(scrape_result, dict):
        return scrape_result.get('metadata', {}) or {}
    return {}


def _extract_links(map_result) -> List[str]:
    """Pull URL strings out of a Firecrawl map response."""
    links = getattr(map_result, 'links', None)
    if links is None and isinstance(map_result, dict):
        links = map_result.get('links')
    if links is None and isinstance(map_result, list):
        links = map_result

    urls: List[str] = []
    for link in links or []:
        if isinstance(link, str):
            urls.append(link)
        elif hasattr(link, 'url'):
            urls.append(link.url)
        elif isinstance(link, dict):
            u = link.get('url', '')
            if u:
                urls.append(u)
    return urls


def scrape_website(url: str, extra_page_keywords: Optional[List[tuple]] = None) -> Dict[str, Any]:
    """Scrape a website's homepage plus any matching context pages.

    Args:
        url: Website URL to scrape
        extra_page_keywords: Optional list of (bucket_name, [keywords]) tuples
                             to look for when mapping the site. If None, uses
                             DEFAULT_PAGE_KEYWORDS.

    Returns:
        dict with:
            content      - homepage markdown
            metadata     - page metadata (title, description, etc.)
            url          - original URL
            extra_pages  - {bucket_name: {"url": ..., "content": ...}} for each
                           additional page found and scraped
    """
    app = _get_firecrawl_app()

    logger.info(f"Scraping homepage: {url}")
    scrape_result = app.scrape(url, formats=['markdown'])

    markdown = _extract_markdown(scrape_result)
    if not markdown:
        raise ValueError("Firecrawl returned empty content for homepage")

    result: Dict[str, Any] = {
        'url': url,
        'content': markdown,
        'metadata': _extract_metadata(scrape_result),
        'extra_pages': {},
    }

    buckets = extra_page_keywords if extra_page_keywords is not None else DEFAULT_PAGE_KEYWORDS

    # Map the site to find additional context pages
    try:
        logger.info(f"Mapping site to find context pages...")
        map_result = app.map(url=url)
        site_urls = _extract_links(map_result)
        logger.info(f"Found {len(site_urls)} URLs on site")

        for bucket_name, keywords in buckets:
            chosen_url: Optional[str] = None
            for site_url in site_urls:
                url_lower = site_url.lower()
                for keyword in keywords:
                    if f'/{keyword}' in url_lower or url_lower.endswith(f'/{keyword}'):
                        chosen_url = site_url
                        break
                if chosen_url:
                    break

            if chosen_url and chosen_url != url:
                logger.info(f"  Scraping {bucket_name} page: {chosen_url}")
                try:
                    extra_scrape = app.scrape(chosen_url, formats=['markdown'])
                    extra_md = _extract_markdown(extra_scrape)
                    if extra_md:
                        result['extra_pages'][bucket_name] = {
                            'url': chosen_url,
                            'content': extra_md,
                        }
                except Exception as e:
                    logger.warning(f"  Failed to scrape {chosen_url}: {e}")

    except Exception as e:
        logger.warning(f"Could not map/scrape additional pages: {e}")

    return result


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Scrape a business website with Firecrawl')
    parser.add_argument('--url', required=True, help='Website URL to scrape')
    parser.add_argument('--output', help='Write full scrape result as JSON to this path')
    parser.add_argument('--extra-keywords',
                        help='Comma-separated keywords to look for in site URLs (e.g. '
                             '"menu,locations,hours"). Pages matching any of these will '
                             'be scraped alongside the homepage.')
    args = parser.parse_args()

    extra_keywords = None
    if args.extra_keywords:
        kw_list = [k.strip() for k in args.extra_keywords.split(',') if k.strip()]
        extra_keywords = [('custom', kw_list)] + DEFAULT_PAGE_KEYWORDS

    try:
        print(f"\n{'='*80}")
        print(f"SCRAPING: {args.url}")
        print(f"{'='*80}\n")

        result = scrape_website(args.url, extra_page_keywords=extra_keywords)

        print(f"\n{'='*80}")
        print("SCRAPE RESULTS")
        print(f"{'='*80}")
        print(f"Homepage:        {len(result['content'])} characters")
        for bucket, data in result['extra_pages'].items():
            print(f"{bucket:16s} {data['url']} ({len(data['content'])} chars)")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nFull result written to: {args.output}")
        else:
            print("\nHomepage preview (first 1500 chars):")
            print("-" * 80)
            print(result['content'][:1500])
            print("-" * 80)
            print("\nPass --output PATH to save the full JSON (including extra pages).")

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
