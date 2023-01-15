import html
import pprint
import re
from pathlib import Path
from typing import Dict, Union, List

from lxml.etree import tostring as l_tostring

from qrt.util.questionnaire import HeaderQuestion, HeaderTitle, SCAnswerOption, check_for_unique_uids, \
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
        if header['type'] == 'question':
            pass
        elif header['type'] == 'introduction':
            pass
        elif header['type'] == 'instruction':
            pass

    title_header_list = []
    title_missing_list = []
    for i, ao in data_dict['aos'].items():
        if 'missing' in ao:
            if ao['missing'] == 'on':
                title_missing_list.append(HeaderTitle(uid=ao['uid'], content=ao['label'], visible=ao['visible']))
                continue
        title_header_list.append(HeaderTitle(uid=ao['uid'], content=ao['label'], visible=ao['visible']))

    header_list = [
        HeaderQuestion(uid="q",
                       content="""Wie wichtig sind Ihnen die folgenden Rollen Ihrer Betreuungsperson(en)?""")
    ]
    # header_list_it = [
    #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

    title_header_list = []
    title_header_list.append(HeaderTitle(uid="ti1", content="unwichtig"))
    title_header_list.append(HeaderTitle(uid="ti2", content=""))
    title_header_list.append(HeaderTitle(uid="ti3", content=""))
    title_header_list.append(HeaderTitle(uid="ti4", content=""))
    title_header_list.append(HeaderTitle(uid="ti5", content="sehr wichtig"))

    title_missing_list = []
    # title_missing_list.append(HeaderTitle(uid="ti5", content="sehr zufrieden"))

    ao_list_it = []
    ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label=title_header_list[len(ao_list_it)].content))
    ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label=title_header_list[len(ao_list_it)].content))
    ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label=title_header_list[len(ao_list_it)].content))
    ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label=title_header_list[len(ao_list_it)].content))
    ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label=title_header_list[len(ao_list_it)].content))

    # ao_list_it.append(SCAnswerOption(uid='ao6', value="6", label=title_missing_list[0].content, missing=True))

    # assert len(title_header_list) == len(ao_list_it)

    assert check_for_unique_uids(ao_list_it)
    assert check_for_unique_uids(title_header_list)
    assert check_for_unique_uids(title_missing_list)
    assert check_for_unique_uids(header_list)

    matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

    it_list = []

    var_ref1 = VarRef(variable=Variable(name="axi09a", type=VAR_TYPE_SC))
    it1 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                       header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                   content="Karriereberater*in")],
                       response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
    it_list.append(it1)

    var_ref2 = VarRef(variable=Variable(name="axi09b", type=VAR_TYPE_SC))
    it2 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                       header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                   content="Networker*in")],
                       response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
    it_list.append(it2)

    var_ref3 = VarRef(variable=Variable(name="axi09c", type=VAR_TYPE_SC))
    it3 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                       header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                   content="Fachlicher Beirat")],
                       response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref3))
    it_list.append(it3)

    # var_ref4 = VarRef(variable=Variable(name="ap03d", type=VAR_TYPE_SC))
    # it4 = SCMatrixItem(uid="it4",
    #                    header_list=[HeaderQuestion(uid="q1",
    #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
    #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref4))
    # it_list.append(it4)
    #
    # var_ref5 = VarRef(variable=Variable(name="ap03e", type=VAR_TYPE_SC))
    # it4 = SCMatrixItem(uid="it5",
    #                    header_list=[HeaderQuestion(uid="q1",
    #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
    #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref5))
    # it_list.append(it4)
    #
    # var_ref6 = VarRef(variable=Variable(name="ap03f", type=VAR_TYPE_SC))
    # att_open = ZofarAttachedOpen(uid='open1', var_ref=VarRef(variable=Variable(name="ap03g", type=VAR_TYPE_STR)))
    # it4 = SCMatrixItem(uid="it6",
    #                    header_list=[HeaderQuestion(uid="q1",
    #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
    #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref6),
    #                    attached_open_list=[att_open])
    # it_list.append(it4)

    matrix_rd.item_list = it_list

    mqsc = ZofarQuestionSCMatrix(uid='mqsc1', header_list=header_list, response_domain=matrix_rd,
                                 title_header=title_header_list, missing_header=title_missing_list)

    y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

    # z = mqsc_example_str
    return z


if __name__ == '__main__':
    input_path = Path(r'C:\Users\friedrich\zofar_workspace\Nacaps2022-1\src\main\resources\questionnaire.xml')
    input_str = input_path.read_text(encoding='utf-8')
    unescaped_str = unescape_html(input_str)
    input_path.write_text(unescaped_str, encoding='utf-8')
    pass
