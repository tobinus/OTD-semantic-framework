import csv
from utils.common_cli import GraphSubcommand, register_arguments_for_rdf_output, \
    with_rdf_output


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
    parser, subcommands = subcommand.register_subcommand(add_parser)
    register_import_command(subcommands.add_parser)


def register_import_command(add_parser):
    parser = add_parser(
        'parse',
        help='Create RDF graph out of manual tagging done as CSV.',
        description='Create RDF graph out of manual tagging done as CSV. '
                    'The first row should be column labels, with "Dataset" '
                    'denoting the column with dataset URIs, and either '
                    '"Concepts" has a comma-separated list of concepts (either '
                    'full or just the identifying part of the concept URI), or '
                    'each concept has its own column, where any non-empty cells'
                    ' indicate an association.',
    )
    parser.add_argument(
        '--dialect',
        '-d',
        help='The dialect to use when parsing the CSV file. '
             '(Default: %(default)s)',
        choices=csv.list_dialects(),
        default='excel',
    )
    parser.add_argument(
        'csv_file',
        help='Path to CSV file to convert to RDF.',
    )
    register_arguments_for_rdf_output(parser)
    parser.set_defaults(
        func=do_import_command
    )


@with_rdf_output
def do_import_command(args):
    from similarity.parse import csv2rdf
    with open(args.csv_file, 'r', newline='') as csv_fn:
        return csv2rdf(csv_fn, args.dialect)

