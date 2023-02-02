import datetime
import re
from collections import defaultdict, OrderedDict
from typing import Any, Dict, Optional, Generator, List, Union, Tuple

import qrt.util.questionnaire
from qrt.util.qml import Questionnaire, ZOFAR_PAGE_TAG, NS, Page
# from qrt.util.questionnaire import Questionnaire
from lxml.etree import ElementTree as lEt
from qrt.util.graph import prepare_digraph, topologically_sorted_nodes, remove_self_loops, find_cycles
import tomllib




def flatten(ll: List[Union[List[Any], Tuple[Any]]]) -> Generator[Any, Any, None]:
    return (i for g in ll for i in g)


def generate_var_declarations(var_data: Dict[str, str], name_sorted: bool = False) -> List[str]:
    if not name_sorted:
        return [f'<zofar:variable name="{varname}" type="{vartype}"/>' for varname, vartype in var_data.items()]
    else:
        return [f'<zofar:variable name="{varname}" type="{vartype}"/>' for varname, vartype in sorted(var_data.items())]


def find_json_episode_data(q: Questionnaire) -> Dict[str, Dict[str, List[str]]]:
    return {'triggers_json_reset': {p.uid: p.triggers_json_reset for p in q.pages},
            'triggers_json_load': {p.uid: p.triggers_json_load for p in q.pages},
            'triggers_json_save': {p.uid: p.triggers_json_save for p in q.pages},
            'aux_var_expl': {p.uid: [var for var in p.triggers_vars_explicit] for p in q.pages},
            'aux_var_impl': {p.uid: [var for var in p.triggers_vars_implicit] for p in q.pages}}


def qml_details(q: Questionnaire, filename: Optional[str] = None) -> Dict[str, Dict[str, Union[str, list, dict]]]:
    warnings_list = []
    vars_dict = OrderedDict()
    for page, var_list in q.body_vars_per_page_dict().items():
        for var_ref in var_list:
            if var_ref.variable.name in vars_dict:
                if var_ref.variable.type != vars_dict[var_ref.variable.name]:
                    warnings_list.append(f'variable "{var_ref.variable.name}" already found as '
                                         f'type "{vars_dict[var_ref.variable.name]}", found '
                                         f'on page "{page}" as type "{var_ref.variable.type}"')
                # else -> continue
            else:
                vars_dict[var_ref.variable.name] = var_ref.variable.type
    # ToDo: CF 2023-01-04: I do not use the above code - is it obsolete?

    g = prepare_digraph(q)
    g_cleaned = remove_self_loops(g)
    topo_sorted_pages = topologically_sorted_nodes(g_cleaned)
    cycles = find_cycles(g_cleaned)

    json_data_dict = find_json_episode_data(q)
    headers = ('page', *sorted(json_data_dict.keys()))
    json_episode_data_table = [['page', *sorted(json_data_dict.keys())]]
    for p in q.pages:
        tmp_list = [p.uid]
        for key in [*sorted(json_data_dict.keys())]:
            if p.uid in json_data_dict[key]:
                tmp_list.append(json_data_dict[key][p.uid])
            else:
                tmp_list.append(None)
        assert len(headers) == len(tmp_list)
        json_episode_data_table.append({k: v for k, v in zip(headers, tmp_list)})

    variable_declarations_per_page = '\t<zofar:variables>\n'
    variable_declarations_per_page += '\t\t' + '\n\t\t'.join(commented_var_declarations(q))
    variable_declarations_per_page += '\n\t</zofar:variables>\n'

    details_dict = OrderedDict()
    if filename is not None:
        details_dict['filename'] = {'title': 'filename',
                                    'data': filename}
    details_dict['warnings'] = {'title': 'warnings',
                                'data': warnings_list}
    details_dict['inconsistent_vartypes'] = {'title': 'inconsistent variable types',
                                             'description': 'variables that are being used as different types throughout the QML',
                                             'data': q.vars_declared_used_inconsistent()}
    details_dict['pages_order_declared'] = {'title': 'pages (in QML order)',
                                            'description': 'according to order within QML',
                                            'data': [p.uid for p in q.pages]}
    details_dict['pages_order_topological'] = {'title': 'pages (in topological order)',
                                               'description': 'empty list if topological sorting is not possible due to cycles',
                                               'data': topo_sorted_pages if topo_sorted_pages != [] else '-> cycles found!'}
    details_dict['graph_cycles'] = {'title': 'graph cycles / "loops"',
                                    'data': cycles}
    details_dict['triggers_json_reset'] = {'title': 'JSON reset triggers',
                                           'data': find_json_episode_data(q)['triggers_json_reset']}
    details_dict['triggers_json_load'] = {'title': 'JSON load triggers',
                                          'data': find_json_episode_data(q)['triggers_json_load']}
    details_dict['triggers_json_save'] = {'title': 'JSON save trigger',
                                          'data': find_json_episode_data(q)['triggers_json_save']}
    details_dict['triggers_json_table'] = {'title': 'JSON episode table',
                                           'comment': '',
                                           'data': json_episode_data_table,
                                           'table': True}
    details_dict['dead_end_pages'] = {'title': 'dead end pages',
                                      'data': q.dead_end_pages()}
    details_dict['page_questions'] = {'title': 'questions per page',
                                      'data': q.all_page_questions_dict()}
    details_dict['all_variables_used_per_page'] = {'title': 'variables per page',
                                                   'data': q.body_vars_per_page_dict()}
    details_dict['all_variables_declared'] = {'title': 'variables declared',
                                              'data': q.all_vars_declared()}
    details_dict['declared_but_unused_vars'] = {'title': 'variables declared but not used',
                                                'data': q.vars_declared_not_used()}
    details_dict['used_but_undeclared_vars'] = {'title': 'variables used but not declared',
                                                'data': q.vars_used_not_declared()}
    # variable declarations
    details_dict['used_but_undeclared_variables_declarations'] = {'title': 'declarations for missing variables',
                                                                  'data': '\n\t\t\t'.join(
                                                                      sorted(generate_var_declarations(
                                                                          q.vars_used_not_declared())))}
    details_dict['used_zofar_functions'] = {'title': 'zofar functions used',
                                            'description': 'no description yet',
                                            'data': all_zofar_functions(q)}
    details_dict['all_variables_per_type'] = {'title': 'variables per type',
                                              'description': 'variables sorted by type',
                                              'data': all_vars_per_type(q)}
    details_dict['all_var_declarations_commented_pages'] = {'title': 'all var declarations sorted per page',
                                                            'description': '',
                                                            'data': variable_declarations_per_page,
                                                            'raw': True}
    return details_dict


