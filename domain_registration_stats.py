import os.path
from collections import defaultdict
import operator
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import math
import sys

sys.path.append('../')
from util import read_auxiliary_file, create_dir

# reg_file = read_auxiliary_file('domains_registration_info_joined_upd.tsv')
reg_file = read_auxiliary_file('domains_registration_info_with_ip.tsv')
# reg_file = read_auxiliary_file('reg_graphs_and_stats/domains_registration_info_joined.tsv')

ORG_TYPES = {
    'mass_media': ['media', 'radio', 'newspaper', 'jyrnal', 'gazet', 'press', 'television', 'GUP RB "Bashkortostan"',
                   'Rossiya Segodnya', 'RIK "Iskra"', 'Inforos Co., Ltd'],
    'publishing': ['publishing', 'izdatelstvo', 'izdatelskiy', 'editorial'],
    'education': ['state university'],
    'gov': ['ministry of', 'ministry for', 'administration of', 'ministerstvo', 'administratsiya',
            'Gosudarstvennogo Sobraniya', 'head of the republic', 'mincult', 'municipalnoe',
            'regionalnaya', 'Spetssvyaz FSO RF'],
    'rostelecom': ['rostelecom', 'rostelekom'],
    'hosters': ['LLC "Ucoz Media"', 'Compubyte Limited', 'Automattic, Inc.', '1&1 Internet Inc', 'Host Gate',
                'JSC Bashinformsvyaz'],
    'blogs': ['LiveJournal, Inc.', 'Google Inc.'],
    'art': ['library', 'teatr', '"TGAT im.G.Kamala"', 'kulturniy center']
}

# СМИ: media, radio, newspaper, jyrnal, gazet, press
# издательства: publishing, izdatelstvo, izdatelskiy, editorial
# образование: state university,
# гос: ministry (of|for), administration of, ministerstvo, Administratsiya
# Regionalnaya Nacianalno-kulturnaya avtonomia tatar Nigegorodskoj oblasti
# Municipalnoe avtonomnoe uchrezhdenie "Kazanskij gorodskoj obshchestvennyj centr"
# ростелеком (тоже hoster?): rostelekom
# art: "Finno-ugorskiy kulturniy center Rossiyskoy Federacii"

LANG_COLORS = {
    'Башкирский': 'orange',
    'Бурятский': 'red',
    'Чеченский': '#DFD91B',
    'Чувашский': 'cyan',
    'Кабардино-черкесский': 'green',
    'Лезгинский': '#7516BD',
    'Лугово-восточный марийский': '#DF1BDF',
    'Эрзя-мордовский': '#1E90FF',
    'Якутский': 'blue',
    'Татарский': 'grey',
    'Тувинский': '#457019',
    'Удмуртский': 'black',
    'Калмыцкий': '#298A08'
}

STYLES_REG = {
    'Общее': 'solid',
    'Частные лица': 'dashed',
    'Организации': 'dotted',
    'Неизвестно': '-.'
}

CODE_LABEL = {
    'overall': 'Общее',
    'overall_private': 'Частные лица',
    'overall_org': 'Организации',
    'overall_none': 'Неизвестно'
}

# Stavropol, Saratov
LANG_CAPITAL = {
    'Абазинский': 'cherkessk',
    'Аварский': 'makhachkala',
    'Адыгейский': 'maykop',
    'Башкирский': 'ufa',
    'Бурятский': 'ulaan-ude',
    'Ингушский': 'magas',
    'Кабардино-черкесский': 'nalchik',  # кабардино-балкария
    'Калмыцкий': 'elista',
    'Карачаево-балкарский': 'cherkessk',
    'Коми-зырянский': 'syktyvkar',
    'Коми-пермяцкий': 'perm',
    'Кумыкский': 'makhachkala',
    'Лакский': 'makhachkala',
    'Лезгинский': 'makhachkala',
    'Литературный даргинский': 'makhachkala',
    'Лугово-восточный марийский': 'yoshkar-ola',
    'Рутульский': 'makhachkala',
    'Татарский': 'kazan',
    'Татский': 'makhachkala',
    'Тувинский': 'kyzyl',
    'Тундровый ненецкий': 'salekhard',
    'Удмуртский': 'izhevsk',
    'Хакасский': 'abakan',
    'Чеченский': 'groznyi',
    'Чувашский': 'cheboksary',
    'Чукотский': 'anadyr',
    'Эвенкийский': '',
    'Эрзя-мордовский': 'saransk',
    'Якутский': 'yakutsk',
}


