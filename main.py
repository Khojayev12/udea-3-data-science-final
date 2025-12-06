from olx_scrap import OLX_Scraper
from olx_url_builder import OLX_URLBuilder
from hh_scrap import HH_Scraper
import asyncio

async def get_olx_data():
    search_items = [
        OLX_URLBuilder(**query) 
        for query in [{"item_query": "2 xonali kvartira arenda", "city": "tashkent", "distance": "30"}]
    ]

    olx_scrapper = OLX_Scraper(search_items, 15)
    result = await olx_scrapper.scrape_data()
    #print(olx_scrapper.data_frames)
    print(result["2 xonali kvartira arenda - Tashkent - 30km"])
    result["2 xonali kvartira arenda - Tashkent - 30km"].to_excel("rent_data.xlsx", sheet_name="OLX_Data", index=False)
    return result

raw_olx_df = asyncio.run(get_olx_data())

def get_hh_data():
    query = 'frontend'
    area = '2759'
    hh_scraper = HH_Scraper()
    links = hh_scraper.get_all_offers_links(query, area)
    print("Job Offers found: ", len(links))
    hh_scraper.parse_offers(links)