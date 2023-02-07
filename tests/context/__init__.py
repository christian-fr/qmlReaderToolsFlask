from pathlib import Path
from qrt.util.qml import read_xml

# from qrt.util.qml import Questionnaire

pv01_str = Path('context/pv01.toml').read_text(encoding='utf-8')

MQSC_XML_STR_01 = """<zofar:matrixQuestionSingleChoice uid="mqsc" block="true">
  <zofar:header>
    <zofar:question uid="q1" visible="qvis1" block="true">qtext1</zofar:question>
    <zofar:introduction uid="int2" visible="intvis2" block="true">inttext2</zofar:introduction>
    <zofar:instruction uid="ins3" visible="insvis3" block="true">instext3</zofar:instruction>
  </zofar:header>
  <zofar:responseDomain uid="rd" noResponseOptions="3">
    <zofar:header>
      <zofar:title uid="ti1">lab1</zofar:title>
      <zofar:title uid="ti2">lab2</zofar:title>
      <zofar:title uid="ti3">lab3</zofar:title>
    </zofar:header>
    <zofar:missingHeader/>
    <zofar:item uid="it1" visible="true">
      <zofar:header>
        <zofar:question uid="q1" visible="true" block="true">itlab1</zofar:question>
      </zofar:header>
      <zofar:responseDomain variable="itvar01" itemClasses="true" uid="rd1">
        <zofar:answerOption uid="ao1" label="lab1" visible="true" value="val1"/>
        <zofar:answerOption uid="ao2" label="lab2" visible="true" value="val2"/>
        <zofar:answerOption uid="ao3" label="lab3" visible="true" value="val3"/>
      </zofar:responseDomain>
    </zofar:item>
    <zofar:item uid="it2" visible="true">
      <zofar:header>
        <zofar:question uid="q2" visible="true" block="true">itlab2</zofar:question>
      </zofar:header>
      <zofar:responseDomain variable="itvar02" itemClasses="true" uid="rd2">
        <zofar:answerOption uid="ao1" label="lab1" visible="true" value="val1"/>
        <zofar:answerOption uid="ao2" label="lab2" visible="true" value="val2"/>
        <zofar:answerOption uid="ao3" label="lab3" visible="true" value="val3"/>
      </zofar:responseDomain>
    </zofar:item>
  </zofar:responseDomain>
</zofar:matrixQuestionSingleChoice>
"""
QSC_XML_STR_01 = """<zofar:questionSingleChoice uid="qsc" visible="qscvisible">
  <zofar:header>
    <zofar:question uid="q1" visible="qvis1" block="true">qtext1</zofar:question>
    <zofar:introduction uid="int2" visible="intvis2" block="true">inttext2</zofar:introduction>
    <zofar:instruction uid="ins3" visible="insvis3" block="true">instext3</zofar:instruction>
  </zofar:header>
  <zofar:responseDomain variable="qvar01" itemClasses="true" uid="rd">
    <zofar:answerOption uid="ao1" label="lab1" visible="true" value="val1"/>
    <zofar:answerOption uid="ao2" label="lab2" visible="true" value="val2"/>
    <zofar:answerOption uid="ao3" label="lab3" visible="true" value="val3"/>
  </zofar:responseDomain>
</zofar:questionSingleChoice>
"""
QSC_XML_STR_02 = """<zofar:questionSingleChoice uid="qsc" visible="qscvisible">
  <zofar:header>
    <zofar:question uid="q1" visible="qvis1" block="true">qtext1</zofar:question>
    <zofar:introduction uid="int2" visible="intvis2" block="true">inttext2</zofar:introduction>
    <zofar:instruction uid="ins3" visible="insvis3" block="true">instext3</zofar:instruction>
  </zofar:header>
  <zofar:responseDomain variable="qvar01" type="dropdown" itemClasses="true" uid="rd">
    <zofar:answerOption uid="ao1" label="lab1" visible="true" value="val1"/>
    <zofar:answerOption uid="ao2" label="lab2" visible="true" value="val2"/>
    <zofar:answerOption uid="ao3" label="lab3" visible="true" value="val3"/>
  </zofar:responseDomain>
</zofar:questionSingleChoice>
"""


def test_qml_path():
    return Path('.', 'context', 'questionnaire.xml')


def test_questionnaire():
    return read_xml(test_qml_path())
