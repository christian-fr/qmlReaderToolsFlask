from unittest import TestCase
from tests.context import test_qml_path, test_questionnaire
from qrt.util.util import qml_details


class TestUtils(TestCase):
    def setUp(self) -> None:
        # setting up the temporary directory
        # self.tmp_dir = TemporaryDirectory()
        # instantiating the QmlLoader class
        self.q = test_questionnaire()

    def tearDown(self) -> None:
        pass
        # self.tmp_dir.cleanup()
        # del self.qml_reader

    def test_qml_details(self):
        d = qml_details(self.q)
        assert 1 == 1
        pass