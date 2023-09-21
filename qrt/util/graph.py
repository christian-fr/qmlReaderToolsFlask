import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import networkx as nx
from qrt.util.qml import Questionnaire, read_xml
from qrt.util.qmlutil import flatten


def prepare_digraph(q: Questionnaire, options_dict: Optional[Dict[str, bool]] = None) -> nx.DiGraph:
    g = nx.DiGraph()
    if options_dict is None:
        options_dict = {}
    # ToDo: 2023-01-04: add options for graph: labels, etc.
    labelled_edges = flatten([[(p.uid, t.target_uid, t.condition) for t in p.transitions] for p in q.pages])
    [g.add_edges_from([(tpl[0], tpl[1])], label=tpl[2]) for tpl in labelled_edges]
    return g


def remove_self_loops(g: nx.DiGraph) -> nx.DiGraph:
    list_of_looped_edges = []
    for u, v in g.edges:
        if u == v:
            list_of_looped_edges.append((u, v))

    for u, v in list_of_looped_edges:
        g.remove_edge(u, v)
    return g


def find_cycles(g: nx.DiGraph) -> List[str]:
    try:
        return [node for node in nx.find_cycle(g)]
    except nx.exception.NetworkXNoCycle as err:
        return ['no cycle found']


def topologically_sorted_nodes(g: nx.DiGraph) -> List[str]:
    try:
        return [node for node in nx.topological_sort(g)]
    except nx.exception.NetworkXUnfeasible:
        return []


ZOFAR_REPL_LIST= [
    (re.compile(r'!([a-zA-Z0-9_\-]+)\.value\s+'), r'\1 == F '),
    (re.compile(r'!([a-zA-Z0-9_\-]+)\.value$'), r'\1 == F '),
    (re.compile(r'([a-zA-Z0-9_\-]+)\.value\s+'), r'\1 == T '),
    (re.compile(r'([a-zA-Z0-9_\-]+)\.value$'), r'\1 == T '),
    (re.compile(r'zofar\.asNumber\(([a-zA-Z0-9_\-]+)\)'), r'\1'),
    (re.compile(r'zofar\.isMissing\(([a-zA-Z0-9_\-]+)\)'), r'\1 == MIS'),
    (re.compile(r'\s+ge\s+'), r'>='),
    (re.compile(r'\s+gt\s+'), r'>'),
    (re.compile(r'\s+le\s+'), r'<='),
    (re.compile(r'\s+lt\s+'), r'<'),
    (re.compile(r'\s+!=\s+'), r'!='),
    (re.compile(r'\s+==\s+'), r'=='),
]
def repl_zofar_cond(cond_str: str):
    if cond_str is None:
        return None
    result = cond_str
    for re_s, repl_s in ZOFAR_REPL_LIST:
        result = re_s.sub(repl_s, result)
    if not (cond_str.startswith('(') and cond_str.endswith(')')):
        result = '(' + result + ')'
    return result


def combine_transition_cond(q: Questionnaire, remove_cond_false: bool = False,
                            replace_zofar_cond: bool = False) -> List[Tuple[str, str, Dict[str, str]]]:
    tr_tuples = defaultdict(list)
    for p in q.pages:
        for i, tr in enumerate(p.transitions):
            tr_condition = tr.condition
            if replace_zofar_cond:
                tr_condition = repl_zofar_cond(tr_condition)
            tr_tuples[(p.uid, tr.target_uid)].append((i, p, tr.target_uid, tr_condition))
    result = []
    for tr_u_v, tr_tuple_list in tr_tuples.items():
        cond_str_ls = []
        for index, _, _, condition in tr_tuple_list:
            if condition is None:
                cond_str_ls.append(f'[{index}]')
            else:
                cond_str = re.sub(r"\s+", " ", condition)
                cond_str_ls.append(f'[{index}] {cond_str}')
        result.append((tr_u_v[0], tr_u_v[1], {'label': ' | \n'.join(cond_str_ls)}))
    return result


