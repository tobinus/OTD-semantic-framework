import argparse


def register_subcommand(add_parser):
    help_text = 'Perform a multi-search using an external search engine.'
    parser = add_parser(
        'ext-multisearch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=help_text,
        description=help_text,
        epilog=f"""
format of YAML file:
  configuration: List of UUID of the configurations to use when running the
                 queries. Since the configuration is only used to recognize
                 datasets, it doesn't make much sense to list more than one.
  query:  Either list of queries, or a mapping where the queries are used as
          keys. The values of the mapping are ignored by this script.
  google: Mapping with configuration options for Google Dataset Search.
  google.site: Site filter to apply to a Google Dataset Search search. Works
               just like the "site:" operator in the normal search. Defaults to
               no filter.

output format: See the documentation for multisearch.
        """
    )
    parser.add_argument(
        'engine',
        choices=['google'],
        help='The search engine to use.'
    )
    parser.add_argument(
        'file',
        type=argparse.FileType('r'),
        help='YAML file used to derive the queries to use. Specify a dash (-) '
             'to use stdin.'
    )
    parser.set_defaults(
        func=do_ext_multisearch
    )


def do_ext_multisearch(args):
    from ontosearch.ext_search.ext_search import do_ext_multi_search
    return do_ext_multi_search(args.engine, args.file)


