import json
from glob import glob
import os
import re
import argparse
from os.path import join
import sys
import statistics
import operator
from collections import defaultdict

sys.path.append('../')
from util import get_tokens, read_file_to_list


# Counts features for data analysis, using internet text collections
# same as here: http://web-corpora.net/minorlangs/download
# although with russian and trash text in the jsons

class LangFeatures(object):
    def __init__(self, lang, lang_dir, url_type1_file=None, aux_stats=None):
        self.lang = lang
        self.json_dir = lang_dir
        self.domains_file = url_type1_file
        self.aux_info = aux_stats
        # web-sites amount
        self.domains = list()
        # web-sites in lang amount
        self.type1_domains = list()
        # web-pages amount
        self.url_amount = 0
        # tokens in each lang (russian, minor lang, trash)
        self.tokens_amount = dict()
        # tokens per page - for token median feature
        self.tokens_per_page = dict()
        self.token_median = 0

        # All features in one dict
        self.features = dict()
        self.feature_list = list()

        # tokens, web-pages and tokens per pages per each lang and web-site separately
        self.site_urls = dict()
        self.site_tokens = dict()
        self.site_tokens_per_page = defaultdict(list)

    def parse_downloaded_jsons(self):
        self.features['lang'] = self.lang
        for filename in glob(join(self.json_dir, '*.json')):
            self.parse_file(filename)
        self.get_type1_domains()
        self.add_domain_and_url_info()
        self.add_tokens_info()
        self.count_word_median()

    def parse_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as infile:
            jsontext = ""
            last_processed_url = ""
            for line in infile:
                line = line.strip('\n')
                jsontext += line
                if line == "}":
                    try:
                        jsonpage = json.loads(jsontext, 'utf-8')
                    except ValueError:
                        print("Can't load file: ", self.lang, filename, last_processed_url, file=sys.stderr)
                        jsontext = ""
                        continue
                    domain = self.unify_domain(jsonpage['domain'])
                    # count only pages that have no less than one token in minor language
                    if self.is_good_page(jsonpage):
                        # count domains
                        if domain not in self.domains:
                            self.domains.append(domain)

                        # per site
                        self.site_urls[domain] = self.site_urls.get(domain, 0) + 1

                        # count urls
                        url = jsonpage['url']
                        last_processed_url = url
                        if url in self.tokens_per_page:
                            print("Дубль!", self.lang, url, file=sys.stderr)
                            jsontext = ""
                            continue
                        self.url_amount += 1
                        # print(self.lang, filename, url)
                        # do some calculation for each url
                        self.count_tokens_for_text(jsonpage)
                    jsontext = ""

    def count_tokens_for_text(self, jsonpage):
        """
        Tokenize each text on a web-page
        write to dict amount of tokens in each lang (russain, minor, trash)
        :param jsonpage: json-result from crawler of concrete web-page
        """
        texts = jsonpage['text']
        url = jsonpage['url']
        domain = self.unify_domain(jsonpage['domain'])
        for text_id in texts:
            try:
                text = texts[text_id]['text']
                lang = texts[text_id]['language']
            except:
                print(self.lang, url, text_id)
                continue
            tokens = get_tokens(text)
            if lang == self.lang:
                self.tokens_per_page[url] = self.tokens_per_page.get(url, 0) + len(tokens)
                self.site_tokens[domain] = self.site_tokens.get(domain, 0) + len(tokens)
            self.tokens_amount[lang] = self.tokens_amount.get(lang, 0) + len(tokens)
        self.site_tokens_per_page[domain].append(self.tokens_per_page[url])

    def get_type1_domains(self):
        type1_domains = list()
        if not self.domains_file:
            self.type1_domains = type1_domains
            self.features['type1_domains_found'] = 0
            return
        type1_domains_from_file = read_file_to_list(self.domains_file)
        type1_domains_from_file = [self.unify_domain(domain) for domain in type1_domains_from_file]
        for domain in self.domains:
            unified_domain = self.unify_domain(domain)
            if unified_domain in type1_domains_from_file and unified_domain not in type1_domains:
                type1_domains.append(unified_domain)
        self.type1_domains = type1_domains
        self.features['type1_domains_found'] = len(type1_domains_from_file)

    def unify_domain(self, domain):
        upd_domain = re.sub('^https?://', '', domain)
        return re.sub('www\.', '', upd_domain)

    def add_domain_and_url_info(self):
        type1_dom = len(self.type1_domains)
        all_dom = len(self.domains)
        self.features['type1_domains_crawled'] = type1_dom
        self.features['all_domains'] = all_dom
        self.features['type1_to_all'] = round(type1_dom / all_dom, 2)
        self.features['urls'] = self.url_amount

    def add_tokens_info(self):
        self.features['lang_tokens'] = self.tokens_amount[self.lang] if self.lang in self.tokens_amount else 0
        self.features['rus_tokens'] = self.tokens_amount['rus'] if 'rus' in self.tokens_amount else 0
        self.features['trash_tokens'] = self.tokens_amount['trash'] if 'trash' in self.tokens_amount else 0

    # есть ли слова на миноритарном языке или вся страница - треш
    @staticmethod
    def is_good_page(jsonpage):
        texts = jsonpage['text']
        for text_id in texts:
            if 'language' in texts[text_id] \
                    and texts[text_id]['language'] not in ['trash', 'rus']:
                return True
            if 'language' not in texts[text_id]:
                return None
        return False

    # token median per web-page
    def count_word_median(self):
        median = statistics.median(self.tokens_per_page.values())
        self.token_median = median
        self.features['token_median'] = median

    def print_features(self, with_header=False):
        sorted_feat = sorted(self.features.items(), key=operator.itemgetter(0))
        if with_header:
            print("\t".join(str(v[0]) for v in sorted_feat))
        print("\t".join(str(v[1]) for v in sorted_feat))

    def print_per_site(self):
        for domain in self.domains:
            token_median_per_site = statistics.median(self.site_tokens_per_page[domain])
            print(self.lang, domain, self.site_urls[domain],
                  self.site_tokens[domain], token_median_per_site, sep='\t', file=sys.stderr)


