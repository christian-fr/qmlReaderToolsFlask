from unittest import TestCase
from qrt.util.qmlgen import gen_mqsc, gen_qsc
from qrt.util.qmlutil import NS
from context import QSC_XML_STR_01, MQSC_XML_STR_01, QSC_XML_STR_02

HEADERS = {1: {'uid': 'q1', 'type': 'question', 'text': 'qtext1', 'visible': 'qvis1'},
           2: {'uid': 'int2', 'type': 'introduction', 'text': 'inttext2', 'visible': 'intvis2'},
           3: {'uid': 'ins3', 'type': 'instruction', 'text': 'instext3', 'visible': 'insvis3'}}

SC_AOS = {1: {'uid': 'ao1', 'value': 'val1', 'label': 'lab1', 'visible': 'vis1'},
          2: {'uid': 'ao2', 'value': 'val2', 'label': 'lab2', 'visible': 'vis2'},
          3: {'uid': 'ao3', 'value': 'val3', 'label': 'lab3', 'missing': 'on', 'visible': 'vis3'}}


class Test(TestCase):
    def test_gen_mqsc(self):
        d = {'q_type': 'mqsc', 'q_uid': 'mqsc', 'q_visible': 'mqscvisible',
             'headers': HEADERS,
             'aos': SC_AOS,
             'items': {1: {'uid': 'it1', 'variable': 'itvar01', 'text': 'itlab1', 'visible': 'itvis1'},
                       2: {'uid': 'it2', 'variable': 'itvar02', 'text': 'itlab2', 'visible': 'itvis2'}}}
        q_str = gen_mqsc(d)
        self.assertEqual(MQSC_XML_STR_01, q_str)

    def test_gen_qsc01(self):
        d = {'q_type': 'qsc', 'q_uid': 'qsc', 'q_visible': 'qscvisible', 'q_variable': 'qvar01',
             'headers': HEADERS,
             'aos': SC_AOS}
        q_str = gen_qsc(d)
        self.assertEqual(QSC_XML_STR_01, q_str)

    def test_gen_qsc02(self):
        d = {'q_type': 'qsc', 'q_uid': 'qsc', 'q_visible': 'qscvisible', 'q_variable': 'qvar01', 'rd_type': 'dropdown',
             'headers': HEADERS,
             'aos': SC_AOS}
        q_str = gen_qsc(d)
        self.assertEqual(QSC_XML_STR_02, q_str)
