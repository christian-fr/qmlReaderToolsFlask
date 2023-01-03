from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, NewType, Union
# noinspection PyProtectedMember
from lxml.etree import _Element as _lE, ElementTree as lEt

ON_EXIT_DEFAULT = 'true'
DIRECTION_DEFAULT = 'forward'
CONDITION_DEFAULT = 'true'

# forward declaration of class TriggerVariable
TriggerVariable = NewType('TriggerVariable', None)
ZofarPageObject = NewType('ZofarPageObject', None)
Section = NewType('Section', None)


@dataclass(kw_only=True)
class ZofarPageObject:
    uid: str
    parent_uid: str
    full_uid: str
    visible: str


@dataclass(kw_only=True)
class Variable:
    name: str
    type: str


@dataclass(kw_only=True)
class HeaderObject(ZofarPageObject):
    type: str
    content: str


@dataclass(kw_only=True)
class HeaderTitle(ZofarPageObject):
    type: str = 'title'


@dataclass(kw_only=True)
class HeaderText(ZofarPageObject):
    type: str = 'text'


@dataclass(kw_only=True)
class HeaderQuestion(ZofarPageObject):
    type: str = 'question'


@dataclass(kw_only=True)
class HeaderIntroduction(ZofarPageObject):
    type: str = 'introduction'


@dataclass(kw_only=True)
class HeaderInstruction(ZofarPageObject):
    type: str = 'instruction'


@dataclass(kw_only=True)
class Section(ZofarPageObject):
    header_list: list
    children: Optional[List[Union[ZofarPageObject, Section]]]
    type: str = 'section'


@dataclass(kw_only=True)
class AnswerOption(ZofarPageObject):
    label: Optional[str]
    value: Optional[str]
    missing: Optional[bool] = False


@dataclass(kw_only=True)
class Item(ZofarPageObject):
    type: Optional[str]
    header_list: List[HeaderObject]
    var_ref: Optional[Variable]
    children: Optional[List[AnswerOption]]


@dataclass(kw_only=True)
class Question(ZofarPageObject):
    type: Optional[str]
    header_list: List[HeaderObject]
    var_ref: Optional[Variable]
    children: Optional[List[ZofarPageObject]]


@dataclass(kw_only=True)
class ZofarQuestionOpen(Question):
    type: str = 'questionOpen'


@dataclass(kw_only=True)
class ZofarQuestionSC(Question):
    ao_list: List[AnswerOption]
    type: str = 'questionSingleChoice'


@dataclass(kw_only=True)
class ZofarQuestionMC(Question):
    type: str = 'multipleChoice'


@dataclass(kw_only=True)
class ZofarQuestionMCMatrix(Question):
    title_header: List[ZofarPageObject]
    missing_header: List[ZofarPageObject]
    type: str = 'matrixMultipleChoice'


@dataclass(kw_only=True)
class ZofarQuestionSCMatrix(Question):
    type: str = 'matrixSingleChoice'


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
