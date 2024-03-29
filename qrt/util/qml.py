import argparse
import copy
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple, Any
from xml.etree import ElementTree

from lxml.etree import ElementTree as lEt
from lxml.etree import _Element as _lE
from lxml.etree import _Comment as _lC
from lxml.etree import tostring as l_to_string

from qrt.util.qmlutil import flatten, ZOFAR_NS, NS, ZOFAR_PAGE_TAG, ZOFAR_SCRIPT_ITEM_TAG, ZOFAR_SECTION_TAG, \
    ZOFAR_BODY_TAG, ZOFAR_QUESTION_OPEN_TAG, ZOFAR_CALENDAR_EPISODES_TAG, ZOFAR_CALENDAR_EPISODES_TABLE_TAG, \
    ZOFAR_SINGLE_CHOICE_TAG, ZOFAR_MULTIPLE_CHOICE_TAG, ZOFAR_MATRIX_QUESTION_OPEN_TAG, ZOFAR_MATRIX_SINGLE_CHOICE_TAG, \
    ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG, ON_EXIT_DEFAULT, DIRECTION_DEFAULT, CONDITION_DEFAULT, ZOFAR_QUESTION_ELEMENTS, \
    RE_VAL, RE_VAL_OF, RE_AS_NUM, RE_TO_LOAD, RE_TO_RESET, RE_TO_PERSIST, RE_REDIRECT_TRIG, RE_REDIRECT_TRIG_AUX
from qrt.util.questionnaire import ZofarJumper


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


@dataclass(kw_only=True)
class ScriptItem:
    value: str


# noinspection PyDataclass
@dataclass(kw_only=True)
class Trigger:
    condition: Optional[str] = 'true'
    children: List[ScriptItem] = field(default_factory=list)
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
    children = [ScriptItem(value=child.attrib['value']) for child in trigger.getchildren() if
                child.tag == ZOFAR_SCRIPT_ITEM_TAG and 'value' in child.attrib]
    if 'command' in trigger.attrib:
        return TriggerAction(command=trigger.attrib['command'],
                             on_exit=on_exit,
                             direction=direction,
                             condition=condition,
                             children=children)
    # print(ElementTree.tostring(trigger))
    raise KeyError('Key "command" not found for variable trigger.')


def variable_trigger(trigger: ElementTree.Element) -> TriggerVariable:
    if 'variable' in trigger.attrib and 'value' in trigger.attrib:
        condition = CONDITION_DEFAULT
        if 'condition' in trigger.attrib:
            condition = trigger.attrib['condition']
        children = [ScriptItem(value=child.attrib['value']) for child in trigger.getchildren() if
                    child.tag == ZOFAR_SCRIPT_ITEM_TAG and 'value' in child.attrib]
        return TriggerVariable(variable=trigger.attrib['variable'], value=trigger.attrib['value'], condition=condition,
                               children=children)
    # print(ElementTree.tostring(trigger))
    raise KeyError('Keys "variable" and/or "value" not found for variable trigger.')


def js_check_trigger(trigger: ElementTree.Element) -> TriggerJsCheck:
    if 'variable' in trigger.attrib and 'xvar' in trigger.attrib and 'yvar' in trigger.attrib:
        return TriggerJsCheck(variable=trigger.attrib['variable'], x_var=trigger.attrib['xvar'],
                              y_var=trigger.attrib['yvar'])
    # print(ElementTree.tostring(trigger))
    raise KeyError('Keys "variable" and/or "xvar" and/or "yvar" not found for variable trigger.')


def process_jumper(jumper: ElementTree.Element) -> ZofarJumper:
    value = jumper.attrib['value']
    target = jumper.attrib['target']
    return ZofarJumper(value=value, target=target.strip('/'))


def process_jumpers(page: ElementTree.Element) -> List[ZofarJumper]:
    jumpers_list = [e for e in page.iter() if e.tag == zofar_tag(NS, 'zofar', 'jumper')]
    results = [process_jumper(j) for j in jumpers_list]
    return results


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
        # raise NotImplementedError(f'triggers: tag not yet implemented: {trigger.tag}')


