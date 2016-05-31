import os
from sys import getsizeof, stderr
from collections import defaultdict, deque
from itertools import chain
import json
import re
import argparse
from operator import itemgetter
from bs4 import BeautifulSoup
from glob import glob
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
from networkx.drawing.nx_agraph import write_dot
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

SITE_ALIASES = {
    'chm.mari-centr.ru': 'mari-centr.ru',
    'old.tavan-en.ru': 'tavan-en.ru',
    'mariuverm.wordpress.com': 'mariuver.wordpress.com'
}


def main(arguments):
    if arguments.lang_folder:
        # path = '../../web_data/web'
        # lang_folder = 'mdf'
        # depends on ending with '/'
        path = os.path.dirname(os.path.dirname(arguments.lang_folder))
        lang_folder = os.path.basename(os.path.dirname(arguments.lang_folder))
        get_links_to_other_sites(path, lang_folder)

    if arguments.web_folder:
        parse_all_htmls(arguments.web_folder)

    if arguments.get_connections:
        lang_lang, lang_lang_dom = get_connections('links_from_htmls', True)

        for key, val in lang_lang.items():
            print(key, val, sep=' -- ')

        langs = list()
        for lang in lang_lang:
            langs.append(lang[0])
            langs.append(lang[1])

        dir_for_graphs = create_dir('link_graphs')

        # overall graph for langs
        draw_graph(list(set(langs)), lang_lang, dir_for_graphs)
        # process_links_seprately_and_draw_small_graphs(lang_lang, langs, dir_for_graphs)
        # graph for each lang and its national sites
        prepare_data_for_domain_graphs(lang_lang_dom, langs, dir_for_graphs)


# taken from https://code.activestate.com/recipes/577504/
def total_size(o, handlers=None, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    if handlers is None:
        handlers = {}
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    }
    all_handlers.update(handlers)  # user handlers take precedence
    seen = set()  # track which object id's have already been seen
    default_size = getsizeof(o)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


def get_links_to_other_sites(path, language):
    links_from_lang = defaultdict(dict)
    part = 0
    url_counter = 0
    for filename in glob(os.path.join(path, language, 'htmls', '*')):
        # print(filename)
        from_link = os.path.basename(filename).replace('_', '/')
        from_domain = '/'.join(from_link.split('/')[:3])

        # с именами файлов иногда бывает беда и выскакивает ошибка surrogates not allowed,
        #  которая проявляется только при печати. эта магия призвана сделать автозамену этих плохих символов
        try:
            print(from_link.encode('utf-8'), file=stderr)
        except UnicodeEncodeError:
            from_link = from_link.encode('utf8', 'replace').decode('utf-8')

        links_from_lang[from_domain][from_link] = dict()
        # print(lang, cur_domain, first_type_domains)
        with open(filename) as html_doc:
            try:
                soup = BeautifulSoup(html_doc, "lxml")
            # нужен конкретный эксепт
            except UnicodeDecodeError:
                with open(filename, encoding='iso-8859-1') as html_doc_upd:
                    soup = BeautifulSoup(html_doc_upd, "lxml")

            for link in soup.find_all('a'):
                cur_link = link.get('href')
                if cur_link and cur_link.startswith('http') and not cur_link.lower().startswith(from_domain):
                    cur_link_dom = '/'.join(cur_link.split('/')[:3])
                    if cur_link_dom not in links_from_lang[from_domain][from_link]:
                        links_from_lang[from_domain][from_link][cur_link_dom] = dict()
                    links_from_lang[from_domain][from_link][cur_link_dom][cur_link] = \
                        links_from_lang[from_domain][from_link][cur_link_dom].get(cur_link, 0) + 1
                    # print(cur_domain, cur_link)
                    # print(filename, link.get('href'))
        url_counter += 1

        # проверка размера - долгая операция, поэтому будем проверять каждые 2К файлов
        if url_counter >= 2000:
            if total_size(links_from_lang) / 1024 / 1024 >= 99:
                dump_links_from_lang(language, links_from_lang, part)
                links_from_lang = defaultdict(dict)
                part += 1
            url_counter = 0
    # оставшийся массив ссылок
    dump_links_from_lang(language, links_from_lang, part)
    return links_from_lang


