from utils.common_cli import register_arguments_for_rdf_output, with_rdf_output


def register_subcommand(add_parser):
    help_text = "Generate RDF for manual tagging of datasets."
    parser = add_parser(
        'create_manual_tag',
        help=help_text,
        description=help_text,
    )
    register_arguments_for_rdf_output(parser)
    parser.set_defaults(
        func=do_subcommand
    )


@with_rdf_output
def do_subcommand(args):
    from misc.manual_tag import create_manual_tag_graph
    return create_manual_tag_graph()
