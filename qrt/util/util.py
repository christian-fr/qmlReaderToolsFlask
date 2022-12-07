from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, Generator, List, Union, Tuple
from qrt.util.qml import read_xml, Questionnaire
import networkx as nx
import pygraphviz


def flatten(ll: List[Union[List[Any], Tuple[Any]]]) -> Generator[Any, Any, None]:
    return (i for g in ll for i in g)


def qml_details(q: Questionnaire, filename: Optional[str] = None) -> Dict[str, Any]:
    details_dict = {}
    if filename is not None:
        details_dict['filename'] = filename
    details_dict['pages'] = [p.uid for p in q.pages]
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
        [[vars_d[p.uid].add(var) for var in p.body_vars] for p in q.pages]
        # add page variables from triggers to dict
        [[vars_d[p.uid].add(var) for var in p.triggers_vars] for p in q.pages]
        vars_d = {k: list(v) for k, v in vars_d.items()}
        replacement_dict = {
            uid: f'{uid}\n' + ',\n'.join(
                [",".join(y) for y in [vars_d[uid][i:i + 3] for i in range(0, len(vars_d[uid]), 3)]]) for uid
            in [p.uid for p in q.pages]}
        # (vars_d[uid]) for uid in [p.uid for p in q.pages]}
        g = nx.relabel_nodes(g, replacement_dict)
        print()

    return g
