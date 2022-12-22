from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Generator, List, Union, Tuple
from qrt.util.qml import read_xml, Questionnaire
import networkx as nx
import pygraphviz


def flatten(ll: List[Union[List[Any], Tuple[Any]]]) -> Generator[Any, Any, None]:
    return (i for g in ll for i in g)


def generate_var_declarations(var_data: Dict[str, str]):
    return [f'\t\t<zofar:variable name="{varname}" type="{vartype}"/>' for varname, vartype in var_data.items()]


def qml_details(q: Questionnaire, filename: Optional[str] = None) -> Dict[str, Any]:
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

    details_dict = {}
    if filename is not None:
        details_dict['filename'] = filename
    details_dict['warnings'] = warnings_list
    details_dict['pages'] = [p.uid for p in q.pages]
    details_dict['page_questions'] = q.all_page_questions_dict()
    details_dict['all_variables_used_per_page'] = q.body_vars_per_page_dict()
    details_dict['all_variables_declared'] = q.all_vars_declared()
    details_dict['inconsistent_vartypes'] = q.vars_declared_used_inconsistent()
    details_dict['declared_but_unused_vars'] = q.vars_declared_not_used()
    details_dict['used_but_undeclared_vars'] = q.vars_used_not_declared()
    # variable declarations
    details_dict['used_but_undeclared_variables_declarations'] = generate_var_declarations(q.vars_used_not_declared())

    return details_dict


def make_flowchart(q: Questionnaire,
                   out_file: Path,
                   filename: Optional[str] = None,
                   show_var: bool = True,
                   show_cond: bool = True) -> bool:
    g = digraph(q=q, show_var=show_var, show_cond=show_cond)
    # ToDo: add filename
    a = nx.nx_agraph.to_agraph(g)
    if filename is not None:
        a.graph_attr['label'] = filename
    a.layout('dot')
    a.draw(out_file)
    return True


def digraph(q: Questionnaire,
            show_var: bool = True,
            show_cond: bool = True) -> nx.DiGraph:
    g = nx.DiGraph()
    tr_tuples = flatten([[(p.uid, t.target_uid, {'label': t.condition}) if t.condition is not None and show_cond
                          else (p.uid, t.target_uid) for t in p.transitions]
                         for p in q.pages])
    g.add_edges_from([t for t in tr_tuples])

    if show_var:
        vars_d = defaultdict(set)
        [vars_d[uid].clear() for uid in [p.uid for p in q.pages]]
        # add page variables from body to dict
        [[vars_d[p.uid].add(var.variable.name) for var in p.body_vars] for p in q.pages]
        # add page variables from triggers to dict
        [[vars_d[p.uid].add(var) for var in p.triggers_vars] for p in q.pages]
        vars_d = {k: list(v) for k, v in vars_d.items()}
        replacement_dict = {
            uid: f'{uid}\n' + ',\n'.join(
                [",".join(y) for y in [vars_d[uid][i:i + 3] for i in range(0, len(vars_d[uid]), 3)]]) for uid
            in [p.uid for p in q.pages]}
        # (vars_d[uid]) for uid in [p.uid for p in q.pages]}
        g = nx.relabel_nodes(g, replacement_dict)

    return g
