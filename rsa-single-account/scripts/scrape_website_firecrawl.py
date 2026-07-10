#!/usr/bin/env python3
"""
Scrape Business Website via Firecrawl (Step 5 of the rsa-single-account skill)

Scrapes the client's website (homepage + services/about pages if found) and
extracts VERIFIED business facts with an LLM: services, credentials,
features, history, and specializations. Every RSA claim must trace back to
this output (or a verified review) — if the scrape fails, generation STOPS;
there is no generic fallback.

Usage:
    python scrape_website_firecrawl.py <website_url>
    python scrape_website_firecrawl.py <website_url> --output website_data.json

Prerequisites:
    - FIRECRAWL_API_KEY environment variable — get a key at firecrawl.dev
    - ANTHROPIC_API_KEY environment variable — for the structured extraction
      (both can live in a .env file at project root)
    - pip install firecrawl-py anthropic python-dotenv
"""

import argparse
import io
import json
import logging
import os
import sys
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Windows console encoding fix
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def _load_dotenv_if_available():
    """Pick up API keys from a .env file at project root, if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _fc_field(obj, field, default=None):
    """Read a field from a Firecrawl result that may be a Document/MapData object
    (firecrawl-py v1/v2, attribute access) or a dict (legacy SDK)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def scrape_business_website(url: str) -> Dict[str, Any]:
    """
    Scrape a business website using the Firecrawl API.

    Args:
        url: Business website URL

    Returns:
        Dict with:
        - content: Full markdown content
        - services_content: Content from services page (if found)
        - about_content: Content from about page (if found)
    """
    try:
        from firecrawl import Firecrawl

        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set. "
                             "Add it to a .env file at project root or export it.")

        app = Firecrawl(api_key=api_key)

        # Scrape homepage
        logger.info(f"Scraping homepage: {url}")
        scrape_result = app.scrape(url, formats=['markdown'])

        homepage_markdown = _fc_field(scrape_result, 'markdown')
        if not scrape_result or not homepage_markdown:
            raise ValueError("Firecrawl returned empty content")

        result = {
            'content': homepage_markdown,
            'metadata': _fc_field(scrape_result, 'metadata', {}),
            'services_content': None,
            'services_url': None,
            'about_content': None,
            'about_url': None
        }

        # Try to find and scrape services and about pages
        try:
            logger.info(f"Mapping site to find services/about pages...")
            map_result = app.map(url=url)

            site_urls = []
            # Firecrawl v1/v2 returns a MapData object (.links); legacy returned a dict/list
            links_raw = _fc_field(map_result, 'links', None)
            if links_raw is None and isinstance(map_result, list):
                links_raw = map_result
            for link in (links_raw or []):
                if isinstance(link, str):
                    site_urls.append(link)
                elif isinstance(link, dict):
                    site_urls.append(link.get('url', ''))
                else:  # LinkResult object (attribute access)
                    site_urls.append(getattr(link, 'url', '') or '')

            logger.info(f"Found {len(site_urls)} URLs on site")

            # Find services page
            services_keywords = ['services', 'service', 'repairs', 'repair']
            for site_url in site_urls:
                url_lower = site_url.lower()
                for keyword in services_keywords:
                    if f'/{keyword}' in url_lower or url_lower.endswith(f'/{keyword}'):
                        result['services_url'] = site_url
                        logger.info(f"Found services page: {site_url}")
                        break
                if result['services_url']:
                    break

            # Find about page
            about_keywords = ['about', 'about-us', 'company', 'who-we-are']
            for site_url in site_urls:
                url_lower = site_url.lower()
                for keyword in about_keywords:
                    if f'/{keyword}' in url_lower or url_lower.endswith(f'/{keyword}'):
                        result['about_url'] = site_url
                        logger.info(f"Found about page: {site_url}")
                        break
                if result['about_url']:
                    break

            # Scrape services page if found
            if result['services_url'] and result['services_url'] != url:
                logger.info(f"Scraping services page: {result['services_url']}")
                services_scrape = app.scrape(result['services_url'], formats=['markdown'])
                services_markdown = _fc_field(services_scrape, 'markdown')
                if services_markdown:
                    result['services_content'] = services_markdown
                    logger.info(f"Successfully scraped services page")

            # Scrape about page if found
            if result['about_url'] and result['about_url'] != url:
                logger.info(f"Scraping about page: {result['about_url']}")
                about_scrape = app.scrape(result['about_url'], formats=['markdown'])
                about_markdown = _fc_field(about_scrape, 'markdown')
                if about_markdown:
                    result['about_content'] = about_markdown
                    logger.info(f"Successfully scraped about page")

        except Exception as e:
            logger.warning(f"Could not map/scrape additional pages: {e}")

        return result

    except ImportError:
        raise ValueError("firecrawl package not installed. Run: pip install firecrawl-py")
    except Exception as e:
        logger.error(f"Error scraping website: {e}")
        raise


