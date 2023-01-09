import tempfile
from io import StringIO
from pathlib import Path
from unittest import TestCase

import lxml.etree
from lxml.etree import tostring as l_tostring

from tests.context import test_qml_path, test_questionnaire
from tests.context.questionnaire_data import mqsc_example_str
from qrt.util.util import qml_details
from qrt.util.questionnaire import example_mqsc, HeaderQuestion, HeaderTitle, SCAnswerOption, check_for_unique_uids, \
    MatrixResponseDomain, VarRef, Variable, VAR_TYPE_SC, SCMatrixItem, SCResponseDomain, ZofarQuestionSCMatrix, \
    HeaderIntroduction, ZofarAttachedOpen, VAR_TYPE_STR, ZofarQuestionOpen, ZofarQuestionSC, MCResponseDomain, \
    ZofarQuestionMC, MCAnswerOption, HeaderInstruction, VAR_TYPE_BOOL

from qrt.util.qml import ZOFAR_NS_URI


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
                           content="""Wie gut fühlen Sie sich mit den folgenden Akteur*innen vernetzt?""")
        ]
        # header_list_it = [
        #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

        title_header_list = []
        title_header_list.append(HeaderTitle(uid="ti1", content="gar nicht"))
        title_header_list.append(HeaderTitle(uid="ti2", content=""))
        title_header_list.append(HeaderTitle(uid="ti3", content=""))
        title_header_list.append(HeaderTitle(uid="ti4", content=""))
        title_header_list.append(HeaderTitle(uid="ti5", content="sehr gut"))

        title_missing_list = []

        ao_list_it = []
        ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label="gar nicht"))
        ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label=""))
        ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label=""))
        ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label=""))
        ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label="sehr gut"))

        assert check_for_unique_uids(ao_list_it)
        assert check_for_unique_uids(title_header_list)
        assert check_for_unique_uids(title_missing_list)
        assert check_for_unique_uids(header_list)

        matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

        it_list = []

        var_ref1 = VarRef(variable=Variable(name="ap14a", type=VAR_TYPE_SC))
        it1 = SCMatrixItem(uid="it1",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Wissenschaftler*innen aus dem eigenen Fach")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
        it_list.append(it1)

        var_ref2 = VarRef(variable=Variable(name="ap14b", type=VAR_TYPE_SC))
        it2 = SCMatrixItem(uid="it2",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Wissenschaftler*innen anderer Fachrichtungen")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
        it_list.append(it2)

        var_ref3 = VarRef(variable=Variable(name="ap14c", type=VAR_TYPE_SC))
        it3 = SCMatrixItem(uid="it3",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="sonstigen Stakeholdern (z.B. aus Wirtschaft, Kultur oder Politik)")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref3))
        it_list.append(it3)

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

    def test_example_qsc(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Welche Veranstaltungsdauer bevorzugen Sie bei Workshops?")]

        ao_list = []
        ao_list.append(SCAnswerOption(uid="ao1", value="1", label="Weniger als 1 Tag"))
        ao_list.append(SCAnswerOption(uid="ao2", value="2", label="1-tägig"))
        ao_list.append(SCAnswerOption(uid="ao3", value="3", label="2-tägig"))
        ao_list.append(SCAnswerOption(uid="ao4", value="4", label="Mehr als 2 Tage"))

        assert len(ao_list) == len({ao.value for ao in ao_list})
        assert len(ao_list) == len({ao.uid for ao in ao_list})
        assert len(ao_list) == len({ao.label for ao in ao_list if ao.label is not None and ao.label.strip() != ""})

        var_ref1 = VarRef(variable=Variable(name="ap13", type=VAR_TYPE_SC))
        rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

        qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

        y = l_tostring(qsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')

        pass

    def test_example_mc(self):
        header_list = [HeaderQuestion(uid="q1",
                                      content="Welche Workshopformate besuchen Sie bevorzugt?"),
                       HeaderInstruction(uid="ins1",
                                         content="Bitte wählen Sie alles Zutreffende aus.")]

        ao_list = []
        ao_list.append(MCAnswerOption(uid="ao1", label="Digital",
                                      var_ref=VarRef(variable=Variable(name="ap12a", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao2", label="in Präsenz",
                                      var_ref=VarRef(variable=Variable(name="ap12b", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao3", label="Hybrid (Präsenztermin mit Option der digitalen Teilnahme)",
                                      var_ref=VarRef(variable=Variable(name="ap12c", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao4", label="Blended (Selbstlernphase und anschließender Präsenztermin)",
                                      var_ref=VarRef(variable=Variable(name="ap12d", type=VAR_TYPE_BOOL))))
        ao_list.append(MCAnswerOption(uid="ao5", label="Keine Präferenz",
                                      var_ref=VarRef(variable=Variable(name="ap12e", type=VAR_TYPE_BOOL))))

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
