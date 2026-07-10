#!/usr/bin/env python3
"""
Get Google Business Profile Reviews via SERP API (Step 6 of the rsa-single-account skill)

Extracts GBP reviews for a business using SERP API local results.
Used as fallback when the website doesn't have sufficient reviews for RSA
social proof headlines. Reviews come from the website or GBP only — never
assumed.

Usage:
    python get_gmb_reviews.py "<business_name>" [location]

Example:
    python get_gmb_reviews.py "Example Auto Repair" "Austin TX"
    python get_gmb_reviews.py "Example Flats" "Springfield IL" --apartment

Prerequisites:
    - SERP_API_KEY environment variable (set in .env or shell)
      Get a key at serpapi.com
    - pip install google-search-results python-dotenv
"""

import sys
import io
import json
import os
from serpapi import GoogleSearch

# Windows console encoding fix
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def get_serpapi_key():
    """SERP API key from the SERP_API_KEY environment variable (.env supported)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.environ.get('SERP_API_KEY')
    if not api_key:
        print("Error: SERP_API_KEY environment variable not set.")
        print("Get a key at serpapi.com, then add SERP_API_KEY to a .env file "
              "at project root or export it in your shell.")
        return None
    return api_key


def get_gmb_reviews(business_name, location=None):
    """
    Get Google Business Profile reviews via SERP API.

    Args:
        business_name (str): Name of business to search for
        location (str, optional): Location to search in (e.g., "Austin TX")

    Returns:
        dict: Dictionary with rating, review count, and review snippets
    """
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

    api_key = get_serpapi_key()
    if not api_key:
        return None

    # Build query
    query = f"{business_name}"
    if location:
        query += f" {location}"

    print(f"Searching for: {query}")

    # SERP API parameters
    params = {
        "q": query,
        "location": location or "United States",
        "api_key": api_key,
        "engine": "google"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Extract local results (Google Business Profile panel)
        local_results = results.get("local_results", {})

        if not local_results:
            print(f"[WARNING] No local results found for {business_name}")
            return {
                "rating": None,
                "reviews_count": None,
                "review_snippets": []
            }

        # Get rating and review count
        rating = local_results.get("rating")
        reviews_count = local_results.get("reviews")

        print(f"\nBusiness Found:")
        print(f"  Name: {local_results.get('title', 'N/A')}")
        print(f"  Rating: {rating} stars")
        print(f"  Reviews: {reviews_count}")

        # Extract review snippets if available
        review_snippets = []
        if "reviews_results" in local_results:
            print(f"\nExtracted Reviews:")
            for i, review in enumerate(local_results["reviews_results"][:5], 1):  # Top 5
                snippet = review.get("snippet", "")
                review_rating = review.get("rating", rating)
                review_date = review.get("date", "")

                review_snippets.append({
                    "text": snippet,
                    "rating": review_rating,
                    "date": review_date
                })

                # Safely encode snippet for printing
                safe_snippet = snippet[:80].encode('ascii', errors='replace').decode('ascii')
                print(f"  {i}. ({review_rating} stars) {safe_snippet}...")

        return {
            "rating": rating,
            "reviews_count": reviews_count,
            "review_snippets": review_snippets
        }

    except Exception as e:
        print(f"Error querying SERP API: {e}")
        return None


def format_for_rsa(gmb_data, property_type="business"):
    """
    Format GBP data for RSA social proof headlines.

    Args:
        gmb_data (dict): GBP review data
        property_type (str): "apartment" for resident attribution, "business" for customer

    Returns:
        dict: Formatted data for RSA generation
    """
    if not gmb_data or not gmb_data.get("rating"):
        return {
            "social_proof_headlines": [],
            "reviews_available": False,
            "rating": None,
            "reviews_count": None
        }

    rating = gmb_data["rating"]
    reviews_count = gmb_data["reviews_count"]
    review_snippets = gmb_data["review_snippets"]

    # Attribution based on property type
    attribution = "Resident" if property_type == "apartment" else "Customer"

    # Generate social proof headline options
    social_proof_headlines = []

    # Rating threshold: Only use rating headline if >= 4.5
    RATING_THRESHOLD = 4.5

    # Option 1: Rating + Count (only if rating >= 4.5)
    if rating and reviews_count and rating >= RATING_THRESHOLD:
        if reviews_count >= 1000:
            count_formatted = f"{reviews_count // 1000}000+"
        elif reviews_count >= 100:
            count_formatted = f"{reviews_count}+"
        else:
            count_formatted = f"{reviews_count}+"

        # Try different formats to fit 30 chars
        headline_options = [
            f"{rating}★ From {count_formatted} {attribution}s",
            f"Rated {rating}★ | {count_formatted} Reviews",
            f"{rating}★ Rating | {count_formatted}+ Reviews",
        ]

        for headline in headline_options:
            if len(headline) <= 30:
                social_proof_headlines.append({
                    "text": headline,
                    "type": "rating_count",
                    "verified": True
                })
                break

    # Option 2: Review snippets from 5-star reviews only
    # Filter for 5-star reviews
    five_star_reviews = [s for s in review_snippets if s.get("rating") == 5]

    # Fall back to all reviews if no 5-star available
    snippets_to_use = five_star_reviews if five_star_reviews else review_snippets

    for snippet_data in snippets_to_use[:3]:
        snippet = snippet_data["text"]
        # Extract key phrases (first sentence or up to 20 chars)
        if len(snippet) < 22:  # Leave room for quotes and attribution
            short_snippet = snippet
        else:
            # Try to get first sentence
            first_sentence = snippet.split('.')[0]
            if len(first_sentence) < 22:
                short_snippet = first_sentence
            else:
                # Take first ~18 chars and find word boundary
                short_snippet = snippet[:18].rsplit(' ', 1)[0].strip()

        headline = f'"{short_snippet}" - {attribution}'
        if len(headline) <= 30:
            social_proof_headlines.append({
                "text": headline,
                "type": "review_snippet",
                "verified": True,
                "original_rating": snippet_data.get("rating")
            })

    return {
        "social_proof_headlines": social_proof_headlines[:2],  # Return top 2
        "reviews_available": len(social_proof_headlines) > 0,
        "rating": rating,
        "reviews_count": reviews_count,
        "rating_meets_threshold": rating >= RATING_THRESHOLD if rating else False
    }


def get_apartment_social_proof(property_name, city, state):
    """
    Convenience function for apartment properties.

    Args:
        property_name (str): Name of apartment complex (e.g., "Example Flats")
        city (str): City name (e.g., "Springfield")
        state (str): State abbreviation (e.g., "IL")

    Returns:
        dict: Social proof data formatted for RSA generation
    """
    location = f"{city}, {state}"
    gmb_data = get_gmb_reviews(property_name, location)

    if not gmb_data:
        return {
            "social_proof_headlines": [],
            "reviews_available": False,
            "rating": None,
            "reviews_count": None,
            "lookup_failed": True
        }

    result = format_for_rsa(gmb_data, property_type="apartment")
    result["lookup_failed"] = False
    result["search_query"] = f"{property_name} {location}"
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Get Google Business Profile reviews for RSA social proof headlines"
    )
    parser.add_argument("business_name", help="Name of business to search for")
    parser.add_argument("location", nargs="?", help="Location (e.g., 'Austin TX')")
    parser.add_argument(
        "--apartment", "-a",
        action="store_true",
        help="Use apartment-specific formatting (Resident attribution, 4.5 threshold)"
    )

    args = parser.parse_args()

    # Get GBP reviews
    gmb_data = get_gmb_reviews(args.business_name, args.location)

    if gmb_data:
        # Format for RSA
        property_type = "apartment" if args.apartment else "business"
        rsa_formatted = format_for_rsa(gmb_data, property_type=property_type)

        print(f"\n{'='*60}")
        print(f"RSA Social Proof Headlines ({property_type.title()} Mode):")
        print('='*60)

        if rsa_formatted.get("rating"):
            threshold_status = "meets" if rsa_formatted.get("rating_meets_threshold") else "below"
            print(f"Rating: {rsa_formatted['rating']}★ ({threshold_status} 4.5 threshold)")
            print(f"Reviews: {rsa_formatted['reviews_count']}")

        print(f"\nGenerated Headlines:")
        for i, headline in enumerate(rsa_formatted["social_proof_headlines"], 1):
            headline_type = headline.get("type", "unknown")
            print(f"  {i}. {headline['text']} ({len(headline['text'])} chars) [{headline_type}]")

        if rsa_formatted["social_proof_headlines"]:
            print(f"\n[OK] Found {len(rsa_formatted['social_proof_headlines'])} usable social proof headlines")
        else:
            print(f"\n[WARNING] No usable headlines (rating below 4.5 and no short review quotes)")
    else:
        print("\n[ERROR] Failed to retrieve GBP reviews")
        sys.exit(1)


if __name__ == "__main__":
    main()