def dump_links_from_lang(lang, js_file, part=0):
    resdir = create_dir('links_from_htmls')
    out_filename = os.path.join(resdir, lang + '_out_links' + '.{:03}.json'.format(part))
    with open(out_filename, 'w', encoding='utf-8') as fd:
        json.dump(js_file, fd, ensure_ascii=False, indent=4)
        fd.write('\n')
    return out_filename


def create_dir(dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname, mode=0o755)
    return dirname


def read_file_to_list(filename):
    with open(filename, 'r', encoding='utf-8') as fd:
        return [line.strip().replace('http://', '') for line in fd]


def parse_all_htmls(path):
    for lang_folder in os.listdir(path):
        print("Processing: ", lang_folder)
        links_from_lang = get_links_to_other_sites(path, lang_folder)
        dump_links_from_lang(lang_folder, links_from_lang)


def unify_domain(domain):
    upd_domain = re.sub('^https?://', '', domain)
    upd_domain = SITE_ALIASES[upd_domain] if upd_domain in SITE_ALIASES else upd_domain
    return re.sub('www\.', '', upd_domain)


def get_lang_sites():
    url_list_folder = '../site/static/files/url_lists'
    lang_sites = dict()
    for lang_dir in os.listdir(url_list_folder):
        if lang_dir.endswith('.zip'):
            continue
        language = lang_dir.split('_')[0]
        url_list_path = os.path.join(url_list_folder, lang_dir, 'url_type1.txt')

        if os.path.exists(url_list_path):
            with open(url_list_path) as fd:
                lang_sites[language] = [unify_domain(line.strip()) for line in fd]
        else:
            lang_sites[language] = []
    return lang_sites


# теперь будет работать с json и его надо переписать
def get_connections(dirname, debug_to_file=False):
    lang_lang_connection = dict()
    lang_lang_with_domains = defaultdict(list)
    code_lang_mapping, lang_code = get_code_lang_mapping('../aux_files/langs_all_info.csv')
    for filename in glob(os.path.join(dirname, '*.json')):
        lang = os.path.basename(filename).split('_')[0]
        lang_site_dict = get_lang_sites()
        with open(filename) as fd:
            lang_dict = dict()
            try:
                lang_dict = json.load(fd)
            except ValueError as e:
                print(e)
                print(filename)
                exit(1)
            for from_domain, dom_dict in lang_dict.items():
                from_domain = unify_domain(from_domain)
                if from_domain not in lang_site_dict[lang]:
                    continue
                # print(lang, 'from domain in list', from_domain)
                # for from_link, to_dict in dom_dict.items():
                to_domains = list()
                for to_dict in dom_dict.values():
                    # for to_domain, to_link in to_dict.items():
                    to_domains.extend([unify_domain(dom) for dom in to_dict.keys()])
                for to_domain in list(set(to_domains)):
                    for lang2, lang_list in lang_site_dict.items():
                        if to_domain in lang_list \
                                and from_domain != to_domain:
                            # print('\t', lang2, 'to domain in list', to_domain)
                            mapped_lang = code_lang_mapping[lang]
                            mapped_lang2 = code_lang_mapping[lang2]
                            if (from_domain, to_domain) in lang_lang_with_domains[(mapped_lang, mapped_lang2)]:
                                continue
                            lang_lang_with_domains[(mapped_lang, mapped_lang2)].append((from_domain, to_domain))
                            lang_lang_connection[(mapped_lang, mapped_lang2)] = lang_lang_connection.get(
                                (mapped_lang, mapped_lang2), 0) + 1
    if debug_to_file:
        with open('links_info.tsv', 'w', encoding='utf-8') as fd:
            fd.write('\t'.join(['-->'.join(['Язык', 'Язык']), 'количество ссылок',
                                'С домена', 'На домен']) + '\n')
            for langs, domains in sorted(lang_lang_with_domains.items()):
                fd.write('\t'.join(['-->'.join(langs), str(len(domains))]) + '\n')
                for domain_pair in domains:
                    fd.write('\t\t')
                    fd.write('\t'.join(domain_pair) + '\n')
    return lang_lang_connection, lang_lang_with_domains


