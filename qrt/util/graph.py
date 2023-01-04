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


def topologically_sorted_nodes(g: nx.DiGraph) -> List[str]:
    try:
        return [node for node in nx.topological_sort(g)]
    except nx.exception.NetworkXUnfeasible:
        return []
