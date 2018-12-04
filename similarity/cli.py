import csv
from utils.common_cli import GraphSubcommand, \
    register_arguments_for_rdf_output, \
    with_rdf_output


def do_generate(_):
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
    register_csv_parse_command(subcommands.add_parser)
    register_csv_prepare_command(subcommands.add_parser)


def register_csv_parse_command(add_parser):
    parser = add_parser(
        'csv_parse',
        help='Create RDF graph out of manual tagging done as CSV.',
        description='Create RDF graph out of manual tagging done as CSV. '
                    'The first row should be column labels, with "Dataset" '
                    'denoting the column with dataset URIs, and either '
                    '"Concepts" has a comma-separated list of concepts (either '
                    'full or just the identifying part of the concept URI), or '
                    'each concept has its own column, where any non-empty cells'
                    ' indicate an association. If you use the csv_prepare '
                    'command, you get a properly formatted CSV to fill in.',
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
        func=do_csv_parse_command
    )


@with_rdf_output
def do_csv_parse_command(args):
    from similarity.csv_parse import csv2rdf
    with open(args.csv_file, 'r', newline='') as csv_fn:
        return csv2rdf(csv_fn, args.dialect)


def register_csv_prepare_command(add_parser):
    help_text = (
        'Prepare CSV file which can be filled out and imported as a new '
        'similarity graph.'
    )
    parser = add_parser(
        'csv_prepare',
        help=help_text,
        description=help_text
    )
    parser.add_argument(
        '--dialect',
        '-d',
        help='The dialect to use when writing the CSV file. '
             '(Default: %(default)s)',
        choices=csv.list_dialects(),
        default='excel',
    )
    parser.add_argument(
        'csv_file',
        help='Path to the CSV file to create.',
    )
    parser.set_defaults(
        func=do_csv_prepare_command
    )


def do_csv_prepare_command(args):
    from similarity.csv_prepare import prepare_csv
    with open(args.csv_file, 'w', newline='') as csv_fn:
        prepare_csv(csv_fn, args.dialect)
