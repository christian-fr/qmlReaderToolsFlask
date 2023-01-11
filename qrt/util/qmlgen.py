import html
import pprint
import re
from pathlib import Path

from lxml.builder import ElementMaker  # lxml only !

ZOFAR_NS_URI = "http://www.his.de/zofar/xml/questionnaire"
NS = {"zofar": ZOFAR_NS_URI}

E = ElementMaker(namespace=ZOFAR_NS_URI, nsmap=NS)

PAGE = E.page
HEADER = E.header
MIS_HEADER = E.missingHeader
BODY = E.body
SECTION = E.section
UNIT = E.unit
QSC = E.questionSingleChoice
MC = E.multipleChoice
MMC = E.matrixMultipleChoice
MQSC = E.matrixQuestionSingleChoice
QO = E.questionOpen
ATTQO = E.attachedOpen
MQO = E.matrixQuestionOpen
RD = E.responseDomain
AO = E.answerOption
ITEM = E.item
TITLE = E.title
TEXT = E.text
INS = E.instruction
INT = E.introduction
QUE = E.question


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


if __name__ == '__main__':
    input_path = Path(r'C:\Users\friedrich\zofar_workspace\Nacaps2022-1\src\main\resources\questionnaire.xml')
    input_str = input_path.read_text(encoding='utf-8')
    unescaped_str = unescape_html(input_str)
    input_path.write_text(unescaped_str, encoding='utf-8')
    pass
