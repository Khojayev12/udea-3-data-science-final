import pandas as pd
from olx_scrap import OLX_Scraper
from olx_url_builder import OLX_URLBuilder
from hh_scrap import HH_Scraper
import asyncio
from datetime import datetime
import re


# Mapping of Russian district names for Tashkent city to English (without the word "District").
RUS_TASHKENT_DISTRICTS_TO_EN = {
    "алмазарский район": "Almazar",
    "бектемирский район": "Bektemir",
    "юнусабадский район": "Yunusabad",
    "яшнабадский район": "Yashnabad",
    "яккасарайский район": "Yakkasaray",
    "сергелийский район": "Sergeli",
    "учтепинский район": "Uchtepa",
    "мирзо-улугбекский район": "Mirzo-Ulugbek",
    "шайхантахурский район": "Shaykhantakhur",
    "чиланзарский район": "Chilanzar",
    "мираборский район": "Mirabad",
    "мирабадский район": "Mirabad",
    "мирабад": "Mirabad",  # sometimes without "район"
}


def _extract_district(location: str) -> str | None:
    """Get district/area in English from a Location string."""
    if pd.isna(location):
        return None
    text = str(location)
    district_ru = text.split(",", 1)[1].strip() if "," in text else text.strip()
    district_key = district_ru.lower()
    translated = RUS_TASHKENT_DISTRICTS_TO_EN.get(district_key)
    return translated if translated else "Tashkent Region"


def _normalize_olx_date(value: str) -> str | None:
    """Convert OLX date text to DD-MM-YYYY. 'Сегодня' -> today."""
    if pd.isna(value):
        return None
    raw = str(value).strip().lower()
    if "сегодня" in raw:
        today = datetime.now().date()
        return today.strftime("%d-%m-%Y")

    month_map = {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }
    match = re.search(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", raw, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_text = match.group(2)
        year = int(match.group(3))
        month = month_map.get(month_text, None)
        if month:
            return f"{day:02d}-{month:02d}-{year}"

    return value


def process_olx_excel(input_path: str = "olx.xlsx", output_path: str = "olx_processed.xlsx") -> pd.DataFrame:
    """
    Read OLX Excel, add District (English) and normalize Date to DD-MM-YYYY.
    """
    df = pd.read_excel(input_path)
    df["District"] = df["Location"].apply(_extract_district)
    df["Date"] = df["Date"].apply(_normalize_olx_date)
    df.to_excel(output_path, index=False)
    return df

async def get_olx_data():
    search_items = [
        OLX_URLBuilder(**query) 
        for query in [{"item_query": "2 xonali kvartira arenda", "city": "tashkent", "distance": "30"}]
    ]

    olx_scrapper = OLX_Scraper(search_items, 10)
    result = await olx_scrapper.scrape_data()
    #print(olx_scrapper.data_frames)
    #print(result["2 xonali kvartira arenda - Tashkent - 30km"])
    #result["2 xonali kvartira arenda - Tashkent - 30km"].to_excel("rent_data.xlsx", sheet_name="OLX_Data", index=False)
    return result["2 xonali kvartira arenda - Tashkent - 30km"]

def get_hh_data():
    query = 'frontend'
    area = '2759'
    hh_scraper = HH_Scraper()
    links = hh_scraper.get_all_offers_links(query, area)
    print("Job Offers found: ", len(links))
    result = hh_scraper.parse_offers(links)
    return result

if __name__ == "__main__":
    raw_olx_df = asyncio.run(get_olx_data())
    print(raw_olx_df)

    raw_hh_df = get_hh_data()
    print(raw_hh_df)
