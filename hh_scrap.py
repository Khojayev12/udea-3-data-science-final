import pandas as pd
import requests
from bs4 import BeautifulSoup
import time


class HH_Scraper():
    def __init__(self):
        pass

    def get_job_title(self, soup):
        titles = soup.select("h1[data-qa='vacancy-title']")
        text = "None"
        for title in titles:
            text = title.get_text()
        return text

    def get_job_salary(self, soup):
        salarys = soup.select("span[data-qa='vacancy-salary-compensation-type-gross']")
        text = "None"
        for title in salarys:
            text = title.get_text()
        return text

    def get_job_location(self, soup):
        locations = soup.select("span[data-qa='vacancy-view-raw-address']")
        text = "None"
        for location in locations:
            text = location.get_text()
        return text

    # get html from the response
    def get_html(self, url):
        headers = {'User-Agent': 'Chrome/142.0.7444.164'}
        rq = requests.get(url, headers=headers)
        return rq.text

    # check if vacansy exists
    def is_empty(self, html):
        soup = BeautifulSoup(html, 'lxml')
        links = links = soup.select("a[data-qa='serp-item__title']")
        if links == []:
            return True
        else:
            return False

    # get link for all job listings
    def get_all_offers_links(self, query, area):
        url_base = "https://tashkent.hh.uz/search/vacancy?area=2759&order_by=publication_time&L_save_area=true&search_field=name&search_field=company_name&search_field=description&enable_snippets=false&label=with_address&label=with_salary&professional_role=156&professional_role=160&professional_role=10&professional_role=12&professional_role=150&professional_role=25&professional_role=165&professional_role=34&professional_role=36&professional_role=73&professional_role=155&professional_role=96&professional_role=164&professional_role=104&professional_role=157&professional_role=107&professional_role=112&professional_role=113&professional_role=148&professional_role=114&professional_role=116&professional_role=121&professional_role=124&professional_role=125&professional_role=126&page="
        # mark end of the list
        page_is_not_empty = True

        all_links = []
        page = 1

        while page_is_not_empty:
            url = url_base + str(page)
            time.sleep(.5)
            html = self.get_html(url)
            if not self.is_empty(html):
                all_links = self.get_offers_links(html, all_links)
                page += 1
            else:
                page_is_not_empty = False
        return all_links

    def get_offers_links(self, html, all_links):
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select("a[data-qa='serp-item__title']")

        for link in links:
            link_parsed = link.get('href').split('?')
            all_links.append(link_parsed[0])
        return all_links

    def parse_skills_in_offer(self, soup):
        key_skills = soup.select("li[data-qa='skills-element']")
        skills_list = ''
        if key_skills:
            skills_list = ','.join(''.join(element.find_all(text=True)) for element in key_skills)
        return skills_list

    def parse_description_in_offer(self, soup):
        if not soup.find(string="Вакансия в архиве"):
            description = soup.select("div[data-qa='vacancy-description']")
            if description:
                text = ''.join(description[0].find_all(text=True))
                for elem in ('.', ',', ';', ':', '"'):
                    if elem in text:
                        text = text.replace(elem, ' ')
            else:
                text = ''
            return text

    def get_and_save_area_codes(self):
        html = self.get_html('https://hh.ru/search/vacancy?area=1347')
        time.sleep(.3)
        soup = BeautifulSoup(html, 'lxml')

        pairs = soup.find('div', class_='clusters-group').find_all('a', class_='clusters-value')

        with open('area_codes02.txt', 'w', encoding='utf-8') as f:
            for pair in pairs:
                area = pair.find('span', class_='clusters-value__name').get_text()
                code = pair.get('href').split('&')[2].split('=')[1]
                f.write(area + ' ' + code + '\n')

    def parse_offers(self, links):
        raw_rows = []
        skill_dict = {}
        description_dict = {}
        for link in links:
            html = self.get_html(link)
            time.sleep(0.3)
            soup = BeautifulSoup(html, 'lxml')
            title = self.get_job_title(soup)
            salary = self.get_job_salary(soup)
            location = self.get_job_location(soup)
            skill_dict = self.parse_skills_in_offer(soup)
            description_dict = self.parse_description_in_offer(soup)

            raw_single_row = {
                "Title": title,
                "Salary": salary,
                "Skills": skill_dict,
                "Location": location,
                "Description": description_dict
            }
            raw_rows.append(raw_single_row)
        result_df = pd.DataFrame(raw_rows)
        return result_df