def extract_business_features(website_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract business features from scraped website data using an LLM.

    Args:
        website_data: Dict from scrape_business_website()

    Returns:
        Dict with:
        - services: List of services offered
        - credentials: List of certifications/credentials
        - features: List of business features (hours, conveniences, etc.)
        - history: Years in business, family-owned status, etc.
        - specializations: Brands, niches, customer types, etc.
    """
    try:
        import anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set. "
                             "Add it to a .env file at project root or export it.")

        client = anthropic.Anthropic(api_key=api_key)

        # Combine all scraped content
        content_parts = [website_data['content']]
        if website_data.get('services_content'):
            content_parts.append("\n\n=== SERVICES PAGE ===\n" + website_data['services_content'])
        if website_data.get('about_content'):
            content_parts.append("\n\n=== ABOUT PAGE ===\n" + website_data['about_content'])

        combined_content = "\n".join(content_parts)

        # Truncate to avoid token limits (keep first 10000 chars)
        content_snippet = combined_content[:10000]

        prompt = f"""Analyze this local service business website and extract the following information:

1. SERVICES OFFERED:
   - List all services mentioned
   - Examples: Oil Changes, Brake Repair, Drain Cleaning, Apartment Tours — whatever this business offers
   - Return up to 20 services
   - Use title case (e.g., "Brake Repair" not "brake repair")

2. CREDENTIALS & CERTIFICATIONS:
   - Examples: ASE Certified, BBB Accredited, State Licensed, Award-Winning, etc.
   - Include any professional affiliations or awards
   - Use exact wording from website when possible

3. BUSINESS FEATURES:
   - Examples: Free shuttle, Same day service, Open Saturdays, Free wifi, Online booking, etc.
   - Include hours/schedule information
   - Include convenience features
   - Use descriptive phrases (max 25 characters each)

4. BUSINESS HISTORY:
   - Years in business / established year
   - Family-owned status
   - Owner names (if mentioned)
   - Any notable history

5. SPECIALIZATIONS:
   - Customer or product niches the business focuses on
   - Specific brands or equipment they work with
   - Special capabilities (e.g., Diesel Repair, Electric Vehicles, Fleet Service, Luxury Units)

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks, no explanation).
Only include facts that appear in the website content — never invent or assume.

{{
  "services": ["Oil Changes", "Brake Repair", "Transmission Repair"],
  "credentials": ["ASE Certified Technicians", "BBB Accredited Business"],
  "features": ["Free Shuttle Service", "Same Day Service", "Open Saturdays"],
  "history": {{
    "established_year": 1986,
    "years_in_business": 38,
    "family_owned": true,
    "notes": "Family owned and operated since 1986"
  }},
  "specializations": ["Domestic Vehicles", "Foreign Vehicles", "Diesel Repair"]
}}

Website content:
{content_snippet}"""

        logger.info("Extracting business features with an LLM...")

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Clean up markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text
            response_text = response_text.rsplit("```", 1)[0] if "```" in response_text else response_text
            response_text = response_text.strip()

        # Parse JSON
        features = json.loads(response_text)

        logger.info(f"Extracted {len(features.get('services', []))} services, "
                   f"{len(features.get('credentials', []))} credentials, "
                   f"{len(features.get('features', []))} features")

        return features

    except ImportError:
        raise ValueError("anthropic package not installed. Run: pip install anthropic")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"Response was: {response_text[:500]}")
        raise ValueError(f"Invalid JSON response from AI: {e}")
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        raise


def main():
    _load_dotenv_if_available()

    parser = argparse.ArgumentParser(
        description='Scrape a business website and extract verified facts for RSA generation'
    )
    parser.add_argument('website_url', help='Website URL to scrape')
    parser.add_argument('--output',
                        help='Write extracted features as JSON to this path '
                             '(cache it — scrape once per account, reuse across ad groups)')
    args = parser.parse_args()

    website_url = args.website_url

    try:
        # Scrape website
        print(f"\n{'='*80}")
        print(f"SCRAPING BUSINESS WEBSITE: {website_url}")
        print(f"{'='*80}\n")

        website_data = scrape_business_website(website_url)

        print(f"\n{'='*80}")
        print("SCRAPE RESULTS")
        print(f"{'='*80}")
        print(f"Homepage scraped: yes")
        print(f"Services page found: {'yes' if website_data.get('services_url') else 'no'}")
        print(f"About page found: {'yes' if website_data.get('about_url') else 'no'}")

        # Extract features
        print(f"\n{'='*80}")
        print("EXTRACTING FEATURES WITH AI")
        print(f"{'='*80}\n")

        features = extract_business_features(website_data)

        # Print results
        print(f"\n{'='*80}")
        print("BUSINESS FEATURES EXTRACTED")
        print(f"{'='*80}\n")

        print(f"SERVICES ({len(features.get('services', []))}):")
        for service in features.get('services', []):
            print(f"  - {service}")

        print(f"\nCREDENTIALS ({len(features.get('credentials', []))}):")
        for cred in features.get('credentials', []):
            print(f"  - {cred}")

        print(f"\nFEATURES ({len(features.get('features', []))}):")
        for feature in features.get('features', []):
            print(f"  - {feature}")

        print(f"\nHISTORY:")
        history = features.get('history', {})
        if history.get('established_year'):
            print(f"  - Established: {history['established_year']}")
        if history.get('years_in_business'):
            print(f"  - Years in business: {history['years_in_business']}")
        if history.get('family_owned'):
            print(f"  - Family owned: Yes")
        if history.get('notes'):
            print(f"  - Notes: {history['notes']}")

        print(f"\nSPECIALIZATIONS ({len(features.get('specializations', []))}):")
        for spec in features.get('specializations', []):
            print(f"  - {spec}")

        print(f"\n{'='*80}\n")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(features, f, indent=2, ensure_ascii=False)
            print(f"Features written to: {args.output}")

        # Output as JSON for programmatic use
        print("JSON OUTPUT:")
        print(json.dumps(features, indent=2))

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