def commented_var_declarations(q) -> List[str]:
    output_list_per_page = []
    processed_var_names = set()
    unknown_var_types = []
    for p in q.pages:
        # page body variables
        if p.uid.find('-->') != -1:
            continue
        output_list_per_page.append('\n')
        output_list_per_page.append(f'<!-- {p.uid} -->')
        vars_dict = {var.variable.name: var.variable.type for var in p.body_vars if
                     var.variable.name not in processed_var_names}

        [output_list_per_page.append(decl) for decl in generate_var_declarations(vars_dict, name_sorted=True)]
        [processed_var_names.add(var_name) for var_name in vars_dict.keys()]

        vars_dict = {}
        for var_name in p.triggers_vars_explicit + p.triggers_vars_implicit:
            if var_name in q.all_page_body_vars():
                continue
            else:
                if var_name in processed_var_names:
                    continue
                else:
                    if var_name in q.var_declarations:
                        vars_dict.update({var_name: q.var_declarations[var_name].type})
                    else:
                        unknown_var_types.append(var_name)
        if vars_dict:
            output_list_per_page.append(f'<!-- {p.uid} TRIGGER VARIABLES -->')
            [output_list_per_page.append(decl) for decl in generate_var_declarations(vars_dict, name_sorted=True)]
            [processed_var_names.add(var_name) for var_name in vars_dict.keys()]

    output_list_other = ['\n', f'<!-- declared, but no usage found -->']
    vars_dict = {var.name: var.type for var in q.var_declarations.values() if var.name not in processed_var_names}
    [output_list_other.append(decl) for decl in generate_var_declarations(vars_dict, name_sorted=True)]

    if not unknown_var_types:
        return output_list_other + output_list_per_page
    else:
        output_list_unknown = ['\n', f'<!-- UNKNOWN VARIABLE TYPES -->']
        vars_dict = {var_name: '???' for var_name in unknown_var_types if var_name not in processed_var_names}
        [output_list_unknown.append(f'<!-- {decl} -->') for decl in
         generate_var_declarations(vars_dict, name_sorted=True)]
        [processed_var_names.add(var_name) for var_name in vars_dict.keys()]
        return output_list_unknown + output_list_other + output_list_per_page


RE_ZOFAR_FN_AS_NUMBER = re.compile(r'zofar\.asNumber\(([a-zA-Z0-9_]+)\)')
RE_ZOFAR_FN_IS_MISSING = re.compile(r'zofar\.isMissing\(([a-zA-Z0-9_]+)\)')
RE_ZOFAR_FN_VALUE = re.compile(r'([a-zA-Z0-9_]+)\.value')

RE_ALL_ZOFAR_FUNCTIONS = {'zofar.asNumber()': RE_ZOFAR_FN_AS_NUMBER,
                          'zofar.isMissing()': RE_ZOFAR_FN_IS_MISSING,
                          '.value': RE_ZOFAR_FN_VALUE}


def all_vars_per_type(q: Questionnaire) -> Dict[str, List[str]]:
    results = defaultdict(list)
    [results[var_type].append(var_name) for var_name, var_type in q.all_vars_declared().items()]
    return results


def extract_attribute_values(root: lEt, attr_name: str) -> List[str]:
    results = []
    for e in root.iterfind(ZOFAR_PAGE_TAG, NS):
        for el in e.iter():
            if hasattr(el, 'attrib'):
                if attr_name in el.attrib:
                    results.append(el.attrib[attr_name])
    return results


def all_zofar_functions(q: Questionnaire) -> Dict[str, List[str]]:
    a_c = extract_attribute_values(q.xml_root, 'condition')
    a_vc = extract_attribute_values(q.xml_root, 'visible')
    a_si = extract_attribute_values(q.xml_root, 'command')

    all_lists = a_c + a_vc + a_si
    all_str = ' '.join(all_lists)

    return {re_name: to_set_to_sorted_list(re_fn.findall(all_str)) for re_name, re_fn in RE_ALL_ZOFAR_FUNCTIONS.items()}


def to_set_to_sorted_list(in_list: List[str]) -> List[str]:
    in_list = list(set(in_list))
    in_list.sort()
    return in_list
