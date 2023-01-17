import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, List
import networkx as nx

from qrt.util.qml import Questionnaire, flatten


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


def digraph(q: Questionnaire,
            show_var: bool = True,
            show_cond: bool = True,
            color_nodes: bool = False) -> nx.DiGraph:
    g = nx.DiGraph()
    tr_tuples = flatten([[(p.uid, t.target_uid, {'label': t.condition}) if t.condition is not None and show_cond
                          else (p.uid, t.target_uid) for t in p.transitions]
                         for p in q.pages])
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
        [[vars_d[p.uid].add(var) for var in p.triggers_vars] for p in q.pages]
        vars_d = {k: list(v) for k, v in vars_d.items()}
        replacement_dict = {
            uid: f'{uid}\n' + ',\n'.join(
                [",".join(y) for y in [vars_d[uid][i:i + 3] for i in range(0, len(vars_d[uid]), 3)]]) for uid
            in [p.uid for p in q.pages]}
        # (vars_d[uid]) for uid in [p.uid for p in q.pages]}
        g = nx.relabel_nodes(g, replacement_dict)

    return g


def make_flowchart(q: Questionnaire,
                   out_file: Path,
                   filename: Optional[str] = None,
                   show_var: bool = True,
                   show_cond: bool = True,
                   color_nodes: bool = False) -> bool:
    g = digraph(q=q, show_var=show_var, show_cond=show_cond, color_nodes=color_nodes)
    # ToDo: add filename
    a = nx.nx_agraph.to_agraph(g)
    if filename is not None:
        a.graph_attr['label'] = filename
    a.layout('dot')
    a.draw(out_file)
    return True