# общая вспомогательная функция
def get_code_lang_mapping(lang_info_data):
    lang_code = dict()
    for row in lang_info_data:
        lang = row['language'].decode('utf-8')
        code = row['iso_code'].decode('utf-8')
        lang_code[code] = lang
    return lang_code


# вспомогательная функция, чтобы посмотреть все домены первого-второго уровня
# и принять решения по повторяющимся
def count_major_domains(reg_data):
    dom_stats = dict()
    for row in reg_data:
        domain = row['domain'].decode('utf-8')
        major_dom = '.'.join(domain.split('.')[-2:])
        dom_stats[major_dom] = dom_stats.get(major_dom, 0) + 1
    return dom_stats


#########################
# кто зарегистрировал   #
#########################
def get_registers_stats(reg_data):
    lang_stats = defaultdict(dict)
    for row in reg_data:
        lang = row['lang'].decode('utf-8')
        person = row['name'].decode('utf-8')
        org = row['org'].decode('utf-8')
        if person != 'None' and org == 'None':
            lang_stats[lang]['private_person'] = lang_stats[lang].get('private_person', 0) + 1
        elif person == 'None' and org == 'None':
            lang_stats[lang]['none'] = lang_stats[lang].get('none', 0) + 1
        elif org != 'None':
            is_org_type_set = False
            org_type = None
            for key, val in sorted(ORG_TYPES.items()):
                for el in val:
                    if el.lower() in org.lower():
                        lang_stats[lang][key] = lang_stats[lang].get(key, 0) + 1
                        is_org_type_set = True
                        org_type = key
                        break
                if is_org_type_set:
                    break
            if not is_org_type_set:
                lang_stats[lang]['other'] = lang_stats[lang].get('other', 0) + 1
            if org_type in ['hosters', 'rostelecom']:
                lang_stats[lang]['none'] = lang_stats[lang].get('none', 0) + 1
            else:
                lang_stats[lang]['org'] = lang_stats[lang].get('org', 0) + 1
        lang_stats[lang]['overall'] = lang_stats[lang].get('overall', 0) + 1
    return lang_stats


def print_registers_stats(lang_stats):
    header = ['lang', 'private_person', 'org', 'mass_media', 'publishing', 'gov', 'blogs',
              'education', 'art', 'rostelecom', 'hosters', 'other', 'none', 'overall']
    print('\t'.join(header))

    for lang, stat in sorted(lang_stats.items()):
        for org_type in ORG_TYPES.keys():
            if org_type not in stat:
                stat[org_type] = 0
        vals_to_print = [lang] + [stat['private_person'] if 'private_person' in stat else 0]
        vals_to_print.append(stat['org'] if 'org' in stat else 0)
        for h in header[3:11]:
            vals_to_print.append(stat[h])
        vals_to_print.append(stat['other'] if 'other' in stat else 0)
        vals_to_print.append(stat['none'] if 'none' in stat else 0)
        vals_to_print.append(stat['overall'])
        print("\t".join(str(val) for val in vals_to_print))
        # print(lang, stat['private_person'] if 'private_person' else 0, stat['mass_media'], stat[''])
        # print('\t', stat)


