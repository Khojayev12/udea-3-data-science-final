import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

BASE_URL = "https://tashkent.hh.uz"
SEARCH_URL = (
    "https://tashkent.hh.uz/search/vacancy?area=2759"
    "&professional_role=96&order_by=publication_time&L_save_area=true"
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# ---------------------------------------------
#  Download page
# ---------------------------------------------
response = requests.get(SEARCH_URL, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

vacancies = soup.select("div.serp-item")
vacancies = soup.select("div[data-qa='vacancy-serp__vacancy']")
print(f"Found vacancies: {len(vacancies)}")

results = []

# ---------------------------------------------
#  Parse each vacancy
# ---------------------------------------------
for v in vacancies:
    # --- title & link ---
    title_tag = v.select_one("a.serp-item__title")
    title_tag = v.select_one("a[data-qa='serp-item__title']")
    title = title_tag.text.strip() if title_tag else None
    url = urljoin(BASE_URL, title_tag["href"]) if title_tag else None

    # --- company ---
    company_tag = v.select_one("a.bloko-link.bloko-link_kind-tertiary")
    company = company_tag.text.strip() if company_tag else None

    # --- salary ---
    salary_tag = v.select_one("span.bloko-header-section-3")
    salary = salary_tag.text.strip() if salary_tag else "Not specified"

    # --- location ---
    location_tag = v.select_one("div[data-qa='vacancy-serp__vacancy-address']")
    location = location_tag.text.strip() if location_tag else None

    # --- short description ---
    snippet_tag = v.select_one("div.g-user-content")
    snippet = snippet_tag.text.strip() if snippet_tag else None

    # --- publication date ---
    date_tag = v.select_one("span[data-qa='vacancy-serp__vacancy-date']")
    pub_date = date_tag.text.strip() if date_tag else None

    results.append({
        "title": title,
        "company": company,
        "salary": salary,
        "location": location,
        "url": url,
        "snippet": snippet,
        "published": pub_date
    })


# ---------------------------------------------
#  Save JSON
# ---------------------------------------------
with open("vacancies.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("\nSaved to vacancies.json")


#https://mitsloan.mit.edu/ideas-made-to-matter/machine-learning-explained