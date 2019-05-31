import argparse
import textwrap
from otd.constants import SIMTYPE_SIMILARITY


def register_subcommand(add_parser):
    register_evaluate(add_parser)


def register_evaluate(add_parser):
    help_text = (
        "Compare the search engine's performance against a ground truth and "
        "report the achieved precision and recall."
    )

    epilog = (f"""
format of YAML file:
  query:        A mapping. The key is the query to run. The value is a list
                consisting of RDF URIs that indicate relevant datasets. They can
                either refer to concepts, in which case the ground-truth
                parameter below is used, or to datasets, in which case they are
                regarded as relevant datasets. You may combine the two however
                you like. OR is used to join the datasets and concepts.

                In addition, you can provide elements which are a mapping,
                with a key named "and" or "AND" with a list of concepts. Only
                datasets associated with all the concepts will be selected,
                using the intersection rather than the union.
                
                An example:

                electric car parking:
                  - http://example.com/datasets#ParkingPlacesInNY
                  - AND:
                      - http://example.com/concepts#Parking
                      - http://example.com/concepts#Car
                      - http://example.com/concepts#Electric
                  - http://example.com/concepts#ChargingStation

                Here, "electric car parking" is the query. The relevant datasets
                are (1) the named dataset, (2) any dataset tagged with the
                Parking, Car AND Electric concepts, and (3) any dataset tagged
                with the ChargingStation concept.
  ground-truth: A mapping with the following keys, influencing how the ground
                truth is derived from the concepts mentioned.
    threshold:  When looking at datasets that are tagged with a mentioned
                concept, this parameter decides how high the tagging score must
                be for this dataset to be considered relevant. Defaults to 0.8.
    simtype:    The dataset tagging used to find connections from concepts to
                datasets. Defaults to {SIMTYPE_SIMILARITY}.
  metadata:     A mapping. What you place here is put verbatim in the final
                results, unless it is overridden by metadata from multisearch
                or metrics. Use this to give an extra categorisation to the end
                results, or to give default values to metadata that may be
                missing when using another engine.
                
  See the help text for the 'multisearch' subcommand for the other parameters 
  available.
""")

    parser = add_parser(
        'evaluate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=help_text,
        description=textwrap.fill(help_text, width=80),
        epilog=epilog
    )

    parser.add_argument(
        'file',
        help='YAML file used to find the queries to use and determine the '
             'ground truth for what is relevant to each query. Specify a dash '
             '(-) to use stdin.',
    )

    parser.add_argument(
        '--print-relevant',
        help='Print the relevant datasets found for each query, then exit.',
        action='store_true',
    )

    parser.add_argument(
        '--multisearch-result',
        '-m',
        help='Use this in order to not run any queries, but instead just read '
             'the provided file, as if it was the output from the multisearch '
             'subcommand. The YAML document is still needed, in order to '
             'determine what datasets are relevant to each query encountered '
             'in the results.'
    )

    parser.add_argument(
        '--format',
        '-f',
        help='Choose a format to use when pretty-printing the results. See the '
             'documentation of python-tabulate for available options. '
             'Additionally, you may use the "csv" format to output a CSV file. '
             '(Default: %(default)s)',
        default='psql',
    )

    parser.set_defaults(
        func=do_evaluate,
    )


def do_evaluate(args):
    from evaluation.evaluate import parse_file, evaluate, evaluate_output, print_results, print_relevant
    variables = parse_file(args.file)

    if args.print_relevant:
        print_relevant(**variables)
    else:
        if args.multisearch_result:
            # Skip the query-running step
            with open(args.multisearch_result) as fp:
                output = fp.read()
            results = evaluate_output(output, **variables)

        else:
            # Run the queries
            results = evaluate(**variables)
        print_results(results, args.format)