def digraph(q: Questionnaire,
            show_var: bool = True,
            show_cond: bool = True,
            show_jumper: bool = True,
            color_nodes: bool = False,
            remove_cond_false: bool = True,
            replace_zofar_cond: bool = False) -> nx.DiGraph:
    g = nx.DiGraph()
    if show_cond:
        tr_tuples = combine_transition_cond(q, remove_cond_false=remove_cond_false,
                                            replace_zofar_cond=replace_zofar_cond)
    else:
        if remove_cond_false:
            tr_tuples = flatten([[(p.uid, t.target_uid, {
                'label': t.condition}) if t.condition is not None and t.condition != 'false' and show_cond
                                  else (p.uid, t.target_uid) for t in p.transitions]
                                 for p in q.pages])
        else:
            tr_tuples = flatten([[(p.uid, t.target_uid, {'label': t.condition}) if t.condition is not None and show_cond
                                  else (p.uid, t.target_uid) for t in p.transitions]
                                 for p in q.pages])

    if show_jumper:
        jj = flatten([[(p.uid, j.target) for j in p.jumpers] for p in q.pages])
        [g.add_edge(t[0], t[1], color='violet') for t in jj]
        pass

    if color_nodes:
        tr_tuples = [tp for tp in tr_tuples]
        nodes = set(flatten([tp[0:1] for tp in tr_tuples]))
        node_beginnings = list(
            {re.findall(r'^[a-zA-Z]+', node)[0] for node in nodes if re.findall(r'^[a-zA-Z]+', node)[0]})
        # remove all ambiguous beginnings
        node_beginnings = [s for s in node_beginnings if not any([s.startswith(t) for t in node_beginnings if t != s])]
        color_list = ['brown4', 'burlywood4', 'cadetblue4', 'chartreuse4', 'chocolate4', 'coral4', 'cornsilk3', 'cyan2',
                      'darkgoldenrod', 'darkgray', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred',
                      'darkseagreen3', 'darkslategray2', 'darkviolet', 'deeppink4', 'deepskyblue4', 'dodgerblue2',
                      'firebrick2', 'fuchsia', 'gold2', 'goldenrod']
        sorted(node_beginnings)
        for node_beginning_color in zip(node_beginnings, color_list):
            node_beginning, node_color = node_beginning_color
            if len(node_beginnings) > len(color_list):
                break
            else:
                [g.add_node(u, style='filled', fillcolor=node_color) for u in nodes if u.startswith(node_beginning)]
    g.add_edges_from([t for t in tr_tuples])

    if show_var:
        vars_d = defaultdict(set)
        [vars_d[uid].clear() for uid in [p.uid for p in q.pages]]
        # add page variables from body to dict
        [[vars_d[p.uid].add(var.variable.name) for var in p.body_vars] for p in q.pages]
        # add page variables from triggers to dict
        [[vars_d[p.uid].add(var) for var in p.triggers_vars_explicit] for p in q.pages]
        vars_d = {k: sorted(list(v)) for k, v in vars_d.items()}
        replacement_dict = {
            uid: f'{uid}\\n[' + ',\\n'.join(
                [",".join(y) for y in [vars_d[uid][i:i + 3] for i in range(0, len(vars_d[uid]), 3)]]) + ']' for uid
            in [p.uid for p in q.pages]}
        # (vars_d[uid]) for uid in [p.uid for p in q.pages]}
        g = nx.relabel_nodes(g, replacement_dict)

    return g


def make_flowchart(q: Questionnaire,
                   out_file: Path,
                   filename: Optional[str] = None,
                   show_var: bool = True,
                   show_cond: bool = True,
                   color_nodes: bool = False,
                   show_jumper: bool = False,
                   replace_zofar_cond: bool = False) -> bool:
    g = digraph(q=q, show_var=show_var, show_cond=show_cond, color_nodes=color_nodes, show_jumper=show_jumper,
                replace_zofar_cond=replace_zofar_cond)
    # ToDo: add filename
    a = nx.nx_agraph.to_agraph(g)
    a.node_attr['shape'] = 'box'
    if filename is not None:
        a.graph_attr['label'] = filename
    a.layout('dot')
    a.draw(out_file)
    return True


if __name__ == '__main__':
    q = read_xml(r'C:\Users\friedrich\PycharmProjects\qmlReaderToolsFlask\tests\context\questionnaire.xml')
    out_file = Path('output.png')
    make_flowchart(q, out_file=out_file, show_jumper=True, show_var=True, show_cond=True, replace_zofar_cond=True)
    pass
