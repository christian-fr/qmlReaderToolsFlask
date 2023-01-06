from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, NewType, Union
# noinspection PyProtectedMember
from lxml.etree import _Element as _lE, ElementTree as lEt, tostring as l_to_string
from qrt.util.qmlgen import *

VAR_TYPE_SC = "singleChoiceAnswerOption"
VAR_TYPE_BOOL = "boolean"
VAR_TYPE_STR = "string"
VAR_TYPE_NUM = "number"

SC_TYPE_DROPDOWN = "dropDown"

ON_EXIT_DEFAULT = 'true'
DIRECTION_DEFAULT = 'forward'
CONDITION_DEFAULT = 'true'

# forward declaration of class TriggerVariable
TriggerVariable = NewType('TriggerVariable', None)
ZofarPageObject = NewType('ZofarPageObject', None)
Section = NewType('Section', None)
# ZofarQuestionOpen = NewType('ZofarQuestionOpen', None)
ResponseDomain = NewType('ResponseDomain', None)


# Item = NewType('Item', None)


@dataclass(kw_only=True)
class ZofarPageObject:
    uid: str
    # parent_uid: Optional[str] = None
    # full_uid: Optional[str] = None
    visible: str = 'true'


@dataclass(kw_only=True)
class Variable:
    name: str
    type: str


@dataclass(kw_only=True)
class VarRef:
    variable: Variable
    # list of conditions (as spring expression) that have to be fulfilled in order to reach the variable reference
    condition: List[str] = field(default_factory=list)

    def __str__(self):
        return f'{self.variable.name}: {self.variable.type}; {self.condition}'

    def __gt__(self, other):
        if not isinstance(other, VarRef):
            raise TypeError("can only compare to other VarRef objects")
        return self.variable.name > other.variable.name

    def __lt__(self, other):
        if not isinstance(other, VarRef):
            raise TypeError("can only compare to other VarRef objects")
        return self.variable.name > other.variable.name

    def __ge__(self, other):
        if not isinstance(other, VarRef):
            raise TypeError("can only compare to other VarRef objects")
        return self.variable.name >= other.variable.name

    def __le__(self, other):
        if not isinstance(other, VarRef):
            raise TypeError("can only compare to other VarRef objects")
        return self.variable.name <= other.variable.name

    def __dict__(self):
        return {self.variable.name: (self.variable.type, self.condition)}


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderObject(ZofarPageObject):
    type: str
    content: str

    def gen_xml(self):
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderTitle(HeaderObject):
    type: str = 'title'

    def gen_xml(self):
        return TITLE(self.content, uid=self.uid, visible=self.visible, block="true")


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderText(HeaderObject):
    type: str = 'text'

    def gen_xml(self):
        return TEXT(self.content, uid=self.uid, visible=self.visible, block="true")


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderQuestion(HeaderObject):
    type: str = 'question'

    def gen_xml(self):
        return QUE(self.content, uid=self.uid, visible=self.visible, block="true")


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderIntroduction(HeaderObject):
    type: str = 'introduction'

    def gen_xml(self):
        return INT(self.content, uid=self.uid, visible=self.visible, block="true")


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderInstruction(HeaderObject):
    type: str = 'instruction'

    def gen_xml(self):
        return INS(self.content, uid=self.uid, visible=self.visible, block="true")


# noinspection PyDataclass
@dataclass(kw_only=True)
class Section(ZofarPageObject):
    header_list: list
    children: List[Union[ZofarPageObject, Section]] = field(default_factory=list)
    type: str = 'section'


# noinspection PyDataclass
@dataclass(kw_only=True)
class ResponseDomain:
    uid: str = "rd"
    header_list: List[HeaderObject] = field(default_factory=list)


# noinspection PyDataclass
@dataclass(kw_only=True)
class Question(ZofarPageObject):
    type: Optional[str]
    var_ref: Optional[VarRef] = None
    header_list: List[HeaderObject] = field(default_factory=list)

    def gen_xml(self):
        return NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionOpen(Question):
    var_ref: VarRef
    type: str = 'questionOpen'
    size: str = "40"
    small_option: bool = True

    def gen_xml(self):
        if self.header_list:
            return QO(HEADER(*[h.gen_xml() for h in self.header_list]), uid=self.uid, visible=self.visible,
                      variable=self.var_ref.variable.name, size=self.size, smallOption=str(self.small_option).lower())
        else:
            return QO(uid=self.uid, visible=self.visible,
                      variable=self.var_ref.variable.name, size=self.size,
                      smallOption=str(self.small_option).lower())


