import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

class HH_Scraper():
    def __init__(self):
        pass
    def get_job_title(soup):
        titles = soup.select("h1[data-qa='vacancy-title']")
        text = "None"
        for title in titles:
            text = title.get_text()
        return text

    def get_job_salary(soup):
        salarys = soup.select("span[data-qa='vacancy-salary-compensation-type-gross']")
        text = "None"
        for title in salarys:
            text = title.get_text() 
        return text

    def get_job_location(soup):
        locations = soup.select("span[data-qa='vacancy-view-raw-address']")
        text = "None"
        for location in locations:
            text = location.get_text() 
        return text


    # get html from the response
    def get_html(url):      
        headers = {'User-Agent': 'Chrome/142.0.7444.164'}
        rq = requests.get(url, headers=headers)
        print('Getting HTML-code from ', url)
        return rq.text


    # check if vacansy exists
    def is_empty(html):
        soup = BeautifulSoup(html, 'lxml')
        links = links = soup.select("a[data-qa='serp-item__title']")
        if links == []:
            return True
        else:
            return False


    # get link for all job listings
    def get_all_offers_links(self, query, area):
        # headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        url_base = 'https://tashkent.hh.uz/search/vacancy?area=2759&professional_role=96&order_by=publication_time&L_save_area=true&page='


        # mark end of the list
        page_is_not_empty = True

        all_links = []
        page = 1

        while page_is_not_empty:
            url = url_base  + str(page)
            time.sleep(.5)
            html = self.get_html(url)
            if not self.is_empty(html):
                all_links = self.get_offers_links(html, all_links)
                page += 1
            else:
                page_is_not_empty = False
        return all_links


    # функция, которая собирает все ссылки на вакансии на странице поиска
    # принимает список, который уже может быть не пустой, возвращает дополненный список
    def get_offers_links(html, all_links):
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select("a[data-qa='serp-item__title']")
    
        for link in links:
            link_parsed = link.get('href').split('?')
            all_links.append(link_parsed[0])
        return all_links


    # функция, которая парсит блок с ключевыми навыками и возвращает дополненный словарь, который ей дали на входе
    def parse_skills_in_offer(soup):
        key_skills = soup.select("li[data-qa='skills-element']")
        skills_list = ','.join(''.join(element.find_all(text=True)) for element in key_skills)
        return skills_list


    # функция, которая парсит блок с описанием вакансии и возвращает дополненный словарь, который ей дали на входе
    def parse_description_in_offer(soup):
        # описание вакансии
        if not soup.find(string="Вакансия в архиве"):
            #description = soup.find('div', class_='vacancy-description')
            description = soup.select("div[data-qa='vacancy-description']")
            # оставим только текст без тегов
            text = ''.join(description[0].find_all(text=True))
            # почистим текст от знаков препинания
            for elem in ('.',',',';',':','"'):
                if elem in text:
                    text = text.replace(elem, ' ')
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
                f.write(area+' '+code+'\n')

        print('DONE')


    def parse_offers(self, links):
        skill_dict = {}
        description_dict = {}
        for link in links:
            html = self.get_html(link)
            time.sleep(.3)
            soup = BeautifulSoup(html, 'lxml')
            title = self.get_job_title(soup)
            salary = self.get_job_salary(soup)
            location = self.get_job_location(soup)
            skill_dict = self.parse_skills_in_offer(soup)
            description_dict = self.parse_description_in_offer(soup)
            with open('job_list.txt', 'a', encoding='utf-8') as f:
                f.write(f"Title: {title} | Salary: {salary} | Skills: {skill_dict} | Location: {location} | Deskcription: {description_dict}\n")