def get_code_lang_mapping(lang_info_file):
    with open(lang_info_file, encoding="utf-8") as fd:
        text = fd.read()

    # воспринимает их как комментарии и выдаёт ошибку по кол-ву столбцов
    newtext = text.replace('#', '@')
    lang_info_data = np.genfromtxt(BytesIO(newtext.encode('utf-8')), names=True,
                                   delimiter='\t', dtype=None)
    lang_code = dict()
    code_lang = dict()
    for row in lang_info_data:
        language = row['language'].decode('utf-8')
        code = row['iso_code'].decode('utf-8')
        code_lang[code] = language
        lang_code[language] = code
    return code_lang, lang_code


def draw_graph(nodes, edges, graphs_dir, default_lang='all'):
    lang_graph = nx.MultiDiGraph()
    lang_graph.add_nodes_from(nodes)
    for edge in edges:
        if edges[edge] == 0:
            lang_graph.add_edge(edge[0], edge[1])
        else:
            lang_graph.add_edge(edge[0], edge[1], weight=float(edges[edge]), label=str(edges[edge]))

    # print graph info in stdout
    # коэффициент центральности
    print('-----------------\n\n')
    print(default_lang)
    print(nx.info(lang_graph))
    try:
        # When ties are associated to some positive aspects such as friendship or collaboration,
        #  indegree is often interpreted as a form of popularity, and outdegree as gregariousness.
        DC = nx.degree_centrality(lang_graph)
        max_dc = max(DC.values())
        max_dc_list = [item for item in DC.items() if item[1] == max_dc]
    except ZeroDivisionError:
        max_dc_list = []
    # https://ru.wikipedia.org/wiki/%D0%9A%D0%BE%D0%BC%D0%BF%D0%BB%D0%B5%D0%BA%D1%81%D0%BD%D1%8B%D0%B5_%D1%81%D0%B5%D1%82%D0%B8
    print('maxdc', str(max_dc_list), sep=': ')
    # коэффициент ассортативности - как связаны "звёзды"
    AC = nx.degree_assortativity_coefficient(lang_graph)
    print('AC', str(AC), sep=': ')
    if nx.is_strongly_connected(lang_graph):
        # максимальное расстояние между вершинами для всех пар вершин
        print('диаметр: ', nx.diameter(lang_graph))
        # минимальное максимальное расстояние между вершинами для всех пар вершин
        print('радиус: ', nx.radius(lang_graph))
    # про связность
    print("Слабо-связный граф: ", nx.is_weakly_connected(lang_graph))
    print("количество слабосвязанных компонент: ", nx.number_weakly_connected_components(lang_graph))
    print("Сильно-связный граф: ", nx.is_strongly_connected(lang_graph))
    print("количество сильносвязанных компонент: ", nx.number_strongly_connected_components(lang_graph))
    print("рекурсивные? компоненты: ", nx.number_attracting_components(lang_graph))
    # наименьшее число вершин, удаление которых приводит к несвязному или тривиальному графу.
    print("число вершинной связности: ", nx.node_connectivity(lang_graph))
    # наименьшее количество ребер, удаление которых приводит к несвязному или тривиальному графу.
    print("число рёберной связности: ", nx.edge_connectivity(lang_graph))
    # other info
    print("average degree connectivity: ", nx.average_degree_connectivity(lang_graph))
    print("average neighbor degree: ", sorted(nx.average_neighbor_degree(lang_graph).items(),
                                              key=itemgetter(1), reverse=True))
    # best for small graphs, and our graphs are pretty small
    print("pagerank: ", sorted(nx.pagerank_numpy(lang_graph).items(), key=itemgetter(1), reverse=True))

    plt.figure(figsize=(16.0, 9.0), dpi=80)
    plt.axis('off')
    pos = graphviz_layout(lang_graph)
    nx.draw_networkx_edges(lang_graph, pos, alpha=0.5, arrows=True)
    nx.draw_networkx(lang_graph, pos, node_size=1000, font_size=12, with_labels=True, node_color='green')
    nx.draw_networkx_edge_labels(lang_graph, pos, edges)

    # saving file to draw it with dot-graphviz
    # changing overall graph view, default is top-bottom
    lang_graph.graph['graph'] = {'rankdir': 'LR'}
    # marking with blue nodes with maximum degree centrality
    for max_dc_node in max_dc_list:
        lang_graph.node[max_dc_node[0]]['fontcolor'] = 'blue'
    write_dot(lang_graph, os.path.join(graphs_dir, default_lang + '_links.dot'))

    # plt.show()
    plt.savefig(os.path.join(graphs_dir, 'python_' + default_lang + '_graph.png'), dpi=100)
    plt.close()


