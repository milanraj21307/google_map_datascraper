import re
from .scraper import scrape_website
from .validator import validate


def clean_address(text):
    """
    Cleans scraped address text and removes footer/nav junk.
    Returns None if address is unreliable.
    """
    if not text:
        return None

    t = text.strip()

    # Fix common encoding issues
    t = (
        t.replace("Â", "")
         .replace("â€“", "-")
         .replace("â€™", "'")
         .replace("â€œ", '"')
         .replace("â€�", '"')
    )

    # Remove obvious footer / navigation junk
    junk_keywords = [
        "copyright", "©", "terms", "privacy", "policy",
        "careers", "about", "search", "login",
        "monday", "friday", "support", "opening hours",
        "disclaimer", "all rights reserved"
    ]

    if any(word in t.lower() for word in junk_keywords):
        return None

    # Must contain numbers (street number / unit)
    if not re.search(r"\d+", t):
        return None

    # Reasonable length check
    if len(t) < 8 or len(t) > 200:
        return None

    return t


def process_company(company):
    # ❌ Skip already processed companies
    if company.processed:
        return

    company.processing_status = "processing"

    try:
        if company.website:
            scraped = scrape_website(company.website)

            company.email = scraped.get("email")

            # ✅ CLEAN ADDRESS HERE
            company.address = clean_address(scraped.get("address"))

            company.ceo = scraped.get("ceo_owner", "UNKNOWN")
            company.ceo_source = scraped.get("ceo_source")

        validate(company)

        company.processed = True
        company.processing_status = "done"

    except Exception:
        company.processing_status = "error"