def process_triggers(page: ElementTree.Element) -> List[Union[TriggerVariable, TriggerAction, TriggerJsCheck]]:
    # gather all variable triggers
    triggers = page.find('./zofar:triggers', NS)
    if triggers is not None and len(triggers) > 0:
        # variable triggers
        trig_list = page.findall('./zofar:triggers/*', NS)
        if trig_list:
            return [process_trigger(trigger) for trigger in trig_list]
    return []


def triggers_json_vars_reset(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_RESET.findall(si.attrib['value']) for si in
                    triggers_action_script_items(page=page, direction=None, on_exit='false')])


def triggers_json_vars_load(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_LOAD.findall(si.attrib['value']) for si in
                    triggers_action_script_items(page=page, direction=None, on_exit='false')])


def triggers_json_vars_save(page: ElementTree.Element) -> List[str]:
    return flatten([RE_TO_PERSIST.findall(si.attrib['value']) for si in
                    triggers_action_script_items(page=page, direction=None, on_exit='true')])


def triggers_action_script_items(page: ElementTree.Element,
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
    if xml_root.find('./zofar:preloads', NS) is not None:
        pi_list = flatten([pr.findall('./zofar:preloadItem', NS) for pr in xml_root.find('./zofar:preloads', NS)])
    else:
        pi_list = []
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
    triggers_vars_explicit: List[str] = field(default_factory=list)
    triggers_vars_implicit: List[str] = field(default_factory=list)
    triggers_json_save: List[str] = field(default_factory=list)
    triggers_json_load: List[str] = field(default_factory=list)
    triggers_json_reset: List[str] = field(default_factory=list)
    visible_conditions: List[str] = field(default_factory=list)
    trig_redirect_on_exit_true: List[TriggerRedirect] = field(default_factory=list)
    trig_redirect_on_exit_false: List[TriggerRedirect] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_element: _lE = field(default_factory=_lE)
    jumpers: List[ZofarJumper] = field(default_factory=list)

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
    pages_unmasked: List[Page] = field(default_factory=list)

    def filter(self, filter_list: List[str], filter_startswith_list: List[str]) -> None:
        self.pages = [p for p in self.pages_unmasked if
                      any([p.uid.startswith(r) for r in filter_startswith_list]) or any(
                          [p.uid == r for r in filter_list])]

    # ToDo: return value? docstring!
    def collapse_pages(self, collapse_list: List[str], collapse_startswith_list: List[str]):
        pages_to_collapse = [p for p in self.pages if
                             any([p.uid.startswith(r) for r in collapse_startswith_list]) or any(
                                 [p.uid == r for r in collapse_list])]
        for page in pages_to_collapse:
            for source_page in self.pages:
                for source_transition in source_page.transitions:
                    if page.uid == source_transition.target_uid:
                        t_to_remove = []
                        for t in page.transitions:
                            source_page.transitions.append(t)
                        source_page.transitions.remove(source_transition)
                        pass

        self.pages = [p for p in self.pages if p.uid not in [p_c.uid for p_c in pages_to_collapse]]
        pass

    def remove_transitions(self, page_uid_list: List[str]):
        for page in self.pages:
            if page.uid in page_uid_list:
                page.transitions = []

    def __str__(self):
        return str([p.uid for p in self.pages[:10]] + ['...'])

    def body_vars_per_page_dict(self):
        return {p.uid: p.body_vars for p in self.pages}

    def all_page_questions_dict(self):
        return {p.uid: p.body_questions for p in self.pages}

    def all_vars_declared(self) -> Dict[str, str]:
        return {var_name: var.type for var_name, var in self.var_declarations.items()}

    def vars_declared_not_used(self) -> Dict[str, str]:
        names_missing = sorted(list(set(self.all_vars_declared().keys()).difference(self.all_page_body_vars().keys())))
        return {varname: self.all_vars_declared()[varname] for varname in names_missing}

    def vars_declared_used_inconsistent(self) -> Dict[str, List[str]]:
        results = defaultdict(set)
        for varname, vartype in self.all_page_body_vars().items():
            if varname in self.all_vars_declared().keys():
                if vartype != self.all_vars_declared()[varname]:
                    results[varname].add(vartype)
                    results[varname].add(self.all_vars_declared()[varname])
        return {k: list(v) for k, v in results.items()}

    def dead_end_pages(self):
        all_transition_targets = set(flatten([[tr.target_uid for tr in p.transitions] for p in self.pages]))
        all_pages = set([p.uid for p in self.pages])
        targets_not_found = all_transition_targets.difference(all_pages)
        lost_pages = all_pages.difference(all_transition_targets)

        # only condition="false" targets

        # all condition == '"false"' transition targets
        condition_false_transitions = set(flatten(
            [[tr.target_uid for tr in p.transitions if tr.condition is not None and tr.condition.strip() == 'false'] for
             p in self.pages]))

        # all condition != '"false"' transition targets
        condition_not_false_transitions = set(flatten(
            [[tr.target_uid for tr in p.transitions if tr.condition is None or tr.condition.strip() != 'false'] for
             p in self.pages]))
        # set difference
        only_false_conditions = condition_false_transitions.difference(condition_not_false_transitions)

        return OrderedDict({'all_pages': sorted(list(all_pages)),
                            'lost_pages': sorted(list(lost_pages)),
                            'targets_not_found': sorted(list(targets_not_found)),
                            'only_false_conditions': sorted(list(only_false_conditions))})

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
    while element.tag not in ZOFAR_QUESTION_ELEMENTS and element is not None:
        element = element.getparent()
        if not hasattr(element, 'tag'):
            return None
    return element.tag


def vars_used(page: _lE) -> List[VarRef]:
    page_uid = page.attrib['uid']
    page_body = page.find(ZOFAR_BODY_TAG, NS)
    if page_body is None:
        return []

    var_list = []
    all_var_elements = [ch for ch in page_body.iter() if 'variable' in ch.attrib]
    # ToDo: refactor this with the new questionnaire element classes!
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
                    # raise TypeError(f'Unknown variable type for {var_element=}')
                    pass

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

        p.jumpers = process_jumpers(l_page)

        p.var_ref = var_refs(l_page)
        p._triggers_list = process_triggers(l_page)
        p.body_vars = vars_used(l_page)
        p.body_questions = body_questions_vars(l_page)

        p.triggers_vars_explicit = list(
            {trig.variable for trig in p.triggers_list if isinstance(trig, TriggerVariable)})
        p.triggers_vars_explicit += list(
            set(flatten([[trig.variable, trig.x_var, trig.y_var] for trig in p.triggers_list if
                         isinstance(trig, TriggerJsCheck)])))
        p.triggers_vars_implicit = list({ch.value[len("zofar.setVariableValue('") - 1:ch.value.find(",")] for ch in
                                         flatten([trig.children for trig in p.triggers_list if
                                                  isinstance(trig, TriggerAction)]) if
                                         ch.value.startswith("zofar.setVariableValue(")})
        p.triggers_json_save = triggers_json_vars_save(l_page)
        p.triggers_json_load = triggers_json_vars_load(l_page)
        p.triggers_json_reset = triggers_json_vars_reset(l_page)
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
    #     p.triggers_vars_explicit = [trig.variable for trig in p.triggers_list if isinstance(trig, TriggerVariable)]
    #     p.trig_json_save = trig_json_vars_save(page)
    #     p.trig_json_load = trig_json_vars_load(page)
    #     p.trig_json_reset = trig_json_vars_reset(page)
    #     p.visible_conditions = visible_conditions(page)
    #
    #     p.trig_redirect_on_exit_true = redirect_triggers(p.triggers_list, 'true')
    #     p.trig_redirect_on_exit_false = redirect_triggers(p.triggers_list, 'false')
    #
    #     q.pages.append(p)

    q.pages_unmasked = q.pages.copy()

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
