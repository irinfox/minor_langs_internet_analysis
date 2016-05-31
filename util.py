import os
import re
import string
import numpy as np
from io import BytesIO


tkn_split = re.compile('(([\w-]+)|([\d]+)|[^\w_]|[+]|[*])', re.U)
punct = u"1!«»?.,…()\"<>[]|_\/${}-–+=;:¤_~'023456789*%@—qwertyuioplkjhgfdsazxcvbnm"


def get_tokens(text):
    """
    tokenization
    """
    token_list = list()
    for m in tkn_split.finditer(text):
        if m and not m.group().isspace():
            token = m.group()
            if token in string.punctuation or token in punct:
                continue
            # exclude most emoticons
            if (len(token) < 2 and ((127744 <= ord(token) < 128592) or
                                        (2600 <= ord(token) < 9983))):
                continue
            token_list.append(token)
    return token_list


def read_file_to_list(filename):
    reslist = list()
    with open(filename, 'r', encoding='utf-8') as infile:
        for line in infile:
            line = line.strip('\n')
            reslist.append(line)
    return reslist


# tsv reader with numpy
def read_auxiliary_file(aux_stat_file):
    with open(aux_stat_file, encoding="utf-8") as fd:
        text = fd.read()

    newtext = text.replace('#', '@')
    data = np.genfromtxt(BytesIO(newtext.encode('utf-8')), names=True,
                         delimiter='\t', dtype=None)
    return data


def create_dir(dirname):
    """
    Function to create any directory inside working dir
    given the name of dir
    :param dirname: name of dir
    :return: name of created dir
    """
    if not os.path.isdir(dirname):
        os.mkdir(dirname, mode=0o755)
    return dirname
