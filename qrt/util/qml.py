import argparse
import copy
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, NewType, Union, Tuple, Any
import re
from xml.etree import ElementTree
from lxml.etree import ElementTree as lEt
from lxml.etree import _Element as _lE
from lxml.etree import _Comment as _lC

ZOFAR_NS = "{http://www.his.de/zofar/xml/questionnaire}"
ZOFAR_NS_URI = "http://www.his.de/zofar/xml/questionnaire"
NS = {
    "xmlns:zofar": ZOFAR_NS_URI,
    "zofar": ZOFAR_NS_URI
}
# noinspection DuplicatedCode
ZOFAR_QUESTIONNAIRE_TAG = f"{ZOFAR_NS}questionnaire"
ZOFAR_NAME_TAG = f"{ZOFAR_NS}name"
ZOFAR_PAGE_TAG = f"{ZOFAR_NS}page"
ZOFAR_TRANSITIONS_TAG = f"{ZOFAR_NS}transitions"
ZOFAR_TRANSITION_TAG = f"{ZOFAR_NS}transition"
ZOFAR_TRIGGERS_TAG = f"{ZOFAR_NS}triggers"
ZOFAR_TRIGGER_TAG = f"{ZOFAR_NS}trigger"
ZOFAR_SCRIPT_ITEM_TAG = f"{ZOFAR_NS}scriptItem"
ZOFAR_ACTION_TAG = f"{ZOFAR_NS}action"
ZOFAR_QUESTION_TAG = f"{ZOFAR_NS}question"
ZOFAR_ANSWER_OPTION_TAG = f"{ZOFAR_NS}answerOption"
ZOFAR_RESPONSE_DOMAIN_TAG = f"{ZOFAR_NS}responseDomain"
ZOFAR_INSTRUCTION_TAG = f"{ZOFAR_NS}instruction"
# noinspection DuplicatedCode
ZOFAR_INTRODUCTION_TAG = f"{ZOFAR_NS}introduction"
ZOFAR_VARIABLES_TAG = f"{ZOFAR_NS}variables"
ZOFAR_VARIABLE_TAG = f"{ZOFAR_NS}variable"
ZOFAR_SECTION_TAG = f"{ZOFAR_NS}section"
ZOFAR_HEADER_TAG = f"{ZOFAR_NS}header"
ZOFAR_BODY_TAG = f"{ZOFAR_NS}body"
ZOFAR_TITLE_TAG = f"{ZOFAR_NS}title"
ZOFAR_DISPLAY_TAG = f"{ZOFAR_NS}display"
ZOFAR_TEXT_TAG = f"{ZOFAR_NS}text"
ZOFAR_QUESTION_OPEN_TAG = f"{ZOFAR_NS}questionOpen"
ZOFAR_CALENDAR_EPISODES_TAG = f"{ZOFAR_NS}episodes"
ZOFAR_CALENDAR_EPISODES_TABLE_TAG = f"{ZOFAR_NS}episodesTable"
ZOFAR_SINGLE_CHOICE_TAG = f"{ZOFAR_NS}questionSingleChoice"
ZOFAR_MULTIPLE_CHOICE_TAG = f"{ZOFAR_NS}multipleChoice"
ZOFAR_MATRIX_QUESTION_OPEN_TAG = f"{ZOFAR_NS}matrixQuestionOpen"
ZOFAR_MATRIX_SINGLE_CHOICE_TAG = f"{ZOFAR_NS}matrixQuestionSingleChoice"
ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG = f"{ZOFAR_NS}matrixQuestionMultipleChoice"
DISPLAY_NAMESPACE = "{http://www.dzhw.eu/zofar/xml/display}"
ZOFAR_DISPLAY_TEXT_TAG = f"{DISPLAY_NAMESPACE}text"
ON_EXIT_DEFAULT = 'true'
DIRECTION_DEFAULT = 'forward'
CONDITION_DEFAULT = 'true'

ZOFAR_QUESTION_ELEMENTS = [ZOFAR_QUESTION_OPEN_TAG, ZOFAR_SINGLE_CHOICE_TAG, ZOFAR_MULTIPLE_CHOICE_TAG,
                           ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG, ZOFAR_MATRIX_QUESTION_OPEN_TAG,
                           ZOFAR_MATRIX_SINGLE_CHOICE_TAG, ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG,
                           ZOFAR_CALENDAR_EPISODES_TAG, ZOFAR_CALENDAR_EPISODES_TABLE_TAG]

