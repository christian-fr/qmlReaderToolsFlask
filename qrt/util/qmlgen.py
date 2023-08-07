import html
import pprint
import re
from pathlib import Path
from typing import Dict, Union, List

from lxml.etree import _Element as _lE, ElementTree as lEt, tostring as l_to_string

from qrt.util.questionnaire import HeaderQuestion, HeaderTitle, HeaderInstruction, HeaderIntroduction, SCAnswerOption, \
    check_for_unique_uids, \
    MatrixResponseDomain, VarRef, Variable, VAR_TYPE_SC, VAR_TYPE_BOOL, SCMatrixItem, SCResponseDomain, \
    ZofarQuestionSCMatrix, \
    ZofarQuestionSC, HeaderObject, MCAnswerOption, ZofarQuestionOpen, VAR_TYPE_STR, SC_TYPE_DROPDOWN, MCResponseDomain, \
    ZofarQuestionMC, MCMatrixItem, ZofarQuestionMCMatrix


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


def example_qsc_edit():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Kennen Sie PoGS-Weiterbildungsangebote für Promovierende (z.B. Programme und Workshops)?")]

    ao_list = []
    ao_list.append(SCAnswerOption(uid="ao1", value="1", label="Ja."))
    ao_list.append(SCAnswerOption(uid="ao2", value="2", label="Nein."))
    ao_list.append(SCAnswerOption(uid="ao3", value="3", label="Weiß ich nicht."))

    var_ref1 = VarRef(variable=Variable(name="ap06", type=VAR_TYPE_SC))
    rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

    qsc = ZofarQuestionSC(uid="qsc1f", header_list=header_list, response_domain=rd)

    return qsc