# общий график с регистрировавшими частниками и организациями
def draw_registers_stats(lang_stats):
    langs = list()
    private = list()
    org = list()
    unknown = list()  # nones
    langs_info = read_auxiliary_file('../aux_files/langs_all_info.csv')
    code_to_lang = get_code_lang_mapping(langs_info)
    lang_stats_ru = dict([(code_to_lang[lang], val) for lang, val in lang_stats.items() if '_' not in lang])
    for lang, stat in sorted(lang_stats_ru.items()):
        langs.append(lang)
        private.append(stat['private_person'] if 'private_person' in stat else 0)
        org.append(stat['org'] if 'org' in stat else 0)
        unknown.append(stat['none'] if 'none' in stat else 0)
    n = len(langs)
    ind = np.arange(n)
    width = 0.25
    fig, ax = plt.subplots()
    rects1 = ax.bar(ind - width, private, width, color='#DF7401')
    rects2 = ax.bar(ind, org, width, color='#0B614B')
    rects3 = ax.bar(ind + width, unknown, width, color='#848484')

    # добавляем надписи
    ax.set_ylabel('Количество сайтов', fontsize=22)
    ttl = ax.set_title('Распределение по регистрировавшим домены', fontsize=30)
    ax.set_xticks(ind + width/2)
    ax.set_xticklabels(langs, rotation=90, fontsize=16)

    # красиво располагаем подписи на графике
    ttl.set_position([.5, 1.02])
    plt.subplots_adjust(bottom=0.35)
    plt.axis([-1, len(langs), 0, max(private + org + unknown) + 5])

    ax.legend((rects1[0], rects2[0], rects3[0]), ('Частные лица', 'Организации', 'Неизвестно'))
    plt.show()


# два графика: на одном те, где больше частников, на другом те, где больше организаций
def draw_registers_stats_separately(lang_stats):
    langs = defaultdict(list)
    private = defaultdict(list)
    org = defaultdict(list)
    unknown = defaultdict(list)  # nones
    langs_info = read_auxiliary_file('../aux_files/langs_all_info.csv')
    code_to_lang = get_code_lang_mapping(langs_info)
    lang_stats_ru = dict([(code_to_lang[lang], val) for lang, val in lang_stats.items() if '_' not in lang])
    for lang, stat in sorted(lang_stats_ru.items()):
        if ('private_person' in stat and 'org' not in stat) \
                or ('private_person' in stat and 'org' in stat
                    and stat['private_person'] > stat['org']):
            langs['private'].append(lang)
            private['private'].append(stat['private_person'] if 'private_person' in stat else 0)
            org['private'].append(stat['org'] if 'org' in stat else 0)
            unknown['private'].append(stat['none'] if 'none' in stat else 0)
        else:
            langs['org'].append(lang)
            private['org'].append(stat['private_person'] if 'private_person' in stat else 0)
            org['org'].append(stat['org'] if 'org' in stat else 0)
            unknown['org'].append(stat['none'] if 'none' in stat else 0)
    for reg_type, stat in langs.items():
        n = len(langs[reg_type])
        ind = np.arange(n)
        width = 0.25
        fig, ax = plt.subplots()
        rects1 = ax.bar(ind - width, private[reg_type], width, color='#DF7401')
        rects2 = ax.bar(ind, org[reg_type], width, color='#0B614B')
        rects3 = ax.bar(ind + width, unknown[reg_type], width, color='#848484')

        # добавляем надписи
        ax.set_ylabel('Количество сайтов', fontsize=22)
        ttl = ax.set_title('Распределение по регистрировавшим домены', fontsize=30)
        ax.set_xticks(ind + width/2)
        ax.set_xticklabels(langs[reg_type], rotation=90, fontsize=16)

        # красиво располагаем подписи на графике
        ttl.set_position([.5, 1.02])
        plt.subplots_adjust(bottom=0.35)
        plt.axis([-1, len(langs[reg_type]), 0, max(private[reg_type] + org[reg_type] + unknown[reg_type]) + 5])

        ax.legend((rects1[0], rects2[0], rects3[0]), ('Частные лица', 'Организации', 'Неизвестно'))
        plt.show()

MONTH_TO_TEXT = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

