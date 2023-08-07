import json
import tempfile
from io import StringIO
from pathlib import Path
from typing import List
from unittest import TestCase

import lxml.etree
from lxml.etree import tostring as l_tostring

from qrt.util.qmlgen import unescape_html, example_mqsc
from tests.context import test_qml_path, test_questionnaire
from tests.context.questionnaire_data import mqsc_example_str
from qrt.util.util import qml_details
from qrt.util.questionnaire import HeaderQuestion, HeaderTitle, SCAnswerOption, check_for_unique_uids, \
    MatrixResponseDomain, VarRef, Variable, VAR_TYPE_SC, SCMatrixItem, SCResponseDomain, ZofarQuestionSCMatrix, \
    HeaderIntroduction, ZofarAttachedOpen, VAR_TYPE_STR, ZofarQuestionOpen, ZofarQuestionSC, MCResponseDomain, \
    ZofarQuestionMC, MCAnswerOption, HeaderInstruction, VAR_TYPE_BOOL, MCMatrixItem, ZofarQuestionMCMatrix

from qrt.util.qmlutil import ZOFAR_NS_URI


class TestQuestionnaire(TestCase):
    def setUp(self) -> None:
        # setting up the temporary directory
        # self.tmp_dir = TemporaryDirectory()
        # instantiating the QmlLoader class
        pass

    def tearDown(self) -> None:
        pass
        # self.tmp_dir.cleanup()
        # del self.qml_reader

    def test_qml_details(self):
        self.q = test_questionnaire()
        d = qml_details(self.q)
        assert 1 == 1

    def test_example_mqsc(self):
        header_list = [
            HeaderQuestion(uid="q",
                           content="""Waren die Informationen aus heutiger Sicht ausreichend?""")
        ]
        # header_list_it = [
        #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

        title_header_list = []
        title_header_list.append(HeaderTitle(uid="ti1", content="gar nicht ausreichend"))
        title_header_list.append(HeaderTitle(uid="ti2", content=""))
        title_header_list.append(HeaderTitle(uid="ti3", content=""))
        title_header_list.append(HeaderTitle(uid="ti4", content=""))
        title_header_list.append(HeaderTitle(uid="ti5", content="völlig ausreichend"))

        title_missing_list = []

        ao_list_it = []
        ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label=title_header_list[len(ao_list_it)].content))

        assert len(title_header_list) == len(ao_list_it)

        assert check_for_unique_uids(ao_list_it)
        assert check_for_unique_uids(title_header_list)
        assert check_for_unique_uids(title_missing_list)
        assert check_for_unique_uids(header_list)

        matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

        it_list = []

        var_ref1 = VarRef(variable=Variable(name="ap03a", type=VAR_TYPE_SC))
        it1 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Webseite")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
        it_list.append(it1)

        var_ref2 = VarRef(variable=Variable(name="ap03b", type=VAR_TYPE_SC))
        it2 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Flyer/Broschüre")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
        it_list.append(it2)

        var_ref3 = VarRef(variable=Variable(name="ap03c", type=VAR_TYPE_SC))
        it3 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Info-Veranstaltung")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref3))
        it_list.append(it3)

        var_ref4 = VarRef(variable=Variable(name="ap03d", type=VAR_TYPE_SC))
        it4 = SCMatrixItem(uid="it4",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Beratungsgespräch")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref4))
        it_list.append(it4)

        var_ref5 = VarRef(variable=Variable(name="ap03e", type=VAR_TYPE_SC))
        it5 = SCMatrixItem(uid="it5",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Gespräch mit anderen Wissenschaftler\*innen")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref5))
        it_list.append(it5)

        var_ref6 = VarRef(variable=Variable(name="ap03f", type=VAR_TYPE_SC))
        att_open = ZofarAttachedOpen(uid='open1', var_ref=VarRef(variable=Variable(name="ap03g", type=VAR_TYPE_STR)))
        it6 = SCMatrixItem(uid="it6",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Sonstige, und zwar:")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref6),
                           attached_open_list=[att_open])
        it_list.append(it6)

        matrix_rd.item_list = it_list

        mqsc = ZofarQuestionSCMatrix(uid='mqsc1', header_list=header_list, response_domain=matrix_rd,
                                     title_header=title_header_list, missing_header=title_missing_list)

        y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        # z = mqsc_example_str
        pass

    def test_example_mqsc02(self):
        header_list = [
            HeaderQuestion(uid="q",
                           content="""Inwieweit treffen folgende Aussagen zu den Informationskanälen der TUM-GS auf Sie zu?""")
        ]
        # header_list_it = [
        #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

        title_header_list = []
        title_header_list.append(HeaderTitle(uid="ti1", content="trifft gar nicht zu"))
        title_header_list.append(HeaderTitle(uid="ti2", content=""))
        title_header_list.append(HeaderTitle(uid="ti3", content=""))
        title_header_list.append(HeaderTitle(uid="ti4", content=""))
        title_header_list.append(HeaderTitle(uid="ti5", content="trifft völlig zu"))

        title_missing_list = []

        ao_list_it = []
        ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label=title_header_list[len(ao_list_it)].content))

        assert len(title_header_list) == len(ao_list_it)

        assert check_for_unique_uids(ao_list_it)
        assert check_for_unique_uids(title_header_list)
        assert check_for_unique_uids(title_missing_list)
        assert check_for_unique_uids(header_list)

        matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

        it_list = []

        var_ref1 = VarRef(variable=Variable(name="axi15a", type=VAR_TYPE_SC))
        it1 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Die Inhalte des allgemeinen TUM-GS Newsletters sind relevant für mich")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
        it_list.append(it1)

        var_ref2 = VarRef(variable=Variable(name="axi15b", type=VAR_TYPE_SC))
        it2 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Die Inhalte des allgemeinen TUM-GS Newsletters sind verständlich für mich")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
        it_list.append(it2)

        matrix_rd.item_list = it_list

        mqsc = ZofarQuestionSCMatrix(uid='mqsc1', header_list=header_list, response_domain=matrix_rd,
                                     title_header=title_header_list, missing_header=title_missing_list)

        y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        # z = mqsc_example_str
        pass

    def test_example_mqsc03(self):
        header_list = [
            HeaderQuestion(uid="q",
                           content="""Wie wichtig sind Ihnen die folgenden Rollen Ihrer Betreuungsperson(en)?""")
        ]
        # header_list_it = [
        #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

        title_header_list = []
        title_header_list.append(HeaderTitle(uid="ti1", content="unwichtig"))
        title_header_list.append(HeaderTitle(uid="ti2", content=""))
        title_header_list.append(HeaderTitle(uid="ti3", content=""))
        title_header_list.append(HeaderTitle(uid="ti4", content=""))
        title_header_list.append(HeaderTitle(uid="ti5", content="sehr wichtig"))

        title_missing_list = []
        # title_missing_list.append(HeaderTitle(uid="ti5", content="sehr zufrieden"))

        ao_list_it = []
        ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label=title_header_list[len(ao_list_it)].content))
        ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label=title_header_list[len(ao_list_it)].content))

        # ao_list_it.append(SCAnswerOption(uid='ao6', value="6", label=title_missing_list[0].content, missing=True))

        # assert len(title_header_list) == len(ao_list_it)

        assert check_for_unique_uids(ao_list_it)
        assert check_for_unique_uids(title_header_list)
        assert check_for_unique_uids(title_missing_list)
        assert check_for_unique_uids(header_list)

        matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

        it_list = []

        var_ref1 = VarRef(variable=Variable(name="axi09a", type=VAR_TYPE_SC))
        it1 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Karriereberater*in")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
        it_list.append(it1)

        var_ref2 = VarRef(variable=Variable(name="axi09b", type=VAR_TYPE_SC))
        it2 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Networker*in")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
        it_list.append(it2)

        var_ref3 = VarRef(variable=Variable(name="axi09c", type=VAR_TYPE_SC))
        it3 = SCMatrixItem(uid=f"it{len(it_list) + 1}",
                           header_list=[HeaderQuestion(uid=f"q{len(it_list) + 1}",
                                                       content="Fachlicher Beirat")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref3))
        it_list.append(it3)

        # var_ref4 = VarRef(variable=Variable(name="ap03d", type=VAR_TYPE_SC))
        # it4 = SCMatrixItem(uid="it4",
        #                    header_list=[HeaderQuestion(uid="q1",
        #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
        #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref4))
        # it_list.append(it4)
        #
        # var_ref5 = VarRef(variable=Variable(name="ap03e", type=VAR_TYPE_SC))
        # it4 = SCMatrixItem(uid="it5",
        #                    header_list=[HeaderQuestion(uid="q1",
        #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
        #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref5))
        # it_list.append(it4)
        #
        # var_ref6 = VarRef(variable=Variable(name="ap03f", type=VAR_TYPE_SC))
        # att_open = ZofarAttachedOpen(uid='open1', var_ref=VarRef(variable=Variable(name="ap03g", type=VAR_TYPE_STR)))
        # it4 = SCMatrixItem(uid="it6",
        #                    header_list=[HeaderQuestion(uid="q1",
        #                                                content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
        #                    response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref6),
        #                    attached_open_list=[att_open])
        # it_list.append(it4)

        matrix_rd.item_list = it_list

        mqsc = ZofarQuestionSCMatrix(uid='mqsc1', header_list=header_list, response_domain=matrix_rd,
                                     title_header=title_header_list, missing_header=title_missing_list)

        y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        # z = mqsc_example_str
        pass

    def test_example_qo(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Auf welche Barrieren oder Hürden beim Zugang oder der Nutzung der PoGS-Angebote sind Sie gestoßen?")]
        qo = ZofarQuestionOpen(uid="qo1", header_list=header_list,
                               var_ref=VarRef(variable=Variable(name="ap11", type=VAR_TYPE_STR)))

        y = l_tostring(qo.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        # z = mqsc_example_str
        pass

    def test_example_qo1(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Welche weiteren Service-Angebote/Dienstleistungen der TUM-GS wünschen Sie sich?")]
        qo = ZofarQuestionOpen(uid="qo1", header_list=header_list,
                               var_ref=VarRef(variable=Variable(name="axi12", type=VAR_TYPE_STR)))

        y = l_tostring(qo.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        # z = mqsc_example_str
        pass

    def test_example_qsc(self):
        header_list = [HeaderInstruction(uid="ins1", content="Inwiefern trifft die folgende Aussage auf Sie zu?"),
                       HeaderQuestion(uid="q1",
                                      content="Die Serviceangebote der TUM-GS decken meinen Bedarf einer Unterstützung durch eine Graduiertenschule während der Promotion ab.")]

        ao_list = []
        ao_list.append(SCAnswerOption(uid="ao1", value="1", label="trifft gar nicht zu"))
        ao_list.append(SCAnswerOption(uid="ao2", value="2", label=""))
        ao_list.append(SCAnswerOption(uid="ao3", value="3", label=""))
        ao_list.append(SCAnswerOption(uid="ao4", value="4", label=""))
        ao_list.append(SCAnswerOption(uid="ao5", value="5", label="trifft völlig zu"))

        assert len(ao_list) == len({ao.value for ao in ao_list})
        assert len(ao_list) == len({ao.uid for ao in ao_list})
        # assert len(ao_list) == len({ao.label for ao in ao_list if ao.label is not None and ao.label.strip() != ""})

        var_ref1 = VarRef(variable=Variable(name="axi11", type=VAR_TYPE_SC))
        rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

        qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

        y = l_tostring(qsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        return None

    def test_example_qsc01(self):
        header_list = [HeaderIntroduction(uid="int1",
                                          content="""Das Center for Young Academics, kurz CYA, ist die zentrale Anlaufstelle zur Information, Karriereentwicklung und Vernetzung der Promovierenden, Postdocs und Advanced Talents der RWTH Aachen."""),
                       HeaderQuestion(uid="q1",
                                      content="Kennen Sie die Angebote des Centers for Young Academics (CYA)?")]

        ao_list = []
        ao_list.append(SCAnswerOption(uid=f"ao{len(ao_list) + 1}", value=f"{len(ao_list) + 1}", label="Ja, kenne ich."))
        ao_list.append(
            SCAnswerOption(uid=f"ao{len(ao_list) + 1}", value=f"{len(ao_list) + 1}", label="Nein, kenne ich nicht."))

        assert len(ao_list) == len({ao.value for ao in ao_list})
        assert len(ao_list) == len({ao.uid for ao in ao_list})

        var_ref1 = VarRef(variable=Variable(name="axh01", type=VAR_TYPE_SC))
        rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

        qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

        y = l_tostring(qsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = unescape_html(y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', ''))

        pass

    def test_example_multiple(self, index: int, list_of_labels: List[str], variable_name: str,
                              visible: str, ao_start_index: int = 0) -> str:
        header_list = [HeaderQuestion(uid="q1",
                                      content="An welcher Fakultät promovieren Sie?")]
        question_visible = "zofar.asNumber(PRELOADpreload01) == 1"
        ao_list = []
        [ao_list.append(
            SCAnswerOption(uid=f"ao{len(ao_list) + 1 + ao_start_index}", value=f"{len(ao_list) + 1 + ao_start_index}",
                           label=ao_label)) for ao_label in list_of_labels]

        assert len(ao_list) == len({ao.value for ao in ao_list})
        assert len(ao_list) == len({ao.uid for ao in ao_list})
        assert len(ao_list) == len({ao.label for ao in ao_list if ao.label is not None and ao.label.strip() != ""})

        var_ref1 = VarRef(variable=Variable(name=variable_name, type=VAR_TYPE_SC))
        rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

        qsc = ZofarQuestionSC(uid=f"qsc{index}", header_list=header_list, response_domain=rd, visible=visible)

        y = l_tostring(qsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
        return z

    def test_multiple_questions(self):
        json_str = Path(
            r'C:\Users\friedrich\AppData\Roaming\JetBrains\PyCharm2022.2\scratches\json_data.json').read_text()

        in_dict = json.loads(json_str)
        out_str_list = []

        index = 0
        ao_start_index = 5
        for k, v in in_dict.items():
            out_str_list.append(self.test_example_multiple(index=index + 1, list_of_labels=v,
                                                           visible=f"zofar.asNumber(PRELOADpreload01) == {int(k) - 1}",
                                                           variable_name=f"adbi26",
                                                           ao_start_index=ao_start_index))
            ao_start_index += len(v)
            index += 1
        out_str = '\n\n'.join(out_str_list)
        Path('.', 'output.xml').write_text(out_str, encoding='utf-8')
        pass

    def test_example_mc(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Welche Informationskanäle der TUM-GS nutzen Sie, um zusätzliche Informationen rund um die Promotion zu erhalten?"),
                       HeaderInstruction(uid="ins1",
                                         content="Bitte wählen Sie alles Zutreffende aus.")]

        ao_list = []
        ao_list.append(MCAnswerOption(uid="ao1", label="TUM-GS Newsletter allgemein",
                                      var_ref=VarRef(variable=Variable(name="axi14a", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao2", label="Kursnewsletter",
                                      var_ref=VarRef(variable=Variable(name="axi14b", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao3", label="LinkedIn Profil",
                                      var_ref=VarRef(variable=Variable(name="axi14c", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao4", label="Instagram Channel",
                                      var_ref=VarRef(variable=Variable(name="axi14d", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao5", label="Ich nutze keine dieser Optionen.",
                                      var_ref=VarRef(variable=Variable(name="axi14e", type=VAR_TYPE_BOOL))))

        # att_open = ZofarQuestionOpen(uid="open", var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
        # ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
        #                               var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
        #                               attached_open_list=[att_open]))

        # integrity check: unique uids
        assert check_for_unique_uids(ao_list)
        assert check_for_unique_uids(header_list)

        rd = MCResponseDomain(ao_list=ao_list)

        mc = ZofarQuestionMC(uid="mc", header_list=header_list, response_domain=rd)
        y = l_tostring(mc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        pass

    def test_example_mc02(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Kennen Sie folgende Angebote des Argelander Programms für den wissenschaftlichen Nachwuchs?"),
                       HeaderInstruction(uid="ins1",
                                         content="Bitte wählen Sie alles Zutreffende aus.")]

        ao_list = []
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Qualifizierungsprogramm Doctorate plus",
                                      var_ref=VarRef(variable=Variable(name="axd01a", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Online Coaching Angebot für Promovierende",
                                      var_ref=VarRef(variable=Variable(name="axd01b", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="E-Trainings",
                                      var_ref=VarRef(variable=Variable(name="axd01c", type=VAR_TYPE_BOOL))))
        ao_list.append(
            MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Compliance-Reihe &#x201C;Better safe than sorry&#x201D;",
                           var_ref=VarRef(variable=Variable(name="axd01d", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Job Talks für Promovierende und Promovierte",
                                      var_ref=VarRef(variable=Variable(name="axd01e", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Beratung zur Promotionsfinanzierung",
                                      var_ref=VarRef(variable=Variable(name="axd01f", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}",
                                      label="Förderangebote des Bonner Graduiertenzentrums, wie Conference Grants oder Santander International Exchange Grants",
                                      var_ref=VarRef(variable=Variable(name="axd01g", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}",
                                      label="Pro-Motion, das Unterstützungsprogramm für internationale Promovierende",
                                      var_ref=VarRef(variable=Variable(name="axd01h", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}",
                                      label="MeTra, das Mentoring- und Trainingsprogramm für Doktorandinnen",
                                      var_ref=VarRef(variable=Variable(name="axd01i", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Healthy Campus Bonn",
                                      var_ref=VarRef(variable=Variable(name="axd01j", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Career Service",
                                      var_ref=VarRef(variable=Variable(name="axd01k", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Transfer Center enaCom",
                                      var_ref=VarRef(variable=Variable(name="axd01l", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label="Ich kenne keines dieser Angebote",
                                      var_ref=VarRef(variable=Variable(name="axd01m", type=VAR_TYPE_BOOL))))

        # att_open = ZofarQuestionOpen(uid="open", var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
        # ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
        #                               var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
        #                               attached_open_list=[att_open]))

        # integrity check: unique uids
        assert check_for_unique_uids(ao_list)
        assert check_for_unique_uids(header_list)

        rd = MCResponseDomain(ao_list=ao_list)

        mc = ZofarQuestionMC(uid="mc", header_list=header_list, response_domain=rd)
        y = l_tostring(mc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        pass

    def test_example_mc03(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Welche Angebote des CYA haben Sie bereits genutzt?"),
                       HeaderInstruction(uid="ins1",
                                         content="Bitte wählen Sie alles Zutreffende aus.")]

        ao_reg_src_list = [('axh03a', 'Seminare und Workshops'),
                           ('axh03b', 'Promotionssupplement'),
                           ('axh03c', 'Young Academics Day'),
                           ('axh03d', 'Advanced Talents Day'),
                           ('axh03e', 'Veranstaltung "Wege in der Wissenschaft"'),
                           ('axh03f', 'Einzelcoaching'),
                           ('axh03g', 'Mentoring'),
                           ('axh03h', 'Orientierungs- und Karriereberatungsgespräche')]
        # ao_exc_src_list = [('axd0m', 'Ich kenne keines dieser Angebote')]
        ao_exc_src_list = []

        ao_list = []

        for ao in ao_reg_src_list:
            var_name, content = ao
            ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label=content,
                                          var_ref=VarRef(variable=Variable(name=var_name, type=VAR_TYPE_BOOL))))

        if ao_exc_src_list:
            for ao in ao_exc_src_list:
                var_name, content = ao
                ao_list.append(MCAnswerOption(uid=f"ao{len(ao_list) + 1}", label=content,
                                              var_ref=VarRef(variable=Variable(name=var_name, type=VAR_TYPE_BOOL)),
                                              exclusive=True))

        # att_open = ZofarQuestionOpen(uid="open", var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
        # ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
        #                               var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
        #                               attached_open_list=[att_open]))

        # integrity check: unique uids
        assert check_for_unique_uids(ao_list)
        assert check_for_unique_uids(header_list)

        rd = MCResponseDomain(ao_list=ao_list)

        mc = ZofarQuestionMC(uid="mc", header_list=header_list, response_domain=rd)
        y = l_tostring(mc.gen_xml(), pretty_print=True).decode('utf-8')
        z = unescape_html(y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', ''))

        pass
