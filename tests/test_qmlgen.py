from unittest import TestCase
from qrt.util.qmlgen import gen_mqsc

class Test(TestCase):
    def test_gen_mqsc(self):
        d = {'type': 'mqsc', 'q_uid': 'mqsc', 'q_visible': 'mqscvisible', 'headers': {1: {'uid': 'q1', 'type': 'question', 'text': 'qtext1', 'visible': 'qvis1'}, 2: {'uid': 'int2', 'type': 'introduction', 'text': 'inttext2', 'visible': 'intvis2'}, 3: {'uid': 'ins3', 'type': 'instruction', 'text': 'instext3', 'visible': 'insvis3'}}, 'aos': {1: {'uid': 'ao1', 'value': 'val1', 'label': 'lab1', 'visible': 'vis1'}, 2: {'uid': 'ao2', 'value': 'val2', 'label': 'lab2', 'visible': 'vis2'}, 3: {'uid': 'ao3', 'value': 'val3', 'label': 'lab3', 'missing': 'on', 'visible': 'vis3'}}, 'items': {1: {'uid': 'it1', 'variable': 'itvar1', 'text': 'itlab1', 'visible': 'itvis1'}, 2: {'uid': 'it2', 'variable': 'itvar2', 'text': 'itlab2', 'visible': 'itvis2'}}}
        x = gen_mqsc(d)
        self.fail()