RE_VAL = re.compile(r'#{([a-zA-Z0-9_]+)\.value}')
RE_VAL_OF = re.compile(r'#{zofar\.valueOf\(([a-zA-Z0-9_]+)\)}')
RE_AS_NUM = re.compile(r'#{zofar\.asNumber\(([a-zA-Z0-9_]+)\)}')

RE_TO_LOAD = re.compile(r"^\s*toLoad\.add\('([0-9a-zA-Z_]+)'\)")
RE_TO_RESET = re.compile(r"^\s*toReset\.add\('([0-9a-zA-Z_]+)'\)")
RE_TO_PERSIST = re.compile(r"^\s*toPersist\.put\('([0-9a-zA-Z_]+)',[a-zA-Z0-9_.]+\)")

RE_REDIRECT_TRIG = re.compile(r"^\s*navigatorBean\.redirect\('([a-zA-Z0-9_]+)'\)\s*$")
RE_REDIRECT_TRIG_AUX = re.compile(r"^\s*navigatorBean\.redirect\(([a-zA-Z0-9_]+)\)\s*$")


def flatten(ll):
    """
    Flattens given list of lists by one level

    :param ll: list of lists
    :return: flattened list
    """
    return [it for li in ll for it in li]


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
class ZofarQuestion(ZofarPageObject):
    type: Optional[str]
    header_list: list
    var_ref: Optional[Variable]


@dataclass(kw_only=True)
class Transition:
    target_uid: str
    condition: Optional[str] = None
    # condition as spring expression that has to be fulfilled on order to follow the transition


# forward declaration of class TriggerVariable
TriggerVariable = NewType('TriggerVariable', None)


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


def transitions(page: ElementTree.Element) -> List[Transition]:
    transitions = page.find('./zofar:transitions', NS)
    if transitions is not None and len(transitions) > 0:
        transitions_list = [t for t in transitions.getchildren() if not isinstance(t, _lC)]
        if transitions_list:
            try:
                return [
                    Transition(target_uid=t.attrib['target'],
                               condition=t.attrib['condition']) if 'condition' in t.attrib else
                    Transition(target_uid=t.attrib['target']) for t in transitions_list if not isinstance(t, _lC)]
            except KeyError as err:
                print(transitions_list)
                print([t.attrib for t in transitions_list])
                raise KeyError(err)
    return []


# noinspection SpellCheckingInspection
def extract_var_ref(input_str: str) -> List[str]:
    # find all strings that match the given regular expressions;
    #  returns list of VARNAMEs for: "#{VARNAME.value}", "#{zofar.valueOf(VARNAME)}", "#{zofar.asNumber(VARNAME)}"
    return RE_VAL.findall(input_str) + RE_VAL_OF.findall(input_str) + RE_AS_NUM.findall(input_str)


def var_refs(page: ElementTree.Element) -> List[str]:
    # get a list of all variables that are used in the texts
    texts = [element.text for element in page.iter() if element.text is not None and len(element.text) > 0]
    return list(set(flatten([extract_var_ref(text) for text in texts])))


def visible_conditions(page: ElementTree.Element) -> List[str]:
    return [element.attrib['visible'] for element in page.iter() if 'visible' in element.attrib]


def zofar_tag(ns: Dict[str, str], ns_name: str, tag_name: str) -> str:
    return f'{{{ns[ns_name]}}}{tag_name}'


def action_trigger(trigger: ElementTree.Element) -> TriggerAction:
    on_exit = None
    direction = None
    condition = CONDITION_DEFAULT
    if 'onExit' in trigger.attrib:
        on_exit = trigger.attrib['onExit']
    if 'direction' in trigger.attrib:
        direction = trigger.attrib['direction']
    if 'condition' in trigger.attrib:
        condition = trigger.attrib['condition']
    if 'command' in trigger.attrib:
        return TriggerAction(command=trigger.attrib['command'],
                             on_exit=on_exit,
                             direction=direction,
                             condition=condition)
    # print(ElementTree.tostring(trigger))
    raise KeyError('Key "command" not found for variable trigger.')