def main(arguments):
    if arguments.lang_folder:
        lang = os.path.basename(os.path.dirname(arguments.lang_folder))
        url_type1_file = os.path.join(arguments.url_list_folder, lang + '_url_lists', 'url_type1.txt')
        lang_feat = LangFeatures(lang, arguments.lang_folder, url_type1_file)
        lang_feat.parse_downloaded_jsons()
        lang_feat.print_per_site()
        lang_feat.print_features(True)

    if arguments.marked_folder:
        counter = 0
        marked_dir_path = arguments.marked_folder
        for lang_dir in os.listdir(marked_dir_path):
            indir = os.path.join(marked_dir_path, lang_dir)
            url_type1_file = os.path.join(arguments.url_list_folder, lang_dir + '_url_lists', 'url_type1.txt')
            if not os.path.exists(url_type1_file):
                url_type1_file = None
            lang_feat = LangFeatures(lang_dir, indir, url_type1_file)
            lang_feat.parse_downloaded_jsons()
            if counter < 1:
                lang_feat.print_features(True)
                counter += 1
            else:
                lang_feat.print_features()
            lang_feat.print_per_site()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", dest="lang_folder", required=False, action="store",
                        help="concrete folder with jsons (ady)")
    parser.add_argument("-m", dest="marked_folder", required=False,
                        action="store",
                        help="general folder with folders with langs with jsons: marked/ady/*.json")
    parser.add_argument("-u", dest="url_list_folder", required=True, action="store",
                        help="folder with url_lists, where we shall find url_type1.txt:"
                             " url_lists/<lang>_url_lists/url_type1.txt")
    args = parser.parse_args()
    main(args)
