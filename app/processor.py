from .scraper import scrape_website
from .validator import validate

def process_company(company):
    # ❌ Skip already processed companies
    if company.processed:
        return

    company.processing_status = "processing"

    try:
        if company.website:
            scraped = scrape_website(company.website)

            company.email = scraped.get("email")
            company.address = scraped.get("address")
            company.ceo = scraped.get("ceo_owner", "UNKNOWN")
            company.ceo_source = scraped.get("ceo_source")

        validate(company)

        company.processed = True
        company.processing_status = "done"

    except Exception:
        company.processing_status = "error"