def variable_trigger(trigger: ElementTree.Element) -> TriggerVariable:
    if 'variable' in trigger.attrib and 'value' in trigger.attrib:
        condition = CONDITION_DEFAULT
        if 'condition' in trigger.attrib:
            condition = trigger.attrib['condition']
        return TriggerVariable(variable=trigger.attrib['variable'], value=trigger.attrib['value'], condition=condition)
    # print(ElementTree.tostring(trigger))
    raise KeyError('Keys "variable" and/or "value" not found for variable trigger.')


def js_check_trigger(trigger: ElementTree.Element) -> TriggerJsCheck:
    if 'variable' in trigger.attrib and 'xvar' in trigger.attrib and 'yvar' in trigger.attrib:
        return TriggerJsCheck(variable=trigger.attrib['variable'], x_var=trigger.attrib['xvar'],
                              y_var=trigger.attrib['yvar'])
    # print(ElementTree.tostring(trigger))
    raise KeyError('Keys "variable" and/or "xvar" and/or "yvar" not found for variable trigger.')


def process_trigger(trigger: ElementTree.Element) -> Union[TriggerVariable, TriggerAction, TriggerJsCheck]:
    if trigger.tag == zofar_tag(NS, 'zofar', 'action'):
        return action_trigger(trigger)
    elif trigger.tag == zofar_tag(NS, 'zofar', 'variable'):
        return variable_trigger(trigger)
    elif trigger.tag == zofar_tag(NS, 'zofar', 'jsCheck'):
        return js_check_trigger(trigger)
    else:
        print('XML string:')
        print(ElementTree.tostring(trigger))
        raise NotImplementedError(f'triggers: tag not yet implemented: {trigger.tag}')


def process_triggers(page: ElementTree.Element) -> List[Union[TriggerVariable, TriggerAction, TriggerJsCheck]]:
    # gather all variable triggers
    triggers = page.find('./zofar:triggers', NS)
    if triggers is not None and len(triggers) > 0:
        # variable triggers
        trig_list = page.findall('./zofar:triggers/*', NS)
        if trig_list:
            return [process_trigger(trigger) for trigger in trig_list]
    return []


def trig_json_vars_reset(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_RESET.findall(si.attrib['value']) for si in
                    trig_action_script_items(page=page, direction=None, on_exit='false')])


def trig_json_vars_load(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_LOAD.findall(si.attrib['value']) for si in
                    trig_action_script_items(page=page, direction=None, on_exit='false')])


def trig_json_vars_save(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_PERSIST.findall(si.attrib['value']) for si in
                    trig_action_script_items(page=page, direction=None, on_exit='true')])


def trig_action_script_items(page: ElementTree.Element,
                             direction: Optional[str],
                             on_exit: Optional[str]) -> List[ElementTree.Element]:
    act_trig = [elmnt for elmnt in page.findall('./zofar:triggers/zofar:action/zofar:scriptItem', NS)]
    return_list = []
    for element in act_trig:
        add_element = True
        if 'onExit' in element.attrib and on_exit is not None:
            if element.attrib['onExit'] != on_exit:
                add_element = False
        if 'direction' in element.attrib and direction is not None:
            if element.attrib['direction'] != direction:
                add_element = False
        if add_element:
            return_list.append(element)
    return return_list


def variables(xml_root: ElementTree.ElementTree) -> Dict[str, Variable]:
    # gather all preload variables
    pi_list = flatten([pr.findall('./zofar:preloadItem', NS) for pr in xml_root.find('./zofar:preloads', NS)])
    pl_var_list = [Variable(name='PRELOAD' + pi.attrib['variable'], type='string') for pi in pi_list]
    # gather all regular variable declarations and add preload variables, return
    reg_var_list = [Variable(name=v.attrib['name'], type=v.attrib['type']) for v in
                    xml_root.find('./zofar:variables', NS).findall('./zofar:variable', NS)]
    return {var.name: var for var in pl_var_list + reg_var_list}