# noinspection PyDataclass
@dataclass(kw_only=True)
class AnswerOption(ZofarPageObject):
    label: Optional[str]
    missing: Optional[bool] = False
    var_ref: Optional[VarRef] = None
    attached_open_list: List[ZofarQuestionOpen] = field(default_factory=list)

    def gen_xml(self) -> _lE:
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class SCAnswerOption(AnswerOption):
    value: Optional[str]

    def gen_xml(self) -> _lE:
        return AO(*[qo.gen_xml() for qo in self.attached_open_list], uid=self.uid, label=self.label,
                  visible=self.visible, value=self.value)


# noinspection PyDataclass
@dataclass(kw_only=True)
class MCAnswerOption(AnswerOption):
    var_ref: VarRef

    def gen_xml(self) -> _lE:
        return AO(*[qo.gen_xml() for qo in self.attached_open_list], uid=self.uid, label=self.label,
                  visible=self.visible, variable=self.var_ref.variable.name)


# noinspection PyDataclass
@dataclass(kw_only=True)
class SCResponseDomain(ResponseDomain):
    var_ref: VarRef
    ao_list: List[AnswerOption]
    item_classes: bool = True
    # for dropDown
    rd_type: Optional[str] = None

    def get_var_refs(self):
        raise NotImplementedError

    def gen_xml(self) -> _lE:
        if self.rd_type is not None:
            if self.rd_type == SC_TYPE_DROPDOWN:
                return RD(*[ao.gen_xml() for ao in self.ao_list],
                          variable=self.var_ref.variable.name,
                          type=SC_TYPE_DROPDOWN,
                          itemClasses=str(self.item_classes).lower(), uid=self.uid)
        return RD(*[ao.gen_xml() for ao in self.ao_list],
                  variable=self.var_ref.variable.name,
                  itemClasses=str(self.item_classes).lower(), uid=self.uid)


# noinspection PyDataclass
@dataclass(kw_only=True)
class MCResponseDomain(ResponseDomain):
    ao_list: List[MCAnswerOption] = field(default_factory=list)

    def get_var_refs(self):
        raise NotImplementedError

    def gen_xml(self):
        return RD(*[ao.gen_xml() for ao in self.ao_list], uid=self.uid)


# noinspection PyDataclass
@dataclass(kw_only=True)
class Item(ZofarPageObject):
    header_list: List[HeaderObject]
    response_domain: ResponseDomain


# noinspection PyDataclass
@dataclass(kw_only=True)
class QOItem(Item):
    var_ref: Optional[VarRef]
    response_domain: SCResponseDomain

    def get_var_refs(self):
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class SCItem(ZofarPageObject):
    var_ref: VarRef
    response_domain: SCResponseDomain

    def get_var_refs(self):
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class MCItem(ZofarPageObject):
    response_domain: MCResponseDomain

    def get_var_refs(self):
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class MatrixResponseDomain(ResponseDomain):
    no_response_options: Optional[str]
    # for singleChoice -> "dropDown"
    rd_type: Optional[str] = None
    item_list: List[Union[MCItem, SCItem]] = field(default_factory=list)

    def get_var_refs(self):
        return [it.get_var_refs() for it in self.item_list]


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionSC(Question):
    response_domain: SCResponseDomain
    type: str = 'questionSingleChoice'

    def get_var_refs(self) -> List[VarRef]:
        return [self.response_domain.var_ref]

    def gen_xml(self) -> _lE:
        return QSC(HEADER(*[h.gen_xml() for h in self.header_list]),
                   self.response_domain.gen_xml(),
                   uid=self.uid, visible=self.visible)


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionMC(Question):
    response_domain: MCResponseDomain
    type: str = 'multipleChoice'

    def gen_xml(self):
        return MC(HEADER(*[h.gen_xml() for h in self.header_list]),
                  self.response_domain.gen_xml(),
                  uid=self.uid)


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionMCMatrix(Question):
    response_domain: MatrixResponseDomain
    title_header: List[ZofarPageObject]
    missing_header: List[ZofarPageObject]
    type: str = 'matrixMultipleChoice'

    @property
    def get_var_refs(self) -> List[VarRef]:
        return [f.var_ref for f in self.children if f.var_ref is not None]


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionSCMatrix(Question):
    title_header: List[ZofarPageObject]
    response_domain: MatrixResponseDomain
    type: str = 'matrixSingleChoice'
    var_ref = None

    def gen_xml(self) -> _lE:
        header_list = []
        for header in self.header_list:
            header_list.append(header.gen_xml())

        rd_header_title_list = []

        for header_title in self.title_header:
            TITLE(header_titleuid=header_title.uid)
        rd_item_list = []
        for item in self.response_domain.item_list:
            rd_item_list.append(IT(uid=item.uid, block="true", visible=item.visible))

        return MQSC(HEADER(*header_list), RD(), uid=self.uid, block="true")