def example_mc_edit():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Aus welchem Grund haben Sie (bisher) keine Weiterbildungsangebote der Potsdam Graduate School besucht?"),
                   HeaderInstruction(uid="ins1",
                                     content="Bitte wählen Sie alles Zutreffende aus.")]

    ao_list = []
    ao_list.append(MCAnswerOption(uid="ao1", label="Keine Zeit",
                                  var_ref=VarRef(variable=Variable(name="ap09a", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao2", label="Format gefällt nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09b", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao3", label="Themen interessieren nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09c", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao4", label="Keine Notwendigkeit",
                                  var_ref=VarRef(variable=Variable(name="ap09d", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao5", label=" Betreuer*in unterstützt Teilnahme nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09e", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao6", label="Zu teuer",
                                  var_ref=VarRef(variable=Variable(name="ap09f", type=VAR_TYPE_BOOL))))

    att_open = ZofarQuestionOpen(uid="open", var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
    ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
                                  var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
                                  attached_open_list=[att_open]))

    # integrity check: unique uids
    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    rd = MCResponseDomain(ao_list=ao_list)

    mc = ZofarQuestionMC(uid="mce", header_list=header_list, response_domain=rd)

    return mc


def example_mc_1():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Welche Kanäle haben Sie im Zuge Ihrer Informationssuche zum Promovieren an der Universität Potsdam genutzt?"),
                   HeaderInstruction(uid="ins1",
                                     content="Bitte wählen Sie alles Zutreffende aus.")]

    att_open = ZofarQuestionOpen(uid="open1", var_ref=VarRef(variable=Variable(name="ap02g", type=VAR_TYPE_STR)))

    ao_list = []
    ao_list.append(MCAnswerOption(uid="ao1", label="Webseite",
                                  var_ref=VarRef(variable=Variable(name="ap02a", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao2", label="Flyer/Broschüre",
                                  var_ref=VarRef(variable=Variable(name="ap02b", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao3", label="Info-Veranstaltung",
                                  var_ref=VarRef(variable=Variable(name="ap02c", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao4", label="Beratungsgespräch",
                                  var_ref=VarRef(variable=Variable(name="ap02d", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao5", label="Gespräch mit anderen Wissenschaftler*innen",
                                  var_ref=VarRef(variable=Variable(name="ap02e", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao6", label="Sonstige, und zwar:",
                                  var_ref=VarRef(variable=Variable(name="ap02f", type=VAR_TYPE_BOOL)),
                                  attached_open_list=[att_open]))

    # integrity check: unique uids
    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    rd = MCResponseDomain(ao_list=ao_list)

    qsc = ZofarQuestionMC(uid="qsc1d", header_list=header_list, response_domain=rd)

    return qsc


def example_mqsc():
    header_list = [HeaderQuestion(uid="q1", content="Was halten Ihre Eltern und Ihre Freunde von Ihrem Studienfach?")]
    header_list_it = [
        HeaderQuestion(uid="q1", content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")]

    title_header_list = []
    title_header_list.append(HeaderTitle(uid="ti1", content="trifft völlig zu"))
    title_header_list.append(HeaderTitle(uid="ti2", content="trifft eher zu"))
    title_header_list.append(HeaderTitle(uid="ti3", content="teils / teils"))
    title_header_list.append(HeaderTitle(uid="ti4", content="trifft eher nicht zu"))
    title_header_list.append(HeaderTitle(uid="ti5", content="trifft gar nicht zu"))

    title_missing_list = []

    ao_list_it = []
    ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label="trifft völlig zu"))
    ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label="trifft eher zu"))
    ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label="teils / teils"))
    ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label="trifft eher nicht zu"))
    ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label="trifft gar nicht zu", missing=True))

    assert check_for_unique_uids(ao_list_it)
    assert check_for_unique_uids(title_header_list)
    assert check_for_unique_uids(title_missing_list)
    assert check_for_unique_uids(header_list)

    matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

    it_list = []

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it1 = SCMatrixItem(uid="it1",
                       header_list=[HeaderQuestion(uid="q1",
                                                   content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")],
                       response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
    it_list.append(it1)

    var_ref2 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it2 = SCMatrixItem(uid="it2",
                       header_list=[HeaderQuestion(uid="q1",
                                                   content="Meine Freundinnen und Freunde finden, dass ich ein gutes Studienfach gewählt habe.")],
                       response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
    it_list.append(it2)

    matrix_rd.item_list = it_list

    mqsc = ZofarQuestionSCMatrix(uid='msca', header_list=header_list, response_domain=matrix_rd,
                                 title_header=title_header_list, missing_header=title_missing_list)
    return mqsc


def example_mqmc():
    header_list = [HeaderQuestion(uid="q1", content="Was halten Ihre Eltern und Ihre Freunde von Ihrem Studienfach?")]
    header_list_it = [
        HeaderQuestion(uid="q1", content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")]

    title_header_list = []
    title_header_list.append(HeaderTitle(uid="ti1", content="trifft völlig zu"))
    title_header_list.append(HeaderTitle(uid="ti2", content="trifft eher zu"))
    title_header_list.append(HeaderTitle(uid="ti3", content="teils / teils"))
    title_header_list.append(HeaderTitle(uid="ti4", content="trifft eher nicht zu"))
    title_header_list.append(HeaderTitle(uid="ti5", content="trifft gar nicht zu"))

    ao_list_it1 = []
    ao_list_it1.append(MCAnswerOption(uid='ao1', var_ref=VarRef(variable=Variable(name="var01a", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it1.append(MCAnswerOption(uid='ao2', var_ref=VarRef(variable=Variable(name="var01b", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it1.append(MCAnswerOption(uid='ao3', var_ref=VarRef(variable=Variable(name="var01c", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it1.append(MCAnswerOption(uid='ao4', var_ref=VarRef(variable=Variable(name="var01d", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it1.append(MCAnswerOption(uid='ao5', var_ref=VarRef(variable=Variable(name="var01e", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu", missing=True))

    ao_list_it2 = []
    ao_list_it2.append(MCAnswerOption(uid='ao1', var_ref=VarRef(variable=Variable(name="var02a", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it2.append(MCAnswerOption(uid='ao2', var_ref=VarRef(variable=Variable(name="var02b", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it2.append(MCAnswerOption(uid='ao3', var_ref=VarRef(variable=Variable(name="var02c", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it2.append(MCAnswerOption(uid='ao4', var_ref=VarRef(variable=Variable(name="var02d", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu"))
    ao_list_it2.append(MCAnswerOption(uid='ao5', var_ref=VarRef(variable=Variable(name="var02e", type=VAR_TYPE_BOOL)),
                                      label="trifft völlig zu", missing=True))

    title_missing_list = []

    assert check_for_unique_uids(ao_list_it1)
    assert check_for_unique_uids(ao_list_it2)
    assert check_for_unique_uids(title_header_list)
    assert check_for_unique_uids(title_missing_list)
    assert check_for_unique_uids(header_list)

    matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it1)))

    it_list = []

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it1 = MCMatrixItem(uid="it1",
                       header_list=[HeaderQuestion(uid="q1",
                                                   content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")],
                       response_domain=MCResponseDomain(uid="rd", ao_list=ao_list_it1))
    # ToDo: Multiple Choice Response Domain works differently from SC!
    it_list.append(it1)

    var_ref2 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it2 = MCMatrixItem(uid="it2",
                       header_list=[HeaderQuestion(uid="q1",
                                                   content="Meine Freundinnen und Freunde finden, dass ich ein gutes Studienfach gewählt habe.")],
                       response_domain=MCResponseDomain(uid="rd", ao_list=ao_list_it2))
    it_list.append(it2)

    matrix_rd.item_list = it_list

    mqmc = ZofarQuestionMCMatrix(uid='mscb', header_list=header_list, response_domain=matrix_rd,
                                 title_header=title_header_list, missing_header=title_missing_list)
    return mqmc


def example_qsc_1():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Haben Sie sich an der Universität Potsdam vor Beginn Ihrer Promotion zum Thema Promovieren informiert?")]

    ao_list = []
    ao_list.append(SCAnswerOption(uid="ao1", value="1", label="Ja."))
    ao_list.append(SCAnswerOption(uid="ao2", value="2", label="Nein."))

    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

    qsc = ZofarQuestionSC(uid="qsc1c", header_list=header_list, response_domain=rd)

    return qsc


def example_oq():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Kennen Sie PoGS-Weiterbildungsangebote für Promovierende (z.B. Programme und Workshops)?")]
    qo = ZofarQuestionOpen(uid="qo1g", header_list=header_list,
                           var_ref=VarRef(variable=Variable(name="ap08", type=VAR_TYPE_STR)))
    return qo


if __name__ == '__main__':
    q_list = []
    q_list.append(example_qsc_1())
    q_list.append(example_qsc_edit())
    q_list.append(example_mc_1())
    q_list.append(example_mc_edit())
    q_list.append(example_mqsc())
    q_list.append(example_mqmc())
    q_list.append(example_oq())

    qml_str = '\n'.join(
        [l_to_string(question.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8') for question in q_list])
    pass
    z = qml_str.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    pass
