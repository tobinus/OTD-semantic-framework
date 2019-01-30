from otd.skosnavigate import SKOSNavigate
from similarity.csv_parse import get_fragment
from utils.graph import create_bound_graph


def sort_turtle(prefix, identifiers, file_in, file_out):
    with open(file_in, encoding='utf8') as fd:
        line_iter = iter(fd)

        entities = dict()
        preamble_finished = False

        preamble = []
        while not preamble_finished:
            line = next(line_iter)
            preamble.append(line)
            if line.strip() == "":
                preamble_finished = True

        extra = []
        try:
            while True:
                line = next(line_iter)
                if line.strip == "":
                    # Extra blank lines between entities
                    continue
                if not line.startswith(prefix):
                    # We don't recognize this, just put it in the end
                    extra.append(line)
                    continue
                # If we are here, then we recognize this line as the first for a
                # subject. Its identifier is from after the prefix, until space.
                this_id = line.split()[0][len(prefix):]
                this_entitity = []
                entities[this_id] = this_entitity

                # do-while loop
                this_entitity.append(line)
                while line.strip() != "":
                    line = next(line_iter)
                    this_entitity.append(line)

        except StopIteration:
            # End of file
            pass

    # Add to file in order given by identifiers
    sorted_lines = list()
    sorted_lines.extend(preamble)
    for ent_id in identifiers:
        if ent_id in entities:
            sorted_lines.extend(entities[ent_id])
            entities.pop(ent_id)
        else:
            print('Identifier', ent_id, 'not found in turtle file')

    remaining_entities = sorted(entities.items())
    for _, lines in remaining_entities:
        sorted_lines.extend(lines)

    if extra:
        sorted_lines.append('\n')
        sorted_lines.extend(extra)

    with open(file_out, mode="w", encoding="utf8") as fd:
        fd.writelines(sorted_lines)


def get_concepts_sorted(file_in):
    identifiers = []

    g = create_bound_graph()
    g.parse(location=file_in, format="turtle")
    navigator = SKOSNavigate(g)

    def do_node(node, visited_nodes):
        identifiers.append(get_fragment(str(node)))

        children = tuple(sorted(navigator.find_children(node)))

        if node not in visited_nodes and len(children):
            for child in children:
                do_node(child, visited_nodes | {node})
        elif node in visited_nodes:
            print('Cycle detected for nodes', visited_nodes, 'at node', node)

    do_node(navigator.find_root(), set())

    return identifiers