@dataclass(kw_only=True)
class Transition:
    target_uid: str
    condition: Optional[str] = None
    # condition as spring expression that has to be fulfilled on order to follow the transition


@dataclass(kw_only=True)
class Trigger:
    condition: Optional[str] = 'true'
    children: Optional[TriggerVariable] = None
    on_exit: Optional[str] = ON_EXIT_DEFAULT
    direction: Optional[str] = DIRECTION_DEFAULT


# noinspection PyDataclass
@dataclass(kw_only=True)
class TriggerRedirect(Trigger):
    target_cond_list: List[Tuple[str, str]]


# noinspection PyDataclass
@dataclass(kw_only=True)
class TriggerVariable(Trigger):
    variable: str
    value: str


# noinspection PyDataclass
@dataclass(kw_only=True)
class TriggerAction(Trigger):
    command: str


# noinspection PyDataclass
@dataclass(kw_only=True)
class TriggerJsCheck(Trigger):
    variable: str
    x_var: str
    y_var: str


@dataclass(kw_only=True)
class EnumValue:
    uid: str
    value: int
    label: str


@dataclass(kw_only=True)
class EnumValues:
    variable: Variable
    values: List[EnumValue]


@dataclass
class Page:
    uid: str
    body_vars: List[VarRef] = field(default_factory=dict)
    body_questions: List[str] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    var_ref: List[str] = field(default_factory=list)
    _triggers_list: List[Trigger] = field(default_factory=list)
    triggers_vars: List[str] = field(default_factory=list)
    triggers_json_save: List[str] = field(default_factory=list)
    triggers_json_load: List[str] = field(default_factory=list)
    triggers_json_reset: List[str] = field(default_factory=list)
    visible_conditions: List[str] = field(default_factory=list)
    trig_redirect_on_exit_true: List[TriggerRedirect] = field(default_factory=list)
    trig_redirect_on_exit_false: List[TriggerRedirect] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_element: _lE = field(default_factory=_lE)

    @property
    def triggers_list(self):
        return self._triggers_list

    def __str__(self):
        return self.uid


@dataclass
class Questionnaire:
    pages: List[Page] = field(default_factory=list)
    var_declarations: Dict[str, Variable] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    xml_root: lEt = field(default_factory=lEt)

    def body_vars_per_page_dict(self):
        return {p.uid: p.body_vars for p in self.pages}

    def all_page_questions_dict(self):
        return {p.uid: p.body_questions for p in self.pages}

    def all_vars_declared(self) -> Dict[str, str]:
        return {var_name: var.type for var_name, var in self.var_declarations.items()}

    def vars_declared_not_used(self) -> Dict[str, str]:
        names_missing = set(self.all_vars_declared().keys()).difference(self.all_page_body_vars().keys())
        return {varname: self.all_vars_declared()[varname] for varname in names_missing}

    def vars_declared_used_inconsistent(self) -> Dict[str, List[str]]:
        results = defaultdict(set)
        for varname, vartype in self.all_page_body_vars().items():
            if varname in self.all_vars_declared().keys():
                if vartype != self.all_vars_declared()[varname]:
                    results[varname].add(vartype)
                    results[varname].add(self.all_vars_declared()[varname])
        return {k: list(v) for k, v in results.items()}

    def vars_used_not_declared(self) -> Dict[str, str]:
        names_missing = set(self.all_page_body_vars().keys()).difference(self.all_vars_declared().keys())
        return {varname: self.all_page_body_vars()[varname] for varname in names_missing}

    def all_page_body_vars(self) -> Dict[str, str]:
        vars_dict = {}
        for page, var_list in self.body_vars_per_page_dict().items():
            for var_ref in var_list:
                if var_ref.variable.name in vars_dict:
                    if var_ref.variable.type != vars_dict[var_ref.variable.name]:
                        self.warnings.append(
                            f'variable "{var_ref.variable.name}" already found as type {vars_dict[var_ref.variable.name]}, found on page "{page}" as type "{var_ref.variable.type}"')
                else:
                    vars_dict[var_ref.variable.name] = var_ref.variable.type
        return vars_dict


