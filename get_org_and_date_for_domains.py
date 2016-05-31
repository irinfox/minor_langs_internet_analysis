import os
from collections import defaultdict
from glob import glob
from datetime import datetime
import time
import argparse
import re
import whois  # python-whois (https://pypi.python.org/pypi/python-whois/0.6)
from urllib import request
import json
import subprocess

import sys

sys.path.append('../')
from util import read_auxiliary_file


def main(arguments):
    if arguments.url_lists_folder or arguments.ambig_domains_folder:
        print('lang', 'domain', 'creation_date', 'registrar', 'name', 'org', 'country', 'city', 'address', sep='\t')

    if arguments.url_lists_folder:
        process_url_lists(arguments.url_lists_folder)

    if arguments.ambig_domains_folder:
        process_ambig_domains_folder(arguments.ambig_domains_folder)

    if arguments.join_files:
        join_several_whois_answers(args.join_files[0], args.join_files[1])

    if arguments.add_geo_by_ip:
        print_geo_by_ip_info(arguments.add_geo_by_ip)

    # print(get_ip_by_domain_name('www.azatliq.org'))
    # print(get_location_by_ip('64.202.124.180'))
    # Test
    # w = whois.whois('belem.ru')
    # print(w.text)
    # print(w)
    # print(w.country, w.city, w.address)
    # print(w.creation_date, w.name, w.org)
    # print_whois_info('abq', read_files_to_list('../site/static/files/url_lists/abq_url_lists/url_type1.txt'))


def print_whois_info(lang, domainlist, start, counter):
    # some info about whois-fields: http://howtointernet.net/dnsrecords.html
    # and here: https://vdsinside.com/en/company/posts/working-with-whois-service.html
    for domain in domainlist:
        try:
            wh = whois.whois(domain.strip())
        except:
            print(lang, domain, 'unknown', 'unknown', 'unknown', 'unknown', sep='\t')
            continue
        # whois allows 30 queries a minute
        if counter == 30 and (datetime.now() - start).seconds < 60:
            time.sleep(36000 - (datetime.now() - start).seconds)
            start = datetime.now()
            counter = 0
        # print(wh)
        print(lang, domain, get_creation_date(wh), get_registrar(wh),
              get_registrant_name(wh), wh.org, get_addr(wh), sep='\t')
        counter += 1


def get_addr(wh):
    addr = list()
    addr.append(wh.country)
    addr.append(wh.city)
    addr.append(wh.address)
    return '\t'.join(str(v) for v in addr)


def get_creation_date(wh):
    if isinstance(wh.creation_date, list):
        # if whois returns two dates, the second is more precise
        return wh.creation_date[1]
    elif wh.creation_date:
        return wh.creation_date
    else:
        for date_item in re.findall('[Cc]reated( on)?:.*\n', wh.text):
            if date_item:
                return date_item.split(':')[1].strip()
            else:
                return None


def get_registrar(wh):
    if isinstance(wh.registrar, list):
        registrars = list()
        prev_reg = wh.registrar[0]
        registrars.append(prev_reg)
        for reg in wh.registrar:
            if reg.lower() == prev_reg.lower():
                continue
            else:
                prev_reg = reg
                registrars.append(reg)
        return ";".join(registrars)
    else:
        return wh.registrar


# name of person (if registrar is not organization)
def get_registrant_name(wh):
    if wh.name:
        return wh.name
    else:
        persons = list()
        for person_item in re.findall('person:.*\n', wh.text):
            person = person_item.split(':')[1].strip()
            persons.append(person)
        if persons:
            return ';'.join(persons)
        return None


def read_files_to_list(filename):
    with open(filename, 'r', encoding='utf-8') as fd:
        return [line.strip() for line in fd]


def read_amb_domain_file_to_dict(filename):
    resdict = defaultdict(list)
    with open(filename, 'r', encoding='utf-8') as fd:
        if os.path.basename(filename).startswith('multi'):
            fd.readline()
        for line in fd:
            parts = line.strip('\n').split('\t')
            langs = '_'.join(parts[1].split(';'))
            resdict[langs].append(parts[0])
    return resdict