#########################
# когда зарегистрировал #
#########################
def get_date_stats(reg_data):
    date_stats = defaultdict(dict)
    for row in reg_data:
        lang = row['lang'].decode('utf-8')
        date_str = row['creation_date'].decode('utf-8')
        if date_str in ['None', 'unknown']:
            continue
        date = datetime.strptime(date_str.split(' ')[0], "%Y-%m-%d")
        if date.year == 2012:
            key_str = date.month
            date_stats[lang][key_str] = date_stats[lang].get(key_str, 0) + 1
            date_stats['overall'][key_str] = date_stats['overall'].get(key_str, 0) + 1
            add_info_into_right_reg_type(row, key_str, date_stats)
        # date_stats[lang][date.year] = date_stats[lang].get(date.year, 0) + 1
        # date_stats['overall'][date.year] = date_stats['overall'].get(date.year, 0) + 1
        # add_info_into_right_reg_type(row, date.year, date_stats)

    return date_stats


def draw_date_stats(date_stats):
    langs_info = read_auxiliary_file('../aux_files/langs_all_info.csv')
    code_to_lang = get_code_lang_mapping(langs_info)
    code_to_lang['overall'] = 'Общее распределение по датам'

    graphs_dir = create_dir('date_graphs')
    # draw_each_lang_separately(date_stats, code_to_lang, graphs_dir)
    # draw_all_langs_same_plot(date_stats, code_to_lang, graphs_dir)
    draw_overall_dates_with_registrars(date_stats, graphs_dir)


def draw_each_lang_separately(date_stats, code_to_lang, graphs_dir):
    for lang, date_val in sorted(date_stats.items()):
        if len(date_val) in [1, 2] or (set(date_val.values()) == {1} and len(date_val) < 5) \
                or 'overall_' in lang:
            # print(date_val)
            continue
        sorted_date = sorted(date_val.items())
        plt.figure(figsize=(16.0, 9.0), dpi=80)
        x = [s_date[0] for s_date in sorted_date]
        y = [s_date[1] for s_date in sorted_date]
        plt.plot(x, y)
        plt.plot(x, y, 'or')
        max_y = max(y) + 1
        plt.ylim([0, max_y])
        plt.xlim([min(x) - 1, max(x) + 1])
        plt.xticks(np.arange(min(x) - 1, max(x) + 1, 1.0), fontsize=12)
        step = 2.0 if lang == 'overall' else 1.0
        plt.yticks(np.arange(min(y) - 1, max(y) + 1, step), fontsize=12)
        plt.xlabel('Даты', fontsize=16, labelpad=20)
        plt.ylabel('Количество сайтов', fontsize=16, labelpad=20)
        if lang not in code_to_lang:
            langs = lang.split('_')
            new_lang = ", ".join([code_to_lang[l] for l in langs])
        else:
            new_lang = code_to_lang[lang]
        ttl = plt.title(new_lang, fontsize=22)
        ttl.set_position([.5, 1.02])  # x and y of position
        # plt.show()
        plt.savefig(os.path.join(graphs_dir, lang + '.png'), dpi=100)
        # print(lang, sorted(date_val.items()))


def draw_all_langs_same_plot(date_stats, code_to_lang):
    plt.figure(figsize=(16.0, 9.0), dpi=80)
    sorted_dates = sorted(date_stats['overall'].keys())
    plt.xlim([min(sorted_dates) - 1, max(sorted_dates) + 2])
    plt.ylim([0, 15])  # magic number
    plt.xticks(np.arange(min(sorted_dates), max(sorted_dates) + 1, 1.0), fontsize=12)
    plt.yticks(np.arange(0, 15, 1.0), fontsize=12)

    for lang, date_val in sorted(date_stats.items()):
        if len(date_val) in [1, 2] or (set(date_val.values()) == {1} and len(date_val) < 5):
            # if len(date_val) in [1, 2] or set(date_val.values()) == {1}\
            #         or set(date_val.values()) == {1, 2}:
            # print(date_val)
            continue
        if lang == 'overall' or '_' in lang:
            continue
        sorted_date = sorted(date_val.items())
        x = [s_date[0] for s_date in sorted_date]
        y = [s_date[1] for s_date in sorted_date]
        new_lang = code_to_lang[lang]
        plt.plot(x, y, color=LANG_COLORS[new_lang], label=new_lang)

    plt.xlabel('Даты', fontsize=16, labelpad=20)
    plt.ylabel('Количество сайтов', fontsize=16, labelpad=20)
    ttl = plt.title('Все языки', fontsize=22)
    ttl.set_position([.5, 1.02])  # x and y of position
    leg = plt.legend(loc='upper right', fontsize='large')
    for legobj in leg.legendHandles:
        legobj.set_linewidth(2.5)
    plt.show()
    # plt.savefig(os.path.join(graphs_dir, 'all_on_one' + '.png'), dpi=100)


