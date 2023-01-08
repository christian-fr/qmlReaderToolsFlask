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
MQO = E.matrixQuestionOpen
RD = E.responseDomain
AO = E.answerOption
ITEM = E.item
TITLE = E.title
TEXT = E.text
INS = E.instruction
INT = E.introduction
QUE = E.question