def redirect_triggers(trig_list: List[Trigger], on_exit: str) -> List[TriggerRedirect]:
    filtered_trig_list = []
    for trigger in trig_list:
        if not isinstance(trigger, TriggerAction):
            continue
        if trigger.on_exit is None and on_exit == ON_EXIT_DEFAULT:
            filtered_trig_list.append(trigger)
        elif trigger.on_exit == on_exit:
            filtered_trig_list.append(trigger)

    helper_vars_list = flatten([RE_REDIRECT_TRIG_AUX.findall(trigger.command) for trigger in filtered_trig_list
                                if RE_REDIRECT_TRIG_AUX.match(trigger.command) is not None])

    aux_var_dict = {var_name: [] for var_name in helper_vars_list}
    for var in helper_vars_list:
        for trigger in trig_list:
            if isinstance(trigger, TriggerVariable) and trigger.variable == var:
                aux_var_dict[var].append((trigger.value.strip("'"), trigger.condition))

    return_list = []
    for trigger in filtered_trig_list:
        if not RE_REDIRECT_TRIG.match(trigger.command) and \
                not RE_REDIRECT_TRIG_AUX.match(trigger.command):
            continue
        if RE_REDIRECT_TRIG.match(trigger.command):
            return_list.append(
                TriggerRedirect(target_cond_list=[(RE_REDIRECT_TRIG.findall(trigger.command)[0], trigger.condition)],
                                on_exit=trigger.on_exit,
                                direction=trigger.direction))
        elif RE_REDIRECT_TRIG_AUX.match(trigger.command):
            aux_var = RE_REDIRECT_TRIG_AUX.findall(trigger.command)[0]
            return_list.append(
                TriggerRedirect(target_cond_list=aux_var_dict[aux_var],
                                on_exit=trigger.on_exit,
                                direction=trigger.direction))
    return return_list


def body_vars(page: ElementTree.Element) -> Dict[str, str]:
    page_uid = page.attrib['uid']
    return_dict = defaultdict(str)
    if page.find('./zofar:body', NS) is not None:
        assert True
        for element in page.find('./zofar:body', NS).iter():
            if element.tag == ZOFAR_BODY_TAG:
                continue
            qo_subelements = [se for se in element.iterfind('./zofar:questionOpen', NS)]
            if qo_subelements:
                # attached open found within question element
                for subelement in element.iterfind('./zofar:questionOpen', NS):
                    assert True

            if element.tag in ZOFAR_QUESTION_ELEMENTS:
                question_type = element.tag.replace(ZOFAR_NS, '')
                if element.tag == ZOFAR_QUESTION_OPEN_TAG:
                    question_var_dict = {element.attrib['variable']: question_type}
                else:
                    question_var_dict = {b.attrib['variable']: question_type for b in
                                         element.iterfind('.//*[@variable]')}
                return_dict.update(question_var_dict)
        assert True
        return return_dict
    return {}


def find_questions(parent: _lE, parent_full_uid: str, question_list: Optional[List[ZofarQuestion]] = None) -> Any:
    if question_list is None:
        question_list = []
    assert True
    for element in parent.iterchildren():
        new_parent_full_uid = parent_full_uid
        if 'uid' in element.attrib:
            new_parent_full_uid = parent_full_uid + '.' + element.attrib['uid']
        if element.tag == ZOFAR_SECTION_TAG:
            find_questions(parent=element, parent_full_uid=new_parent_full_uid, question_list=question_list)
        assert True
        question_list.append(element)
    # recursively search for questions
    return []


def body_questions_vars_lxml(page: _lE):
    page_uid = page.attrib['uid']
    if page.find(ZOFAR_BODY_TAG, NS) is None:
        return [], {}

    page_body = page.find(ZOFAR_BODY_TAG, NS)
    assert isinstance(page_body, _lE)
    list_of_questions = find_questions(page_body, page_body.attrib['uid'])

    question_type_list = []
    variable_dict = {}
    processed_list = []

    assert True
    return question_type_list, variable_dict


