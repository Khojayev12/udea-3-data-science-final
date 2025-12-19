# Async scraper for OLX listings (housing focus), with helpers for parsing listing cards.
import json
import os
from datetime import datetime
from typing import Union, Callable
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import bs4.element
import pandas as pd
import aiohttp
import asyncio
import re

from olx_url_builder import OLX_URLBuilder

import locale
import re


class OLX_Scraper:
    def __init__(self, url_strings: list[OLX_URLBuilder], page_limit: int) -> None:
        """
        Scraper class for scraping data from OLX.
        :param url_strings: List of URLBuilder objects for scraping data.
        :param page_limit: Limit of pages to scrape for each URL.
        """
        self.url_list = url_strings if url_strings else []
        self.page_limit = page_limit
        self.data_frames = dict()
        self.count_pattern = re.compile(r'Znaleźliśmy\s+(?:ponad\s+)?(\d+)\s+ogłosze(?:ń|nie|nia)')
        self.listings_counts = []
        self.resources_dir = os.path.join(os.path.dirname(__file__), '../Resources')
        self.scraping_history = self.load_scraping_history()
        self.last_scrape_date = datetime.fromisoformat(
            self.scraping_history[-1]['scrape_date']) if self.scraping_history else None

    def add_url(self, url: OLX_URLBuilder) -> None:
        """
        Adds a URLBuilder object to the list of URLs to scrape.
        :param url: URLBuilder object to add.
        :return:
        """
        self.url_list.append(url)

    def format_price(self, price: str) -> int:
        """
        Returns price as integer. Removes all non-digit characters.
        :param price: price string
        :return: formatted price
        """
        price = price.replace("do negocjacji", "").strip()
        price = re.sub(r'\D', '', price)
        return int(price) if price else 0

    def format_location_date(self, location_date: str) -> tuple[str, str]:
        """
        Returns location and date from location_date string. Formats date to polish format.
        :param location_date: location and date string
        :return: formatted location and date
        """
        location, date = location_date.split(" - ")[:2]
        if "dzisiaj" in date.lower():
            locale.setlocale(locale.LC_ALL, 'pl_PL')
            formatted_date = datetime.datetime.now().strftime("%d %B %Y")
            date = formatted_date
        return location, date

    async def scrape_data(self, progress_callback: Callable[[int], None] = None) -> dict[str, pd.DataFrame]:
        """
        Scrapes data from the URLs asynchronously.
        :param progress_callback: Callback function to update the progress bar.
        :return: Dictionary of data frames with scraped data.
        """
        self.data_frames = dict()
        num_urls = len(self.url_list)
        tasks = []
        for i, url in enumerate(self.url_list):
            tasks.append(self._fetch_data_from_url(url))
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50))
            await asyncio.sleep(0.1)  # Small delay to allow UI update

        data = await asyncio.gather(*tasks)
        for i, result, url_builder in zip(range(len(self.url_list)), data, self.url_list):
            key = url_builder.generate_data_key()
            self.data_frames[key] = result
            if progress_callback:
                progress_callback(int((i + 1) / num_urls * 50 + 50))
        self.last_scrape_date = datetime.now()
        self.save_scrape_date()
        return self.data_frames

    async def _fetch_data_from_url(self, url_builder: OLX_URLBuilder) -> pd.DataFrame:
        """
        Fetches data from the given URL.
        :param url_builder: URLBuilder object to fetch data from.
        :return: Data frame with the scraped data.
        """
        async with aiohttp.ClientSession() as session:
            all_items = []
            page = 1
            while True:
                site_url = urlparse(url_builder.build_url(page))
                async with session.get(site_url.geturl()) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), "html.parser")
                        items = soup.find_all("div", {"data-cy": "l-card"})
                        all_items.extend(items)
                        count = self.find_count(soup)

                        # Stop when we hit the configured page cap or have collected the advertised total.
                        if page >= self.page_limit or len(all_items) >= count:
                            break
                        page += 1
                    else:
                        raise Exception(f"Error: {response.status} for {site_url.geturl()}")
            return pd.DataFrame(self._process_item(self, item) for item in all_items) if all_items else pd.DataFrame()

    @staticmethod
    def _process_item(self, item: bs4.element.Tag) -> dict:
        """
        Processes an item from the scraped data.
        :param item: Item to process.
        :return: Dictionary with the processed item data.
        """
        try:
            title = item.find("h4").text.strip()
            price = item.find("p", {"data-testid": "ad-price"}).text.strip()
            location, date = self.format_location_date(
                item.find("p", {"data-testid": "location-date"}).text) if item.find("p",
                                                                                    {
                                                                                        "data-testid": "location-date"}) else (
                "", "")
            photo = item.find("img").get("src") if item.find("img") else ""
            item_url = urljoin("https://www.olx.uz", item.find("a").get("href"))
            return {"Title": title, "Price": price, "Location": location, "Date": date, "Item URL": item_url,
                    "Photo": photo}
        except Exception as e:
            print(e)
            return {"Title": None, "Price": None, "Location": None, "Date": None, "Item URL": None,
                    "Photo": None}

    def find_count(self, soup: BeautifulSoup) -> int:
        """
        Finds the number of listings on the page.
        :param soup: Soup object to search for the count.
        :return: Number of listings on the page.
        """
        count_element = soup.find("span", {"data-testid": "total-count"})
        if not count_element or not count_element.text:
            return 0
        text = count_element.text.strip()
        # Match number including "1 000" with spaces
        match = re.search(r'(\d[\d\s]*)', text)
        if not match:
            return 0
        # Remove spaces inside the number
        number = re.sub(r"\s+", "", match.group(1))
        try:
            count = int(number)
        except ValueError:
            return 0
        self.listings_counts.append(count)
        return count

    def save_scrape_date(self) -> None:
        """
        Saves the date of the last scrape to the scraping history file.
        :return:
        """
        history_file_path = "scraping_history.json"
        scraping_entry = {'scrape_date': self.last_scrape_date.isoformat()}

        try:
            with open(history_file_path, 'r+') as file:
                history = json.load(file)
                history.append(scraping_entry)
                file.seek(0)
                json.dump(history, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(history_file_path, 'w') as file:
                json.dump([scraping_entry], file, indent=4)

    def load_scraping_history(self) -> list[dict[str, Union[str, datetime]]]:
        """
        Loads the scraping history from the scraping history file.
        :return: List of scraping history entries.
        """
        try:
            with open(os.path.join(self.resources_dir, 'scraping_history.json'), 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def update_url_list(self, config: dict) -> None:
        """
        Updates the URL list with the given configuration.
        :param config: Configuration dictionary.
        :return:
        """
        self.url_list = [OLX_URLBuilder(**query) for query in config['search_queries']]
