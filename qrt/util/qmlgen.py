import html
import pprint
import re
from pathlib import Path
from typing import Dict, Union, List

from lxml.etree import tostring as l_tostring

from qrt.util.questionnaire import HeaderQuestion, HeaderTitle, HeaderInstruction, HeaderIntroduction, SCAnswerOption, \
    check_for_unique_uids, \
    MatrixResponseDomain, VarRef, Variable, VAR_TYPE_SC, VAR_TYPE_BOOL, SCMatrixItem, SCResponseDomain, \
    ZofarQuestionSCMatrix, \
    ZofarQuestionSC, HeaderObject, MCAnswerOption, ZofarQuestionOpen, VAR_TYPE_STR, SC_TYPE_DROPDOWN


def unescape_html(escaped_str: str) -> str:
    char_list = ['ä', 'Ä', 'ö', 'Ö', 'ü', 'Ü', 'ß']
    char_dict = {html.escape(char): char for char in char_list}
    special_chars = ["&amp;", "&lt;", "&gt;"]
    typo_quotes = ['&#8221;', '&#8220;', '&#8222;']
    list_of_escaped_chars = set(re.findall(r'&#?[a-z0-9A-Z]{,6};', escaped_str))
    dict_of_escaped_chars = {char: html.unescape(char) for char in list_of_escaped_chars if
                             char not in special_chars + typo_quotes}
    pprint.pprint(sorted(dict_of_escaped_chars))
    output_str = escaped_str
    for escaped_char, unescaped_char in dict_of_escaped_chars.items():
        output_str = output_str.replace(escaped_char, unescaped_char)
    return output_str


def create_headers(data_dict: Dict[str, Dict[str, str]]) -> List[HeaderObject]:
    header_list = []
    for i, header in data_dict.items():
        _dict = {'uid': header['uid'],
                 'visible': header['visible'] if header['visible'].strip() != "" else "true",
                 'content': header['text']}
        if header['type'] == 'question':
            header_list.append(HeaderQuestion(**_dict))
        elif header['type'] == 'introduction':
            header_list.append(HeaderIntroduction(**_dict))
        elif header['type'] == 'instruction':
            header_list.append(HeaderInstruction(**_dict))
    return header_list


def gen_qsc(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    header_list = create_headers(data_dict=data_dict['headers'])

    ao_list = [SCAnswerOption(uid=ao['uid'], value=ao['value'], label=ao['label'])
               for i, ao in sorted(data_dict['aos'].items(), key=lambda x: x[0])]

    assert check_for_unique_uids(header_list)
    assert check_for_unique_uids(ao_list)

    rd_dict = {'uid': 'rd',
               'var_ref': VarRef(variable=Variable(name=data_dict['q_variable'],
                                                   type=VAR_TYPE_SC)),
               'ao_list': ao_list}

    if 'rd_type' in data_dict:
        rd_dict.update({'rd_type': SC_TYPE_DROPDOWN})
    rd = SCResponseDomain(**rd_dict)

    qsc = ZofarQuestionSC(uid=data_dict['q_uid'], header_list=header_list, response_domain=rd,
                          visible=data_dict['q_visible'])

    return replace_zofar_ns(l_tostring(qsc.gen_xml(), pretty_print=True).decode('utf-8'))


def replace_zofar_ns(text: str) -> str:
    return text.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')


def gen_qo(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    pass


def gen_mc(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    header_list = create_headers(data_dict=data_dict['headers'])

    ao_list = []
    for i, ao in data_dict['aos'].items():
        ao_dict = {'uid': ao['uid'], 'label': ao['label'],
                   'var_ref': VarRef(variable=Variable(name=ao['variable'], type=VAR_TYPE_BOOL))}
        if 'exclusive' in ao:
            ao_dict.update({'exclusive': ao['exclusive']})
        if 'attached_open' in ao:
            attached_open_list = []
            # raise NotImplementedError
            for j, attached_open in ao['attached_open'].items():
                att_open_obj = ZofarQuestionOpen(uid="open",
                                                 var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
                attached_open_list.append(att_open_obj)
        ao_list.append(MCAnswerOption(**ao_dict))

    # ao_list = []
    # ao_list.append(MCAnswerOption(uid="ao1", label="Keine Zeit",
    #                               var_ref=VarRef(variable=Variable(name="ap09a", type=VAR_TYPE_BOOL))))
    # ao_list.append(MCAnswerOption(uid="ao2", label="Format gefällt nicht",
    #                               var_ref=VarRef(variable=Variable(name="ap09b", type=VAR_TYPE_BOOL))))
    # ao_list.append(MCAnswerOption(uid="ao3", label="Themen interessieren nicht",
    #                               var_ref=VarRef(variable=Variable(name="ap09c", type=VAR_TYPE_BOOL))))
    # ao_list.append(MCAnswerOption(uid="ao4", label="Keine Notwendigkeit",
    #                               var_ref=VarRef(variable=Variable(name="ap09d", type=VAR_TYPE_BOOL))))
    # ao_list.append(MCAnswerOption(uid="ao5", label=" Betreuer*in unterstützt Teilnahme nicht",
    #                               var_ref=VarRef(variable=Variable(name="ap09e", type=VAR_TYPE_BOOL))))
    # ao_list.append(MCAnswerOption(uid="ao6", label="Zu teuer",
    #                               var_ref=VarRef(variable=Variable(name="ap09f", type=VAR_TYPE_BOOL))))
    #
    # att_open =
    # ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
    #                               var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
    #                               attached_open_list=[att_open]))
    #
    # # integrity check: unique uids
    # assert check_for_unique_uids(ao_list)
    # assert check_for_unique_uids(header_list)
    #
    # rd = MCResponseDomain(ao_list=ao_list)
    #
    # mc = ZofarQuestionMC(uid="mce", header_list=header_list, response_domain=rd)

    raise NotImplementedError
    return mc


def gen_mqmc(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    pass


def gen_mqqo(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    pass


def unescape_characters(input_str: str) -> str:
    # umlaute etc. get automatically replaced by their html escape codes when being written by the parser
    # replace them back (remove html escapes and replace by non-ascii characters)
    matches = re.findall(r'(&#.{,5};)', input_str)
    matches_set = set(matches)
    if len(matches_set) > 0:
        print('\n' + f'The following characters will be replaced:')
        for match in matches_set:
            match_replacement = html.unescape(match)
            print(f'    {match=} -> {match_replacement}')
            input_str = input_str.replace(match, match_replacement)
    return input_str


def gen_mqsc(data_dict: Dict[str, Union[List, Dict, str]]) -> str:
    header_list = create_headers(data_dict['headers'])

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
                                 title_header=title_header_list, missing_header=title_missing_list,
                                 visible=data_dict['q_visible'])

    return replace_zofar_ns(l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8'))


if __name__ == '__main__':
    input_path = Path(r'C:\Users\friedrich\zofar_workspace\Nacaps2022-1\src\main\resources\questionnaire.xml')
    input_str = input_path.read_text(encoding='utf-8')
    unescaped_str = unescape_html(input_str)
    input_path.write_text(unescaped_str, encoding='utf-8')
    pass
