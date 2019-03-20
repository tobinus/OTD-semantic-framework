from otd.skosnavigate import SKOSNavigate
from similarity.csv_parse import get_fragment
from db import graph


def get_concept_list(uuid=None):
    lines = []
    navigator = SKOSNavigate(graph.Ontology.from_uuid(uuid).graph)
    indent = '  '

    def do_node(node, visited_nodes, depth):
        this_outer_indent = indent * depth
        lines.append(f'{this_outer_indent}<li>')

        depth += 1
        this_inner_indent = indent * depth

        lines.append(f'{this_inner_indent}{get_fragment(str(node))}')
        children = tuple(sorted(navigator.find_children(node)))

        if node not in visited_nodes and len(children):
            lines.append(f'{this_inner_indent}<ul>')
            for child in children:
                do_node(child, visited_nodes | {node}, depth + 1)
            lines.append(f'{this_inner_indent}</ul>')

        lines.append(f'{this_outer_indent}</li>')

    lines.append('<ul>')
    do_node(navigator.find_root(), set(), 1)
    lines.append('</ul>')

    return '\n'.join(lines)
