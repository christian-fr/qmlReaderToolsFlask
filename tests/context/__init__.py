from pathlib import Path
from qrt.util.qml import read_xml

# from qrt.util.qml import Questionnaire

pv01_str = Path('context/pv01.toml').read_text(encoding='utf-8')


def test_qml_path():
    return Path('.', 'context', 'questionnaire.xml')


def test_questionnaire():
    return read_xml(test_qml_path())