def body_questions_vars(page: _lE) -> Tuple[List[str], Dict[str, str]]:
    # page_uid = page.attrib['uid']
    question_type_list = []
    variable_dict = {}
    processed_list = []

    body_element = page.find(ZOFAR_BODY_TAG, NS)
    if body_element is not None:
        for element in body_element.iter():
            if element.tag in ZOFAR_QUESTION_ELEMENTS:
                sub_questions = [sc for sc in element.iter() if sc.tag in ZOFAR_QUESTION_ELEMENTS and sc != element]
                if sub_questions:
                    for sq in sub_questions:
                        if sq.tag == ZOFAR_QUESTION_OPEN_TAG:
                            question_type_list.append("questionOpen(attached)")
                        else:
                            raise NotImplementedError(f'Nested question of type "{sq.tag=}" not implemented!')

                # add question type, remove NS from tag
                question_type_list.append(element.tag.replace(ZOFAR_NS, ''))

                if element.tag == ZOFAR_SINGLE_CHOICE_TAG:
                    pass
                elif element.tag == ZOFAR_MATRIX_SINGLE_CHOICE_TAG:
                    pass
                elif element.tag == ZOFAR_QUESTION_OPEN_TAG:
                    pass
                elif element.tag == ZOFAR_MATRIX_QUESTION_OPEN_TAG:
                    pass
                elif element.tag == ZOFAR_MULTIPLE_CHOICE_TAG:
                    pass
                elif element.tag == ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG:
                    pass
                elif element.tag == ZOFAR_CALENDAR_EPISODES_TAG:
                    pass
                elif element.tag == ZOFAR_CALENDAR_EPISODES_TABLE_TAG:
                    pass
        return question_type_list, variable_dict

    if page.find('./zofar:body', NS) is not None:
        assert True
        for element in page.find('./zofar:body', NS).iter():
            if element.tag == ZOFAR_BODY_TAG:
                continue
            if element.tag in ZOFAR_QUESTION_ELEMENTS:
                if element in processed_list:
                    continue
                processed_list.append(element)
                if ZOFAR_QUESTION_OPEN_TAG in [e.tag for e in element.iter()]:
                    qo_elements = [e for e in element.iter() if e.tag == ZOFAR_QUESTION_OPEN_TAG]
                    for qo_element in qo_elements:
                        if qo_element not in processed_list:
                            question_type_list.append('questionOpen (attached)')
                            processed_list.append(qo_element)
                            if 'variable' in qo_element.attrib:
                                variable_dict[qo_element.attrib['variable']] = 'string'

                # add question type, remove NS from tag
                question_type_list.append(element.tag.replace(ZOFAR_NS, ''))

                if element.tag == ZOFAR_QUESTION_OPEN_TAG:
                    if 'variable' in element.attrib:
                        if element.attrib['variable'] in variable_dict:
                            if variable_dict[element.attrib['variable']] != 'string':
                                raise ValueError(f'Key has wrong type: variable '
                                                 f'"{element.attrib["variable"]}" found in variable_dict as '
                                                 f'"{variable_dict[element.attrib["variable"]]}", '
                                                 f'but also as string in questionOpen!')
                        else:
                            variable_dict[element.attrib['variable']] = 'string'
                else:
                    sub_elements = [e for e in element.iter() if e.tag != ZOFAR_QUESTION_OPEN_TAG]
                    for sub_element in sub_elements:
                        if hasattr(sub_element, 'iter'):
                            for sub_sub_element in sub_element.iter():
                                if hasattr(sub_sub_element, 'attrib'):
                                    if 'variable' in sub_sub_element.attrib:
                                        if sub_sub_element.tag in [ZOFAR_SINGLE_CHOICE_TAG,
                                                                   ZOFAR_MATRIX_SINGLE_CHOICE_TAG]:
                                            if sub_sub_element.attrib['variable'] in variable_dict:
                                                if variable_dict[
                                                    sub_sub_element.attrib['variable']] != 'singleChoiceAnswerOption':
                                                    raise ValueError(f'Key has wrong type: variable '
                                                                     f'"{sub_sub_element.attrib["variable"]}" found in variable_dict as '
                                                                     f'"{variable_dict[sub_sub_element.attrib["variable"]]}", '
                                                                     f'but also as singleChoiceAnswerOption!')
                                            variable_dict[
                                                sub_sub_element.attrib['variable']] = 'singleChoiceAnswerOption'
                                        if sub_sub_element.tag in [ZOFAR_MULTIPLE_CHOICE_TAG,
                                                                   ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG]:
                                            if sub_sub_element.attrib['variable'] in variable_dict:
                                                if variable_dict[sub_sub_element.attrib['variable']] != 'boolean':
                                                    raise ValueError(f'Key has wrong type: variable '
                                                                     f'"{sub_sub_element.attrib["variable"]}" found in variable_dict as '
                                                                     f'"{variable_dict[sub_sub_element.attrib["variable"]]}", '
                                                                     f'but also as boolean!')
                                            variable_dict[sub_sub_element.attrib['variable']] = 'boolean'
    return question_type_list, variable_dict


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


