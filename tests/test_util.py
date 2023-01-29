from unittest import TestCase
from context import pv01_str
from qrt.util.util import read_pv


class Test(TestCase):
    def test_read_pv(self):
        pv = read_pv(pv01_str)
        pass
