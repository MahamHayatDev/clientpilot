import httpx
from bs4 import BeautifulSoup


def scrape_website(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (ClientPilot Research Agent)"
    }

    response = httpx.get(
        url,
        headers=headers,
        timeout=20,
        follow_redirects=True,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(
        ["script", "style", "nav", "footer", "header", "noscript"]
    ):
        element.decompose()

    text = soup.get_text(" ", strip=True)

    return text