def draw_overall_dates_with_registrars(date_stats, graphs_dir):
    plt.figure(figsize=(16.0, 9.0), dpi=80)
    sorted_dates = sorted(date_stats['overall'].keys())
    y_range = date_stats['overall'].values()
    plt.xlim([min(sorted_dates) - 1, max(sorted_dates) + 2])
    plt.ylim([0, max(y_range) + 1])
    # plt.xticks(np.arange(min(sorted_dates), max(sorted_dates) + 1, 1.0), fontsize=12)
    labels = list(MONTH_TO_TEXT.values())
    plt.xticks(np.arange(min(sorted_dates), max(sorted_dates) + 1, 1.0), labels, fontsize=12)
    plt.yticks(np.arange(0, max(y_range), 2.0), fontsize=12)

    for lang in sorted(CODE_LABEL.keys()):
        date_val = date_stats[lang]
        sorted_date = sorted(date_val.items())
        x = [s_date[0] for s_date in sorted_date]
        y = [s_date[1] for s_date in sorted_date]
        plt.plot(x, y, linestyle=STYLES_REG[CODE_LABEL[lang]], label=CODE_LABEL[lang], color='#2C6B3A')
    plt.xlabel('Даты', fontsize=16, labelpad=20)
    plt.ylabel('Количество сайтов', fontsize=16, labelpad=20)
    ttl = plt.title('Общее распределение по датам', fontsize=22)
    ttl.set_position([.5, 1.02])  # x and y of position
    leg = plt.legend(loc='upper right', fontsize='large')
    for legobj in leg.legendHandles:
        legobj.set_linewidth(2.5)
    # plt.show()
    plt.savefig(os.path.join(graphs_dir, 'overall_reg_mono' + '.png'), dpi=100)


def add_info_into_right_reg_type(row, data, res_dict):
    person = row['name'].decode('utf-8')
    org = row['org'].decode('utf-8')
    if person != 'None' and org == 'None':
        res_dict['overall_private'][data] = res_dict['overall_private'].get(data, 0) + 1
    # информация о том, что домен зарегистрирован хостингом, не обязательно говорит о том,
    #  что регистрировавший организация
    elif person == 'None' and org == 'None':
        res_dict['overall_none'][data] = res_dict['overall_none'].get(data, 0) + 1
    elif org != 'None':
        trash_org_set = False
        for el in ORG_TYPES['hosters'] + ORG_TYPES['rostelecom']:
            if el.lower() in org.lower():
                res_dict['overall_none'][data] = res_dict['overall_none'].get(data, 0) + 1
                trash_org_set = True
                break
        if not trash_org_set:
            res_dict['overall_org'][data] = res_dict['overall_org'].get(data, 0) + 1


#########################
# где зарегистрировали  #
#########################
def get_city_stats(reg_data):
    city_stats = defaultdict(dict)
    for row in reg_data:
        lang = row['lang'].decode('utf-8')
        # city_str = row['city'].decode('utf-8').lower()
        city_str = row['city_by_ip'].decode('utf-8').lower().split('(')[0].strip().strip('')
        # if city_str in ['none', 'unknown']:
        #     continue
        if row['name'].decode('utf-8') == 'None' and row['org'].decode('utf-8') == 'None':
            city_str = 'none'
        city_stats[lang][city_str] = city_stats[lang].get(city_str, 0) + 1
        city_stats['overall'][city_str] = city_stats['overall'].get(city_str, 0) + 1
        add_info_into_right_reg_type(row, city_str, city_stats)
    return city_stats


