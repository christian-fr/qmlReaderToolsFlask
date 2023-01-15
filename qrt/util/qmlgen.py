import html
import pprint
import re
from pathlib import Path
from typing import Dict, Union, List

from lxml.etree import tostring as l_tostring

from qrt.util.questionnaire import HeaderQuestion, HeaderTitle, HeaderInstruction, HeaderIntroduction, SCAnswerOption, \
    check_for_unique_uids, \
    MatrixResponseDomain, VarRef, Variable, VAR_TYPE_SC, SCMatrixItem, SCResponseDomain, ZofarQuestionSCMatrix


def unescape_html(input_str: str) -> str:
    char_list = ['ä', 'Ä', 'ö', 'Ö', 'ü', 'Ü', 'ß']
    char_dict = {html.escape(char): char for char in char_list}
    special_chars = ["&amp;", "&lt;", "&gt;"]
    typo_quotes = ['&#8221;', '&#8220;', '&#8222;']
    list_of_escaped_chars = set(re.findall(r'&#?[a-z0-9A-Z]{,6};', input_str))
    dict_of_escaped_chars = {char: html.unescape(char) for char in list_of_escaped_chars if
                             char not in special_chars + typo_quotes}
    pprint.pprint(sorted(dict_of_escaped_chars))
    output_str = input_str
    for escaped_char, unescaped_char in dict_of_escaped_chars.items():
        output_str = output_str.replace(escaped_char, unescaped_char)
    return output_str


def gen_mqsc(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    header_list = []
    for i, header in data_dict['headers'].items():
        _dict = {'uid': header['uid'],
                 'visible': header['visible'] if header['visible'].strip() != "" else "true",
                 'content': header['text']}
        if header['type'] == 'question':
            header_list.append(HeaderQuestion(**_dict))
        elif header['type'] == 'introduction':
            header_list.append(HeaderIntroduction(**_dict))
        elif header['type'] == 'instruction':
            header_list.append(HeaderInstruction(**_dict))

    title_header_list = []
    ao_list_it = []

    title_missing_list = []
    for i, ao in data_dict['aos'].items():
        # set answer option object
        ao_list_it.append(SCAnswerOption(uid=ao['uid'], value=ao['value'], label=ao['label']))

        # set title header according to answer option label
        if 'missing' in ao:
            if ao['missing'] == 'on':
                # if answer option marked as missing -> add to missing header
                title_missing_list.append(HeaderTitle(uid=f'ti{i}', content=ao['label'], visible=ao['visible']))
                continue
        # if else -> add to regular title
        title_header_list.append(HeaderTitle(uid=ao['uid'], content=ao['label'], visible=ao['visible']))


    it_list = []

    for j, it in data_dict['items'].items():
        var_ref = VarRef(variable=Variable(name=it['variable'], type=VAR_TYPE_SC))
        it_element = SCMatrixItem(uid=it['uid'],
                                  header_list=[HeaderQuestion(uid=f"q{j}",
                                                              content=it['text'])],
                                  response_domain=SCResponseDomain(uid=f"rd{j}", ao_list=ao_list_it, var_ref=var_ref))
        it_list.append(it_element)


    assert check_for_unique_uids(header_list)
    assert check_for_unique_uids(title_header_list)
    assert check_for_unique_uids(title_missing_list)
    assert check_for_unique_uids(title_header_list + title_missing_list)
    assert check_for_unique_uids(ao_list_it)
    assert check_for_unique_uids(it_list)

    matrix_rd = MatrixResponseDomain(uid='rd', no_response_options=str(len(ao_list_it)), item_list=it_list)

    mqsc = ZofarQuestionSCMatrix(uid=data_dict['q_uid'], header_list=header_list, response_domain=matrix_rd,
                                 title_header=title_header_list, missing_header=title_missing_list)

    y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

    return z


if __name__ == '__main__':
    input_path = Path(r'C:\Users\friedrich\zofar_workspace\Nacaps2022-1\src\main\resources\questionnaire.xml')
    input_str = input_path.read_text(encoding='utf-8')
    unescaped_str = unescape_html(input_str)
    input_path.write_text(unescaped_str, encoding='utf-8')
    pass
