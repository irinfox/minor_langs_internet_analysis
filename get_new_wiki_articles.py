from urllib import request
from urllib import parse
from bs4 import BeautifulSoup


def get_json_from_wiki():
    concrete_page = 'Википедия:Список_Википедий'
    quote_page = parse.quote(concrete_page, encoding='utf-8')
    # url = 'https://meta.wikipedia.org//w/api.php?action=parse&format=json&text=%s&contentmodel=wikitext' % quote_page
    # url = 'https://ru.wikipedia.org/wiki/%s' % quote_page
    url = 'https://incubator.wikimedia.org/wiki/User:Andrijko_Z./%D0%92%D0%B8%D0%BA%D0%B8_%D0%BD%D0%B0_%D1%8F%D0%B7%D1%8B%D0%BA%D0%B0%D1%85_%D0%BD%D0%B0%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8_%D0%B8_%D0%B1%D0%BB%D0%B8%D0%B6%D0%BD%D0%B5%D0%B3%D0%BE_%D0%B7%D0%B0%D1%80%D1%83%D0%B1%D0%B5%D0%B6%D1%8C%D1%8F'
    # print(url)
    soup = BeautifulSoup(request.urlopen(url).read().decode('utf-8'))
    soup_main_tag = soup.body
    tables = soup_main_tag.find_all('table', attrs= {'class': 'sortable'})
    for table in tables:
        headers = list()

        for th in table.find_all('th'):
            # print(th)
            span = th.find('span')
            a = th.find('a')
            if span:
                text = span.text
            elif a:
                text = a.text
            else:
                text = th.text
            headers.append(text)
        print('\t'.join(headers))
        for tr in table.find_all('tr'):
            contents = list()
            for td in tr.find_all('td'):
                a = td.find('a')
                text = a.text if a else td.text
                contents.append(text)
            print('\t'.join(contents))

get_json_from_wiki()