def process_url_lists(dirname):
    start = datetime.now()
    counter = 0
    for url_list_dir in os.listdir(dirname):
        lang = url_list_dir.split('_', 1)[0]
        url_list_file = os.path.join(dirname, url_list_dir, 'url_type1.txt')
        if os.path.exists(url_list_file):
            url_list = read_files_to_list(url_list_file)
            # print(lang, url_list)
            print_whois_info(lang, url_list, start, counter)


def process_ambig_domains_folder(dirname):
    start = datetime.now()
    counter = 0
    for domain_file in glob(os.path.join(dirname, '*_domains_deb.tsv')):
        domain_dict = read_amb_domain_file_to_dict(domain_file)
        for langs, domains in domain_dict.items():
            # print(langs, domains)
            print_whois_info(langs, domains, start, counter)


def join_several_whois_answers(file1, file2):
    data1 = read_auxiliary_file(file1)
    data2 = read_auxiliary_file(file2)
    names = data1.dtype.names
    reslist = list()
    for row in data1:
        for row2 in data2:
            if row['domain'].decode('utf-8') == row2['domain'].decode('utf-8'):
                tmplst = list()
                for name in names:
                    if row[name].decode('utf-8') == 'None' and row2[name].decode('utf-8') != 'None':
                        tmplst.append(row2[name].decode('utf-8'))
                    elif row[name].decode('utf-8') != 'None':
                        tmplst.append(row[name].decode('utf-8'))
                    else:
                        tmplst.append(row[name].decode('utf-8'))
                reslist.append(tmplst)
    for l in reslist:
        print('\t'.join(l))


def read_domains_info_file_to_list(filename):
    domains_list = list()
    with open(filename, 'r', encoding='utf-8') as fd:
        for line in fd:
            parts = line.strip('\n').split('\t')
            domains_list.append(parts)
    return domains_list


def print_geo_by_ip_info(filename):
    domains_list = read_domains_info_file_to_list(filename)
    header = domains_list[0]
    header.extend(['ip', 'country_by_ip', 'city_by_ip'])
    print('\t'.join(header))
    counter = 0
    start = datetime.now()
    for el in domains_list[1:]:
        domain = el[1]
        ip = get_ip_by_domain_name(domain).strip('\n')
        if not ip:
            print('\t'.join(el + ['None', 'None', 'None']))
            continue
        # разрешено 150 запросов в минуту
        if counter == 140 and (datetime.now() - start).seconds < 60:
            time.sleep(60 - (datetime.now() - start).seconds)
            start = datetime.now()
            counter = 0
        country, city = get_location_by_ip(ip)
        counter += 1
        # country, city = ('', '')
        print('\t'.join(el + [ip, country, city]))


def get_ip_by_domain_name(domain_name):
    # dig www.buryatia.org | grep -oP 'A\t\d+.\d+.\d+.\d+' | cut -f2
    dig = subprocess.Popen(['dig', domain_name], stdout=subprocess.PIPE)
    grep = subprocess.Popen(['grep', '-o', '-P', "A\t\d+.\d+.\d+.\d+"],
                            stdin=dig.stdout, stdout=subprocess.PIPE)
    cut = subprocess.Popen(['cut', '-f', '2'], stdin=grep.stdout, stdout=subprocess.PIPE)
    ip_address = cut.stdout.read().decode('utf-8').split('\n')[0]
    return ip_address


def get_location_by_ip(ip):
    url = 'http://ip-api.com/json/%s' % ip
    response = request.urlopen(url).read().decode('utf-8')
    location = json.loads(response)
    location_country = location['country']
    location_city = location['city']
    return location_country, location_city


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", dest="url_lists_folder", required=False, action="store",
                        help="folder with url_lits: folder -> ady_url_lists, abq_url_lists")
    parser.add_argument("-a", dest="ambig_domains_folder", required=False, action="store",
                        help="folder with ambig urls and domains: ambig_domains"
                             " -> abkhadyg_domains_deb.tsv etc")
    parser.add_argument("-j", dest="join_files", required=False, metavar='FILE', nargs='*',
                        help="joins several tsv's after different runs")
    parser.add_argument('-g', dest="add_geo_by_ip", required=False, metavar='FILE',
                        help="adds geo info (country, city) by ip to info from the given file and prints to stdout")
    args = parser.parse_args()
    main(args)
