import requests
import re
from bs4 import BeautifulSoup

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def scrape_website(url: str):
    result = {
        "email": None,
        "address": None,
        "ceo_owner": "UNKNOWN",
        "ceo_source": None
    }

    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ")

        emails = re.findall(EMAIL_REGEX, text)
        if emails:
            result["email"] = emails[0]

        footer = soup.find("footer")
        if footer:
            result["address"] = footer.get_text(strip=True)[:200]

    except Exception:
        pass

    return result
