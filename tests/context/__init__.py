from pathlib import Path

from qrt.util.qml import read_xml, Questionnaire


def test_qml_path():
    return Path('.', 'context', 'questionnaire.xml')


def test_questionnaire():
    return read_xml(test_qml_path())
