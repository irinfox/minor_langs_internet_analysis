# English version
# Minor langs internet analysis
The repository contains scripts and auxiliary files used in masters HSE work "Representation of minor languages of Russia on the Internet: quantitative
description and data analysis".

### Getting stats from downloaded minor langs internet collection
#### count_feautures.py

Counts and prints to stdout different stats about internet text collections: 
amount of all web-sites, amount of whole-downloaded web-sites, amount of web-pages, amount of tokens, token median per page,
whole-downloaded ratio to all web-sites

receives options:
-l - to process single folder with jsons
-m - to process all lang folders with jsons
-u - for folder with lists of whole-downloaded web-sites

For what it is all about, see repo of the project: https://bitbucket.org/LudaLuda/minorlangs/overview  (sorry, Russian).
Works with text collections similar to web-site collections: http://web-corpora.net/wsgi3/minorlangs/download

Calculated data with other data merged presented here: 
https://github.com/irinfox/minor_langs_internet_analysis/blob/master/data/langs_all_info_merged.tsv

### Getting and drawing domain registration info
#### get_org_and_date_for_domains.py

uses whois-api and ip-api to receive domains registration info
Perhaps, works only in linux systems

options:
-u - for list with web-sites and langs
-a - for list with ambigious web-sites and langs
-g - to add geo ip information to the whois-file

you can find all gathered whois information here: 
https://github.com/irinfox/minor_langs_internet_analysis/blob/master/data/domains_registration_info_with_ip.tsv

#### domain_registration_stats.py

drawing script for all registration stats info

### Getting hyperlinks information
#### get_links_info.py

Script works in two stages:
1. gets all links from all htmls and save them into json file
options -l or -w - to pass folders with htmls
outputs folder with json: links_from_htmls

2. gets all connections between different languages 
options -c (connection mode) and -u (files with url_types from web-site: http://web-corpora.net/wsgi3/minorlangs/download)
output:
* files with links info to tsv file (see https://github.com/irinfox/minor_langs_internet_analysis/blob/master/data/links_info.tsv)
* files with graph info to stdout (see https://github.com/irinfox/minor_langs_internet_analysis/blob/master/data/graph_info.txt)
* creates folder link_graphs with plenty of .dot files

NB! Implicitly uses langs_all_info_merged.tsv from data folder in this repo.

#### draw_all_grahs_with_dot.sh

Miniscript to draw all dot files saved from get_links_info.py.

### Auxiliary scripts
#### get_new_wiki_articles.py

Auxiliary scipt to parse Wikipedia page with table of wikipedias in all languages and all information about them

#### util.py

Script with some regularly used functions, such as file reading

## Ipython notebooks
There are two ipynb files with Russian comments for data analysis

#### internet_data_analysis.ipynb

includes data preparation, analysis of correlations, regression analysis and hierarchical clustering

#### token_median.ipynb

draws graphs for token median per page and scatter plot of token median per page and web-pages
includes comments in Russian


