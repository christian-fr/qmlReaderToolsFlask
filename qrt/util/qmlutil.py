import re

from lxml.builder import ElementMaker


def flatten(ll):
    """
    Flattens given list of lists by one level

    :param ll: list of lists
    :return: flattened list
    """
    return [it for li in ll for it in li]


ZOFAR_NS = "{http://www.his.de/zofar/xml/questionnaire}"
ZOFAR_NS_URI = "http://www.his.de/zofar/xml/questionnaire"
NS = {
    "xmlns:zofar": ZOFAR_NS_URI,
    "zofar": ZOFAR_NS_URI
}
ZOFAR_QUESTIONNAIRE_TAG = f"{ZOFAR_NS}questionnaire"
ZOFAR_NAME_TAG = f"{ZOFAR_NS}name"
ZOFAR_PAGE_TAG = f"{ZOFAR_NS}page"
ZOFAR_TRANSITIONS_TAG = f"{ZOFAR_NS}transitions"
ZOFAR_TRANSITION_TAG = f"{ZOFAR_NS}transition"
ZOFAR_TRIGGERS_TAG = f"{ZOFAR_NS}triggers"
ZOFAR_TRIGGER_TAG = f"{ZOFAR_NS}trigger"
ZOFAR_SCRIPT_ITEM_TAG = f"{ZOFAR_NS}scriptItem"
ZOFAR_ACTION_TAG = f"{ZOFAR_NS}action"
ZOFAR_QUESTION_TAG = f"{ZOFAR_NS}question"
ZOFAR_ANSWER_OPTION_TAG = f"{ZOFAR_NS}answerOption"
ZOFAR_RESPONSE_DOMAIN_TAG = f"{ZOFAR_NS}responseDomain"
ZOFAR_INSTRUCTION_TAG = f"{ZOFAR_NS}instruction"
ZOFAR_INTRODUCTION_TAG = f"{ZOFAR_NS}introduction"
ZOFAR_VARIABLES_TAG = f"{ZOFAR_NS}variables"
ZOFAR_VARIABLE_TAG = f"{ZOFAR_NS}variable"
ZOFAR_SECTION_TAG = f"{ZOFAR_NS}section"
ZOFAR_HEADER_TAG = f"{ZOFAR_NS}header"
ZOFAR_BODY_TAG = f"{ZOFAR_NS}body"
ZOFAR_TITLE_TAG = f"{ZOFAR_NS}title"
ZOFAR_DISPLAY_TAG = f"{ZOFAR_NS}display"
ZOFAR_TEXT_TAG = f"{ZOFAR_NS}text"
ZOFAR_QUESTION_OPEN_TAG = f"{ZOFAR_NS}questionOpen"
ZOFAR_CALENDAR_EPISODES_TAG = f"{ZOFAR_NS}episodes"
ZOFAR_CALENDAR_EPISODES_TABLE_TAG = f"{ZOFAR_NS}episodesTable"
ZOFAR_SINGLE_CHOICE_TAG = f"{ZOFAR_NS}questionSingleChoice"
ZOFAR_MULTIPLE_CHOICE_TAG = f"{ZOFAR_NS}multipleChoice"
ZOFAR_MATRIX_QUESTION_OPEN_TAG = f"{ZOFAR_NS}matrixQuestionOpen"
ZOFAR_MATRIX_SINGLE_CHOICE_TAG = f"{ZOFAR_NS}matrixQuestionSingleChoice"
ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG = f"{ZOFAR_NS}matrixQuestionMultipleChoice"
DISPLAY_NAMESPACE = "{http://www.dzhw.eu/zofar/xml/display}"
ZOFAR_DISPLAY_TEXT_TAG = f"{DISPLAY_NAMESPACE}text"
ON_EXIT_DEFAULT = 'true'
DIRECTION_DEFAULT = 'forward'
CONDITION_DEFAULT = 'true'
ZOFAR_QUESTION_ELEMENTS = [ZOFAR_QUESTION_OPEN_TAG, ZOFAR_SINGLE_CHOICE_TAG, ZOFAR_MULTIPLE_CHOICE_TAG,
                           ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG, ZOFAR_MATRIX_QUESTION_OPEN_TAG,
                           ZOFAR_MATRIX_SINGLE_CHOICE_TAG, ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG,
                           ZOFAR_CALENDAR_EPISODES_TAG, ZOFAR_CALENDAR_EPISODES_TABLE_TAG]
RE_VAL = re.compile(r'#{([a-zA-Z0-9_]+)\.value}')
RE_VAL_OF = re.compile(r'#{zofar\.valueOf\(([a-zA-Z0-9_]+)\)}')
RE_AS_NUM = re.compile(r'#{zofar\.asNumber\(([a-zA-Z0-9_]+)\)}')
RE_TO_LOAD = re.compile(r"^\s*toLoad\.add\('([0-9a-zA-Z_]+)'\)")
RE_TO_RESET = re.compile(r"^\s*toReset\.add\('([0-9a-zA-Z_]+)'\)")
RE_TO_PERSIST = re.compile(r"^\s*toPersist\.put\('([0-9a-zA-Z_]+)',[a-zA-Z0-9_.]+\)")
RE_REDIRECT_TRIG = re.compile(r"^\s*navigatorBean\.redirect\('([a-zA-Z0-9_]+)'\)\s*$")
RE_REDIRECT_TRIG_AUX = re.compile(r"^\s*navigatorBean\.redirect\(([a-zA-Z0-9_]+)\)\s*$")
ZOFAR_NS_URI_E = "http://www.his.de/zofar/xml/questionnaire"
NS_E = {"zofar": ZOFAR_NS_URI}
E = ElementMaker(namespace=ZOFAR_NS_URI_E, nsmap=NS_E)
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
LBL = E.label
PRE = E.prefix
POST = E.postfix
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
