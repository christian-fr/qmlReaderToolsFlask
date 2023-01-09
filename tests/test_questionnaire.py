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
    HeaderIntroduction

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
            HeaderIntroduction(uid="intro1",
                               content="""Wir beziehen uns hier auf Ihr Praktikum "#{zofar.getJsonProperty(episodeObj,'name')}" zwischen #{zofar.labelOf(startmonth)} #{zofar.labelOf(startyear)} und #{zofar.labelOf(endmonth)} #{zofar.labelOf(endyear)}.""",
                               visible="!missingStartDate.value and !missingEndDate.value and zofar.getJsonProperty(episodeObj,'name')!=''"),
            HeaderIntroduction(uid="intro2",
                               content="""Wir beziehen uns hier auf Ihr Praktikum zwischen #{zofar.labelOf(startmonth)} #{zofar.labelOf(startyear)} und #{zofar.labelOf(endmonth)} #{zofar.labelOf(endyear)}.""",
                               visible="!missingStartDate.value and !missingEndDate.value and zofar.getJsonProperty(episodeObj,'name')==''"),
            HeaderIntroduction(uid="intro3",
                               content="""Wir beziehen uns hier auf Ihr Praktikum "#{zofar.getJsonProperty(episodeObj,'name')}".""",
                               visible="(missingStartDate.value or missingEndDate.value) and zofar.getJsonProperty(episodeObj,'name')!=''"),
            HeaderQuestion(uid="q",
                           content="""Bitte geben Sie für jede Aussage an, ob sie auf dieses Praktikum völlig zutrifft, eher zutrifft, teilweise zutrifft, eher nicht zutrifft oder gar nicht zutrifft.""")
        ]
        # header_list_it = [
        #     HeaderQuestion(uid="q1", content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")]

        title_header_list = []
        title_header_list.append(HeaderTitle(uid="ti1", content="trifft völlig zu"))
        title_header_list.append(HeaderTitle(uid="ti2", content="trifft eher zu"))
        title_header_list.append(HeaderTitle(uid="ti3", content="teils/teils"))
        title_header_list.append(HeaderTitle(uid="ti4", content="trifft eher nicht zu"))
        title_header_list.append(HeaderTitle(uid="ti5", content="trifft gar nicht zu"))

        title_missing_list = []
        title_missing_list.append(HeaderTitle(uid="ti6", content="weiß nicht"))

        ao_list_it = []
        ao_list_it.append(SCAnswerOption(uid='ao1', value="1", label="trifft völlig zu"))
        ao_list_it.append(SCAnswerOption(uid='ao2', value="2", label="trifft eher zu"))
        ao_list_it.append(SCAnswerOption(uid='ao3', value="3", label="teils/teils"))
        ao_list_it.append(SCAnswerOption(uid='ao4', value="4", label="trifft eher nicht zu"))
        ao_list_it.append(SCAnswerOption(uid='ao5', value="5", label="trifft gar nicht zu"))
        ao_list_it.append(SCAnswerOption(uid='ao6', value="-9", label="weiß nicht", missing=True))

        assert check_for_unique_uids(ao_list_it)
        assert check_for_unique_uids(title_header_list)
        assert check_for_unique_uids(title_missing_list)
        assert check_for_unique_uids(header_list)

        matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

        it_list = []

        var_ref1 = VarRef(variable=Variable(name="int021", type=VAR_TYPE_SC))
        it1 = SCMatrixItem(uid="it1",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Ich konnte bei diesem Praktikum immer wieder Neues dazulernen.")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1),
                           visible="""((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) lt zofar.asNumber(h_exitdatum)""")
        it_list.append(it1)


        var_ref2 = VarRef(variable=Variable(name="int021", type=VAR_TYPE_SC))
        it2 = SCMatrixItem(uid="it1_2",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Ich kann bei diesem Praktikum immer wieder Neues dazulernen.")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1),
                           visible="""((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) ge zofar.asNumber(h_exitdatum)""")
        it_list.append(it2)


        var_ref3 = VarRef(variable=Variable(name="int022", type=VAR_TYPE_SC))
        it3 = SCMatrixItem(uid="it2",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviert habe, war sehr gut.")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1),
                           visible="""((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) lt zofar.asNumber(h_exitdatum)""")
        it_list.append(it3)


        var_ref2 = VarRef(variable=Variable(name="int022", type=VAR_TYPE_SC))
        it4 = SCMatrixItem(uid="it2_2",
                           header_list=[HeaderQuestion(uid="q1",
                                                       content="Die Betreuung durch die Einrichtung, in der ich das Praktikum absolviere, ist sehr gut.")],
                           response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1),
                           visible="""((zofar.asNumber(endyear) * 100) + zofar.asNumber(endmonth)) ge zofar.asNumber(h_exitdatum)""")
        it_list.append(it4)



        matrix_rd.item_list = it_list

        mqsc = ZofarQuestionSCMatrix(uid='mqsc1', header_list=header_list, response_domain=matrix_rd,
                                     title_header=title_header_list, missing_header=title_missing_list)

        y = l_tostring(mqsc.gen_xml(), pretty_print=True).decode('utf-8')
        z = mqsc_example_str
        pass