# http://matplotlib.org/examples/pylab_examples/bar_stacked.html
def draw_city_per_lang(city_stats, with_none=False, log_scale=False):
    langs = list()
    region_capitals = list()
    ru_capital = list()
    spb = list()
    other_cities = list()
    nones = list()
    langs_info = read_auxiliary_file('../aux_files/langs_all_info.csv')
    code_to_lang = get_code_lang_mapping(langs_info)
    lang_stats_ru = dict([(code_to_lang[lang], val) for lang, val in city_stats.items()
                          if '_' not in lang and lang != 'overall'])
    for lang, stat in sorted(lang_stats_ru.items()):
        # не рисуем языки, где только столбик с неизвестно
        if 'none' in stat and len(stat) == 1:
            continue
        else:
            langs.append(lang)
            other_cities_num = 0
            for city, freq in stat.items():
                if city not in (LANG_CAPITAL[lang], 'moscow', 'none', 'saint petersburg'):
                    other_cities_num += freq
            region_capitals.append(stat[LANG_CAPITAL[lang]] if LANG_CAPITAL[lang] in stat else 0)
            ru_capital.append(stat['moscow'] if 'moscow' in stat else 0)
            spb.append(stat['saint petersburg'] if 'saint petersburg' in stat else 0)
            other_cities.append(other_cities_num)
            nones.append(stat['none'] if 'none' in stat else 0)

    n = len(langs)
    ind = np.arange(n)
    width = 0.25

    if log_scale:
        other_cities = [math.log(city) if city != 0 else 0 for city in other_cities]
        ru_capital = [math.log(city) if city != 0 else 0 for city in ru_capital]
        region_capitals = [math.log(city) if city != 0 else 0 for city in region_capitals]
        nones = [math.log(city) if city != 0 else 0 for city in nones]

    p1 = plt.bar(ind, other_cities, width, color='#D8D8D8')
    p2 = plt.bar(ind, ru_capital, width, color='#848484', bottom=other_cities)
    p5 = plt.bar(ind, spb, width, color='#58ACFA',
                 bottom=[i + j for i, j in zip(other_cities, ru_capital)])
    p3 = plt.bar(ind, region_capitals, width, color='#A9E2F3',
                 bottom=[i + j + k for i, j, k in zip(other_cities, ru_capital, spb)])
    if with_none:
        p4 = plt.bar(ind, nones, width, color='white',
                     bottom=[i + j + k + z for i, j, k, z in zip(other_cities, ru_capital, region_capitals, spb)])

    # добавляем надписи
    plt.ylabel('Количество сайтов', fontsize=22)
    ttl = plt.title('Распределение сайтов по городам', fontsize=30)
    plt.xticks(ind + width / 2., langs, rotation=90, fontsize=16)

    # красиво располагаем подписи на графике
    ttl.set_position([.5, 1.02])
    plt.subplots_adjust(bottom=0.35)
    if with_none:
        max_y = max(region_capitals) + max(ru_capital) + max(nones) + max(other_cities) + max(spb)
    else:
        max_y = max(region_capitals) + max(ru_capital) + max(other_cities)
    plt.axis([-1, len(langs), 0, max_y + 5])

    # if log_scale:
    #     plt.yscale('log', )

    if with_none:
        plt.legend((p3[0], p5[0], p2[0], p1[0], p4[0]), ('Столицы регионов', 'Санкт-Петербург', 'Москва', 'Другие города', 'Неизвестно'))
    else:
        plt.legend((p3[0], p2[0], p1[0]), ('Столицы регионов', 'Москва', 'Другие города'))
    plt.show()


