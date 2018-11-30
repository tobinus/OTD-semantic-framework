from utils.common_cli import GraphSubcommand


def do_generate(args):
    from similarity.generate import create_manual_tag_graph
    return create_manual_tag_graph()


subcommand = GraphSubcommand(
    'similarity',
    'similarities',
    None,
    None,
    do_generate,
    'Similarity and autotag graphs both represent a set of connections between '
    'concepts and datasets. Similarity graphs represent the manually curated '
    'connections, enriching the dataset metadata.'
)


def register_subcommand(add_parser):
    return subcommand.register_subcommand(add_parser)