def example_mqsc():
    header_list = [HeaderQuestion(uid="q1", content="Was halten Ihre Eltern und Ihre Freunde von Ihrem Studienfach?")]
    header_list_it = [
        HeaderQuestion(uid="q1", content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")]

    title_header_list = []
    title_header_list.append(HeaderTitle(uid="ti1", content="trifft völlig zu"))
    title_header_list.append(HeaderTitle(uid="ti2", content="trifft eher zu"))
    title_header_list.append(HeaderTitle(uid="ti3", content="teils / teils"))
    title_header_list.append(HeaderTitle(uid="ti4", content="trifft eher nicht zu"))
    title_header_list.append(HeaderTitle(uid="ti5", content="trifft gar nicht zu"))

    ao_list_it = []
    ao_list_it.append(AnswerOption(uid='ao1', value="1", label="trifft völlig zu"))
    ao_list_it.append(AnswerOption(uid='ao2', value="2", label="trifft eher zu"))
    ao_list_it.append(AnswerOption(uid='ao3', value="3", label="teils / teils"))
    ao_list_it.append(AnswerOption(uid='ao4', value="4", label="trifft eher nicht zu"))
    ao_list_it.append(AnswerOption(uid='ao5', value="5", label="trifft gar nicht zu"))

    assert check_for_unique_uids(ao_list_it)
    assert check_for_unique_uids(title_header_list)
    assert check_for_unique_uids(header_list)

    matrix_rd = MatrixResponseDomain(uid="rd", no_response_options=str(len(ao_list_it)))

    it_list = []

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it1 = Item(uid="it1",
               header_list=[HeaderQuestion(uid="q1",
                                           content="Meine Eltern finden, dass ich ein gutes Studienfach gewählt habe.")],
               response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref1))
    it_list.append(it1)

    var_ref2 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    it2 = Item(uid="it2",
               header_list=[HeaderQuestion(uid="q1",
                                           content="Meine Freundinnen und Freunde finden, dass ich ein gutes Studienfach gewählt habe.")],
               response_domain=SCResponseDomain(uid="rd", ao_list=ao_list_it, var_ref=var_ref2))
    it_list.append(it2)

    matrix_rd.item_list = it_list

    mqsc = ZofarQuestionSCMatrix(uid='msc', header_list=header_list, response_domain=matrix_rd,
                                 title_header=title_header_list)
    y = l_to_string(mqsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    return mqsc


def example_qsc_1():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Haben Sie sich an der Universität Potsdam vor Beginn Ihrer Promotion zum Thema Promovieren informiert?")]

    ao_list = []
    ao_list.append(SCAnswerOption(uid="ao1", value="1", label="Ja."))
    ao_list.append(SCAnswerOption(uid="ao2", value="2", label="Nein."))

    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

    qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

    y = l_to_string(qsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    return qsc.gen_xml()


def example_mc_1():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Welche Kanäle haben Sie im Zuge Ihrer Informationssuche zum Promovieren an der Universität Potsdam genutzt?"),
                   HeaderInstruction(uid="ins1",
                                     content="Bitte wählen Sie alles Zutreffende aus.")]

    att_open = ZofarQuestionOpen(uid="open1", var_ref=VarRef(variable=Variable(name="ap02g", type=VAR_TYPE_STR)))

    ao_list = []
    ao_list.append(MCAnswerOption(uid="ao1", label="Webseite",
                                  var_ref=VarRef(variable=Variable(name="ap02a", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao2", label="Flyer/Broschüre",
                                  var_ref=VarRef(variable=Variable(name="ap02b", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao3", label="Info-Veranstaltung",
                                  var_ref=VarRef(variable=Variable(name="ap02c", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao4", label="Beratungsgespräch",
                                  var_ref=VarRef(variable=Variable(name="ap02d", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao5", label="Gespräch mit anderen Wissenschaftler*innen",
                                  var_ref=VarRef(variable=Variable(name="ap02e", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao6", label="Sonstige, und zwar:",
                                  var_ref=VarRef(variable=Variable(name="ap02f", type=VAR_TYPE_BOOL)),
                                  attached_open_list=[att_open]))

    # integrity check: unique uids
    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    rd = MCResponseDomain(ao_list=ao_list)

    qsc = ZofarQuestionMC(uid="qsc1", header_list=header_list, response_domain=rd)

    y = l_to_string(qsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    return qsc.gen_xml()


def example_mc_edit():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Aus welchem Grund haben Sie (bisher) keine Weiterbildungsangebote der Potsdam Graduate School besucht?"),
                   HeaderInstruction(uid="ins1",
                                     content="Bitte wählen Sie alles Zutreffende aus.")]

    ao_list = []
    ao_list.append(MCAnswerOption(uid="ao1", label="Keine Zeit",
                                  var_ref=VarRef(variable=Variable(name="ap09a", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao2", label="Format gefällt nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09b", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao3", label="Themen interessieren nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09c", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao4", label="Keine Notwendigkeit",
                                  var_ref=VarRef(variable=Variable(name="ap09d", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao5", label=" Betreuer*in unterstützt Teilnahme nicht",
                                  var_ref=VarRef(variable=Variable(name="ap09e", type=VAR_TYPE_BOOL))))
    ao_list.append(MCAnswerOption(uid="ao6", label="Zu teuer",
                                  var_ref=VarRef(variable=Variable(name="ap09f", type=VAR_TYPE_BOOL))))

    att_open = ZofarQuestionOpen(uid="open", var_ref=VarRef(variable=Variable(name="ap09g", type=VAR_TYPE_STR)))
    ao_list.append(MCAnswerOption(uid="ao7", label="Sonstige, und zwar:",
                                  var_ref=VarRef(variable=Variable(name="ap09h", type=VAR_TYPE_BOOL)),
                                  attached_open_list=[att_open]))

    # integrity check: unique uids
    assert check_for_unique_uids(ao_list)
    assert check_for_unique_uids(header_list)

    rd = MCResponseDomain(ao_list=ao_list)

    qsc = ZofarQuestionMC(uid="qsc1", header_list=header_list, response_domain=rd)

    y = l_to_string(qsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    return qsc.gen_xml()


def check_for_unique_uids(list_of_elements: List[ZofarPageObject]) -> bool:
    return len({ao.uid for ao in list_of_elements}) == len(list_of_elements)


def example_qsc_edit():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Kennen Sie PoGS-Weiterbildungsangebote für Promovierende (z.B. Programme und Workshops)?")]

    ao_list = []
    ao_list.append(SCAnswerOption(uid="ao1", value="1", label="Ja."))
    ao_list.append(SCAnswerOption(uid="ao2", value="2", label="Nein."))
    ao_list.append(SCAnswerOption(uid="ao3", value="3", label="Weiß ich nicht."))

    var_ref1 = VarRef(variable=Variable(name="ap06", type=VAR_TYPE_SC))
    rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

    qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

    y = l_to_string(qsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    return qsc.gen_xml()


def example_oq():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Kennen Sie PoGS-Weiterbildungsangebote für Promovierende (z.B. Programme und Workshops)?")]

    qo = ZofarQuestionOpen(uid="qo1", var_ref=VarRef(variable=Variable(name="ap08", type=VAR_TYPE_STR)))
    y = l_to_string(qo.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    z = y.replace('xmlns:zofar="http://www.his.de/zofar/xml/questionnaire" ', '')
    return qo.gen_xml()


if __name__ == '__main__':
    # example_qsc_1()
    # example_qsc_edit()
    # example_mc_1()
    example_mc_edit()
    # example_mqsc()
    # example_oq()
