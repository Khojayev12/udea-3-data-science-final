import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# get html from the response
def get_html(url):      
    headers = {'User-Agent': 'Chrome/142.0.7444.164'}
    rq = requests.get(url, headers=headers)
    print('Gettin HTML-code from ', url)
    return rq.text


# check if vacansy exists
def is_empty(html):
    soup = BeautifulSoup(html, 'lxml')
    links = soup.find_all('a', class_='magritte-link___b4rEM_6-1-8 magritte-link_mode_primary___l6una_6-1-8 magritte-link_style_neutral___iqoW0_6-1-8 magritte-link_enable-visited___Biyib_6-1-8')
    if links == []:
        return True
    else:
        return False


# get link for all job listings
def get_all_offers_links(query, area):
    # headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    url_base = 'https://tashkent.hh.uz/search/vacancy'
    url_text = '?text='+query
    url_area = '&area='+area
    url_page = '&page='

    # mark end of the list
    page_is_not_empty = True

    all_links = []
    page = 1

    while page_is_not_empty:
        url = url_base + url_text + url_area + url_page + str(page)
        time.sleep(.5)
        html = get_html(url)
        if not is_empty(html):
            all_links = get_offers_links(html, all_links)
            page += 1
        else:
            page_is_not_empty = False
    return all_links


# функция, которая собирает все ссылки на вакансии на странице поиска
# принимает список, который уже может быть не пустой, возвращает дополненный список
def get_offers_links(html, all_links):
    # новый объект класса BeutifulSoup
    soup = BeautifulSoup(html, 'lxml')

    links = soup.find_all('a', class_='magritte-link___b4rEM_6-1-8 magritte-link_mode_primary___l6una_6-1-8 magritte-link_style_neutral___iqoW0_6-1-8 magritte-link_enable-visited___Biyib_6-1-8')
    for link in links:
        link_parsed = link.get('href').split('?')
        all_links.append(link_parsed[0])
    return all_links


# функция, которая парсит блок с ключевыми навыками и возвращает дополненный словарь, который ей дали на входе
def parse_skills_in_offer(soup, skill_dict):
    # находим блок с ключевыми навыками на странице
    key_skills = soup.find_all('span', class_='Bloko-TagList-Text')

    # добавляем текст навыков в словарь
    for skill in key_skills:
        if skill.get_text().lower() in skill_dict:
            skill_dict[skill.get_text().lower()] += 1
        else:
            skill_dict[skill.get_text().lower()] = 1

    return skill_dict


# функция, которая парсит блок с описанием вакансии и возвращает дополненный словарь, который ей дали на входе
def parse_description_in_offer(soup, description_dict):
    # описание вакансии
    if not soup.find(string="Вакансия в архиве"):
        description = soup.find('div', class_='vacancy-description')
        # оставим только текст без тегов
        text = ''.join(description.findAll(text=True))
        # почистим текст от знаков препинания
        for elem in ('.',',',';',':','"'):
            if elem in text:
                text = text.replace(elem, ' ')
        # проверим каждое слово и занесем его в словарь
        for word in text.split(' '):
            if word.lower() in description_dict:
                description_dict[word.lower()] += 1
            else:
                description_dict[word.lower()] = 1

    return description_dict


# функция, которая парсит основные регионы со страницы https://hh.ru/search/vacancy
# и сохраняет название региона и его код для GET запроса в файл
# функция нужна для себя - чтобы знать, какой код региона использовать
def get_and_save_area_codes():
    html = get_html('https://hh.ru/search/vacancy?area=1347')
    time.sleep(.3)
    soup = BeautifulSoup(html, 'lxml')
    # areas_parsed = []

    # нашли все объекты, которые содержат название региона и его код
    pairs = soup.find('div', class_='clusters-group').find_all('a', class_='clusters-value')

    # выделяем текст региона и кода, записываем в файл
    with open('area_codes02.txt', 'w', encoding='utf-8') as f:
        for pair in pairs:
            area = pair.find('span', class_='clusters-value__name').get_text()
            code = pair.get('href').split('&')[2].split('=')[1]
            f.write(area+' '+code+'\n')

    print('DONE')


def parse_offers(links):
    skill_dict = {}
    description_dict = {}
    for link in links:
        html = get_html(link)
        time.sleep(.3)
        soup = BeautifulSoup(html, 'lxml')
        skill_dict = parse_skills_in_offer(soup, skill_dict)
        description_dict = parse_description_in_offer(soup, description_dict)

    # запишем навыки в файл skills_freq
    skills_sorted = sorted(skill_dict.items(), key=lambda x: x[1], reverse = True)
    with open('skill_freq.txt', 'w', encoding='utf-8') as f:
        for skill in skills_sorted:
            f.write(skill[0]+' '+str(skill[1])+'\n')

    # запишем слова из описаний в файл descriptions_freq
    descriptions_sorted = sorted(description_dict.items(), key=lambda x: x[1], reverse = True)
    with open('description_freq.txt', 'w', encoding='utf-8') as f:
        for description in descriptions_sorted:
            f.write(description[0]+' '+str(description[1])+'\n')


if __name__ == '__main__':
    query = 'frontend'
    area = '2759'
    # сначала вытащим все ссылки на вакансии по данному запросу и региону
    links = get_all_offers_links(query, area)
    # теперь распарсим информацию по каждой ссылке, полученной выше
    parse_offers(links)

    print('Проверено ',len(links), ' вакансий.')