def domain_graphs_with_subgraphs(nodes, edges, subgraphs, graphs_dir, language):
    domain_graph = nx.MultiDiGraph()
    domain_graph.add_nodes_from(nodes)
    for edge in edges:
        domain_graph.add_edge(edge[0], edge[1], weight=float(edges[edge]), label=str(edges[edge]))

    for lang, nodelist in subgraphs:
        domain_graph.subgraph(nodelist, name=lang)
        # subgr.name = lang

    # saving file to draw it with dot-graphviz
    # changing overall graph view, default is top-bottom
    domain_graph.graph['graph'] = {'rankdir': 'LR'}
    write_dot(domain_graph, os.path.join(graphs_dir, 'domains_' + language + '_links.dot'))


def process_links_seprately_and_draw_small_graphs(lang_to_lang_dict, langs, graphs_dir):
    lang_graph = defaultdict(dict)
    for language in langs:
        lang_graph[language]['edges'] = dict()
        lang_graph[language]['nodes'] = set()
        for lang_tuple, weight in lang_to_lang_dict.items():
            if language in lang_tuple:
                lang_graph[language]['edges'][lang_tuple] = weight
                lang_graph[language]['nodes'].add(lang_tuple[0])
                lang_graph[language]['nodes'].add(lang_tuple[1])

    code_lang, lang_code = get_code_lang_mapping('../aux_files/langs_all_info.csv')
    for language, graph_data in lang_graph.items():
        draw_graph(graph_data['nodes'], graph_data['edges'], graphs_dir, lang_code[language])


def prepare_data_for_domain_graphs(lang_to_lang_with_domains, langs, graphs_dir):
    domain_graph = defaultdict(dict)
    for language in langs:
        domain_graph[language]['edges'] = dict()
        domain_graph[language]['nodes'] = set()
        for lang_tuple, domain_tuples in lang_to_lang_with_domains.items():
            if language in lang_tuple and lang_tuple[0] == lang_tuple[1]:
                for domain_tuple in domain_tuples:
                    domain_graph[language]['edges'][domain_tuple] = 0
                    domain_graph[language]['nodes'].add(domain_tuple[0])
                    domain_graph[language]['nodes'].add(domain_tuple[1])

    code_lang, lang_code = get_code_lang_mapping('../aux_files/langs_all_info.csv')
    for language, graph_data in domain_graph.items():
        if graph_data['nodes']:
            draw_graph(graph_data['nodes'], graph_data['edges'], graphs_dir, lang_code[language])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", dest="lang_folder", required=False, action="store",
                        help="concrete folder with htmls (ady)")
    parser.add_argument("-w", dest="web_folder", required=False,
                        action="store",
                        help="general folder with folders with langs with jsons: web/ady/htmls/*")
    parser.add_argument("-c", dest='get_connections', required=False, action="store_true",
                        help="get connections, draw graphs and save them to folder link_graphs")
    args = parser.parse_args()
    main(args)
