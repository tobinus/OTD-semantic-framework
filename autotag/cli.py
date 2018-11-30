from utils.common_cli import GraphSubcommand


subcommand = GraphSubcommand(
    'autotag',
    'autotags',
    None,
    None,
    None,
    'Autotag and similarity graphs both represent a set of connections between '
    'concepts and datasets. Autotag graphs represent the automatically created '
    'tags, created through analysis of the existing dataset metadata.'
)


def register_subcommand(add_parser):
    return subcommand.register_subcommand(add_parser)