def get_question_parent(element: _lE) -> str:
    while element.tag not in ZOFAR_QUESTION_ELEMENTS:
        element = element.getparent()
    return element.tag


def vars_used(page: _lE) -> List[VarRef]:
    page_uid = page.attrib['uid']
    page_body = page.find(ZOFAR_BODY_TAG, NS)
    if page_body is None:
        return []

    var_list = []
    all_var_elements = [ch for ch in page_body.iter() if 'variable' in ch.attrib]
    for var_element in all_var_elements:
        condition_list = []
        element = var_element
        var_type = None
        while element.tag != ZOFAR_PAGE_TAG:
            var_name = var_element.attrib['variable']
            try:
                assert var_element is not None
            except AssertionError as err:
                print()
            question_type = get_question_parent(var_element)
            if var_type is None:
                if question_type in [ZOFAR_MULTIPLE_CHOICE_TAG, ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG]:
                    var_type = 'boolean'
                elif question_type in [ZOFAR_SINGLE_CHOICE_TAG, ZOFAR_MATRIX_SINGLE_CHOICE_TAG]:
                    var_type = 'singleChoiceAnswerOption'
                elif question_type in [ZOFAR_QUESTION_OPEN_TAG, ZOFAR_MATRIX_QUESTION_OPEN_TAG,
                                       ZOFAR_CALENDAR_EPISODES_TAG, ZOFAR_CALENDAR_EPISODES_TABLE_TAG]:
                    var_type = 'string'
                else:
                    raise TypeError(f'Unknown variable type for {var_element=}')

            if 'condition' in element.attrib:
                condition_list.append(element.attrib['condition'])
            element = element.getparent()

        var_list.append(VarRef(variable=Variable(name=var_name, type=var_type), condition=condition_list))
    return var_list


def read_xml(xml_path: Path) -> Questionnaire:
    xml_root = ElementTree.parse(xml_path)
    lxml_root = lEt(file=xml_path)
    q = Questionnaire()
    q.xml_root = copy.deepcopy(lxml_root)
    q.var_declarations = variables(xml_root)

    for l_page in lxml_root.iterfind(ZOFAR_PAGE_TAG, NS):
        p = Page(l_page.attrib['uid'])

        p.body_vars = vars_used(l_page)
        # tmp_q, tmp_v = body_questions_vars_lxml(l_page)
        p = Page(l_page.attrib['uid'])

        p.transitions = transitions(l_page)
        p.var_ref = var_refs(l_page)
        p._triggers_list = process_triggers(l_page)
        p.body_vars = vars_used(l_page)
        p.body_questions = body_questions_vars(l_page)

        p.triggers_vars = [trig.variable for trig in p.triggers_list if isinstance(trig, TriggerVariable)]
        p.trig_json_save = trig_json_vars_save(l_page)
        p.trig_json_load = trig_json_vars_load(l_page)
        p.trig_json_reset = trig_json_vars_reset(l_page)
        p.visible_conditions = visible_conditions(l_page)

        p.trig_redirect_on_exit_true = redirect_triggers(p.triggers_list, 'true')
        p.trig_redirect_on_exit_false = redirect_triggers(p.triggers_list, 'false')

        q.pages.append(p)

    # for page in xml_root.findall('./zofar:page', NS):
    #     continue
    #     p = Page(page.attrib['uid'])
    #
    #     p.transitions = transitions(page)
    #     p.var_ref = var_refs(page)
    #     p._triggers_list = process_triggers(page)
    #
    #     p.triggers_vars = [trig.variable for trig in p.triggers_list if isinstance(trig, TriggerVariable)]
    #     p.trig_json_save = trig_json_vars_save(page)
    #     p.trig_json_load = trig_json_vars_load(page)
    #     p.trig_json_reset = trig_json_vars_reset(page)
    #     p.visible_conditions = visible_conditions(page)
    #
    #     p.trig_redirect_on_exit_true = redirect_triggers(p.triggers_list, 'true')
    #     p.trig_redirect_on_exit_false = redirect_triggers(p.triggers_list, 'false')
    #
    #     q.pages.append(p)

    return q


def main(xml_file: str):
    q = read_xml(Path(xml_file))
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-i', '--xml-file', help='The path of the XML input')
    ns = parser.parse_args()
    main(**ns.__dict__)

    pass
