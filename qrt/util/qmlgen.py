from lxml.builder import ElementMaker  # lxml only !
import lxml.etree

import qrt.util.questionnaire
from qrt.util.qml import ZOFAR_NS, NS
from qrt.util.questionnaire import example_mqsc

NS = {'zofar': NS['zofar']}
E = ElementMaker(namespace=NS['zofar'], nsmap=NS)

PAGE = E.page
HEADER = E.header
BODY = E.body
SECTION = E.section
UNIT = E.unit
QSC = E.questionSingleChoice
MC = E.multipleChoice
MMC = E.matrixMultipleChoice
MQSC = E.matrixQuestionSingleChoice
QO = E.questionOpen
MQO = E.matrixQuestionOpen
RD = E.responseDomain
AO = E.answerOption
IT = E.item
TITLE = E.title
TEXT = E.text
INS = E.instruction
INT = E.introduction
QUE = E.question

if __name__ == '__main__':
    mqsc_obj = qrt.util.questionnaire.example_mqsc()

    # matrix single choice
    mqsc = MQSC()
    print(lxml.etree.tostring(mqsc, pretty_print=True))
