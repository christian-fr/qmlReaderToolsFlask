import os.path
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, NewType, Union, Tuple
import re
from xml.etree import ElementTree

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
                           ZOFAR_MATRIX_SINGLE_CHOICE_TAG, ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG]

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


@dataclass
class Transition:
    target_uid: str
    # condition as spring expression that has to be fulfilled on order to follow the transition
    condition: Optional[str] = None


@dataclass
class Variable:
    name: str
    type: str


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


@dataclass
class VarRef:
    variable: Variable
    # list of conditions (as spring expression) that have to be fulfilled in order to reach the variable reference
    condition: List[str] = field(default_factory=list)


@dataclass
class EnumValue:
    uid: str
    value: int
    label: str


@dataclass
class EnumValues:
    variable: Variable
    values: List[EnumValue]


def transitions(page: ElementTree.Element) -> List[Transition]:
    transitions_list = page.find('./zofar:transitions', NS)
    if transitions_list:
        return [Transition(t.attrib['target'], t.attrib['condition']) if 'condition' in t.attrib else
                Transition(t.attrib['target']) for t in transitions_list]
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
    print(ElementTree.tostring(trigger))
    raise KeyError('Key "command" not found for variable trigger.')


def variable_trigger(trigger: ElementTree.Element) -> TriggerVariable:
    if 'variable' in trigger.attrib and 'value' in trigger.attrib:
        condition = CONDITION_DEFAULT
        if 'condition' in trigger.attrib:
            condition = trigger.attrib['condition']
        return TriggerVariable(variable=trigger.attrib['variable'], value=trigger.attrib['value'], condition=condition)
    print(ElementTree.tostring(trigger))
    raise KeyError('Keys "variable" and/or "value" not found for variable trigger.')


def js_check_trigger(trigger: ElementTree.Element) -> TriggerJsCheck:
    if 'variable' in trigger.attrib and 'xvar' in trigger.attrib and 'yvar' in trigger.attrib:
        return TriggerJsCheck(variable=trigger.attrib['variable'], x_var=trigger.attrib['xvar'],
                              y_var=trigger.attrib['yvar'])
    print(ElementTree.tostring(trigger))
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
    if triggers:
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
    pl_var_list = [Variable('PRELOAD' + pi.attrib['variable'], 'string') for pi in pi_list]
    # gather all regular variable declarations and add preload variables, return
    reg_var_list = [Variable(v.attrib['name'], v.attrib['type']) for v in
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


def body_questions_vars(page: ElementTree.Element) -> Tuple[List[str], Dict[str, str]]:
    page_uid = page.attrib['uid']
    question_type_list = []
    variable_dict = {}
    processed_list = []
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

                question_type = element.tag.replace(ZOFAR_NS, '')
                question_type_list.append(question_type)

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
                                        if sub_sub_element.tag in [ZOFAR_SINGLE_CHOICE_TAG, ZOFAR_MATRIX_SINGLE_CHOICE_TAG]:
                                            if sub_sub_element.attrib['variable'] in variable_dict:
                                                if variable_dict[sub_sub_element.attrib['variable']] != 'singleChoiceAnswerOption':
                                                    raise ValueError(f'Key has wrong type: variable '
                                                                     f'"{sub_sub_element.attrib["variable"]}" found in variable_dict as '
                                                                     f'"{variable_dict[sub_sub_element.attrib["variable"]]}", '
                                                                     f'but also as singleChoiceAnswerOption!')
                                            variable_dict[sub_sub_element.attrib['variable']] = 'singleChoiceAnswerOption'
                                        if sub_sub_element.tag in [ZOFAR_MULTIPLE_CHOICE_TAG, ZOFAR_MATRIX_MULTIPLE_CHOICE_TAG]:
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
    body_vars: Dict[str, str] = field(default_factory=dict)
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

    @property
    def triggers_list(self):
        return self._triggers_list


@dataclass
class Questionnaire:
    pages: List[Page] = field(default_factory=list)
    var_declarations: Dict[str, Variable] = field(default_factory=list)

    def all_page_body_vars_dict(self):
        return {p.uid: p.body_vars for p in self.pages}

    def all_page_questions_dict(self):
        return {p.uid: p.body_questions for p in self.pages}



def read_xml(xml_path: Path) -> Questionnaire:
    xml_root = ElementTree.parse(xml_path)
    q = Questionnaire()

    q.var_declarations = variables(xml_root)

    for page in xml_root.findall('./zofar:page', NS):
        p = Page(page.attrib['uid'])

        p.transitions = transitions(page)
        p.var_ref = var_refs(page)
        p._triggers_list = process_triggers(page)
        p.body_questions, p.body_vars = body_questions_vars(page)
        p.triggers_vars = [trig.variable for trig in p.triggers_list if isinstance(trig, TriggerVariable)]
        p.trig_json_save = trig_json_vars_save(page)
        p.trig_json_load = trig_json_vars_load(page)
        p.trig_json_reset = trig_json_vars_reset(page)
        p.visible_conditions = visible_conditions(page)

        p.trig_redirect_on_exit_true = redirect_triggers(p.triggers_list, 'true')
        p.trig_redirect_on_exit_false = redirect_triggers(p.triggers_list, 'false')

        q.pages.append(p)

    return q


if __name__ == '__main__':
    input_xml = Path(r'C:\Users\friedrich\zofar_workspace\slc_stube22-2\src\main\resources\questionnaire.xml')
    questionnaire = read_xml(input_xml)
    pass
