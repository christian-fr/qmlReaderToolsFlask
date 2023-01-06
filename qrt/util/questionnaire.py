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
ZofarQuestionOpen = NewType('ZofarQuestionOpen', None)
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


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderText(HeaderObject):
    type: str = 'text'


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


# noinspection PyDataclass
@dataclass(kw_only=True)
class HeaderInstruction(HeaderObject):
    type: str = 'instruction'


# noinspection PyDataclass
@dataclass(kw_only=True)
class Section(ZofarPageObject):
    header_list: list
    children: List[Union[ZofarPageObject, Section]] = field(default_factory=list)
    type: str = 'section'


# noinspection PyDataclass
@dataclass(kw_only=True)
class ResponseDomain:
    uid: str
    header_list: List[HeaderObject] = field(default_factory=list)


# noinspection PyDataclass
@dataclass(kw_only=True)
class AnswerOption(ZofarPageObject):
    label: Optional[str]
    value: Optional[str]
    missing: Optional[bool] = False
    var_ref: Optional[VarRef] = None
    attached_open_list: List[ZofarQuestionOpen] = field(default_factory=list)

    def gen_xml(self) -> _lE:
        return AO(uid=self.uid, label=self.label, visible=self.visible, value=self.value)


# noinspection PyDataclass
@dataclass(kw_only=True)
class MCAnswerOption(AnswerOption):
    var_ref: VarRef


# noinspection PyDataclass
@dataclass(kw_only=True)
class SCResponseDomain(ResponseDomain):
    var_ref: VarRef
    ao_list: List[AnswerOption]
    uid: str = 'rd'
    item_classes: bool = True
    # for dropDown
    rd_type: Optional[str] = None

    def get_var_refs(self):
        raise NotImplementedError


# noinspection PyDataclass
@dataclass(kw_only=True)
class MCResponseDomain(ResponseDomain):
    ao_list: List[MCAnswerOption] = field(default_factory=list)

    def get_var_refs(self):
        raise NotImplementedError


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
class Question(ZofarPageObject):
    type: Optional[str]
    var_ref: Optional[VarRef] = None
    header_list: List[HeaderObject] = field(default_factory=list)


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionOpen(Question):
    var_ref: VarRef
    type: str = 'questionOpen'


# noinspection PyDataclass
@dataclass(kw_only=True)
class ZofarQuestionSC(Question):
    response_domain: SCResponseDomain
    type: str = 'questionSingleChoice'

    def get_var_refs(self) -> List[VarRef]:
        return [self.response_domain.var_ref]

    def gen_xml(self) -> _lE:
        if self.response_domain.rd_type is not None:
            if self.response_domain.rd_type == SC_TYPE_DROPDOWN:
                return QSC(HEADER(*[h.gen_xml() for h in self.header_list]),
                           RD(*[ao.gen_xml() for ao in self.response_domain.ao_list],
                              variable=self.response_domain.var_ref.variable.name,
                              type=SC_TYPE_DROPDOWN,
                              itemClasses=str(self.response_domain.item_classes).lower()),
                           uid=self.uid, visible=self.visible)
        return QSC(HEADER(*[h.gen_xml() for h in self.header_list]),
                   RD(*[ao.gen_xml() for ao in self.response_domain.ao_list],
                      variable=self.response_domain.var_ref.variable.name,
                      itemClasses=str(self.response_domain.item_classes).lower()),
                   uid=self.uid, visible=self.visible)


@dataclass(kw_only=True)
class ZofarQuestionMC(Question):
    type: str = 'multipleChoice'


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

    title_header = []
    title_header.append(HeaderTitle(uid="ti1", content="trifft völlig zu"))
    title_header.append(HeaderTitle(uid="ti2", content="trifft eher zu"))
    title_header.append(HeaderTitle(uid="ti3", content="teils / teils"))
    title_header.append(HeaderTitle(uid="ti4", content="trifft eher nicht zu"))
    title_header.append(HeaderTitle(uid="ti5", content="trifft gar nicht zu"))

    ao_list_it = []
    ao_list_it.append(AnswerOption(uid='ao1', value="1", label="trifft völlig zu"))
    ao_list_it.append(AnswerOption(uid='ao2', value="2", label="trifft eher zu"))
    ao_list_it.append(AnswerOption(uid='ao3', value="3", label="teils / teils"))
    ao_list_it.append(AnswerOption(uid='ao4', value="4", label="trifft eher nicht zu"))
    ao_list_it.append(AnswerOption(uid='ao5', value="5", label="trifft gar nicht zu"))

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
                                 title_header=title_header)
    y = l_to_string(mqsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    return mqsc


def example_qsc_1():
    header_list = [HeaderQuestion(uid="q1",
                                  content="Haben Sie sich an der Universität Potsdam vor Beginn Ihrer Promotion zum Thema Promovieren informiert?")]

    ao_list = []
    ao_list.append(AnswerOption(uid="ao1", value="1", label="Ja."))
    ao_list.append(AnswerOption(uid="ao2", value="2", label="Nein."))

    var_ref1 = VarRef(variable=Variable(name="foc680", type=VAR_TYPE_SC))
    rd = SCResponseDomain(var_ref=var_ref1, ao_list=ao_list)

    qsc = ZofarQuestionSC(uid="qsc1", header_list=header_list, response_domain=rd)

    y = l_to_string(qsc.gen_xml(), pretty_print=True, encoding='utf-8').decode('utf-8')
    return qsc.gen_xml()


if __name__ == '__main__':
    example_qsc_1()
    example_mqsc()