# http://matplotlib.org/examples/api/barchart_demo.html
def draw_cities_overall(city_stats, with_none=False):
    labels = ['Частные лица', 'Организации']
    region_capitals = list()
    ru_capital = list()
    spb = list()
    other_cities = list()
    nones = list()
    keys = ['overall_private', 'overall_org']
    for key in keys:
        region_capitals_num = 0
        other_cities_num = 0
        for city, freq in city_stats[key].items():
            if city not in list(LANG_CAPITAL.values()) + ['moscow', 'none', 'saint petersburg']:
                other_cities_num += freq
            elif city in list(LANG_CAPITAL.values()):
                region_capitals_num += freq
        region_capitals.append(region_capitals_num)
        other_cities.append(other_cities_num)
        ru_capital.append(city_stats[key]['moscow'] if 'moscow' in city_stats[key] else 0)
        spb.append(city_stats[key]['saint petersburg'] if 'saint petersburg' in city_stats[key] else 0)
        nones.append(city_stats[key]['none'] if 'none' in city_stats[key] else 0)
    n = 2
    ind = np.arange(n)
    width = 0.10
    fig, ax = plt.subplots()
    rects1 = ax.bar(ind - 2*width, region_capitals, width, color='#A9E2F3')
    rects2 = ax.bar(ind - width, ru_capital, width, color='#848484')
    rects5 = ax.bar(ind, spb, width, color='#58ACFA')
    rects3 = ax.bar(ind + width, other_cities, width, color='#D8D8D8')
    if with_none:
        rects4 = ax.bar(ind + 2 * width, nones, width, color='white')

    # добавляем надписи
    ax.set_ylabel('Количество сайтов', fontsize=22)
    ttl = ax.set_title('Распределение сайтов по городам', fontsize=30)
    if with_none:
        ax.set_xticks(ind + width)
    else:
        ax.set_xticks(ind + width / 2)
        # ax.set_xticks(ind + width)
    ax.set_xticklabels(labels, fontsize=16)

    # красиво располагаем подписи на графике
    ttl.set_position([.5, 1.02])
    # plt.subplots_adjust(bottom=0.35)
    if with_none:
        plt.axis([-0.5, len(region_capitals), 0, max(region_capitals + ru_capital + other_cities + nones) + 25])
    else:
        plt.axis([-0.3, len(region_capitals) - 0.5, 0, max(region_capitals + ru_capital + other_cities + spb) + 5])

    if with_none:
        ax.legend((rects1[0], rects2[0], rects5[0], rects3[0], rects4[0]),
                  ('Столицы регионов', 'Москва', 'Санкт-Петербург', 'Другие города', 'Неизвестно'))
    else:
        ax.legend((rects1[0], rects2[0], rects5[0], rects3[0]), ('Столицы регионов', 'Москва', 'Санкт-Петербург', 'Другие города'))

    autolabel(rects1, ax)
    autolabel(rects2, ax)
    autolabel(rects3, ax)
    autolabel(rects5, ax)
    if with_none:
        autolabel(rects4, ax)

    plt.show()


def autolabel(rects, ax):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2., height,
                '%d' % int(height),
                ha='center', va='bottom')
    return

# date_stats = get_date_stats(reg_file)
# draw_date_stats(date_stats)

city_stats = get_city_stats(reg_file)
# print(city_stats['bak'])
# draw_city_per_lang(city_stats, True, True)
# draw_city_per_lang(city_stats, True)
# draw_city_per_lang(city_stats)
# draw_cities_overall(city_stats, True)
# draw_cities_overall(city_stats)
# for city, freq in sorted(city_stats['overall_private'].items(), key=operator.itemgetter(1), reverse=True):
#     print(city, freq, sep='\t')


# reg_stats = get_registers_stats(reg_file)
# print_registers_stats(reg_stats)
# draw_registers_stats(reg_stats)
# draw_registers_stats_separately(reg_stats)

# for key, val in sorted(count_major_domains(reg_file).items(), key=operator.itemgetter(1), reverse=True):
#     if val == 1:
#         continue
#     print(key, val, sep='\t')
