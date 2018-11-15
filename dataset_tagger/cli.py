from os.path import dirname
from utils.common_cli import make_subcommand_gunicorn


def register_subcommand(add_parser):
    parser = add_parser(
        'dataset_tagger',
        help="Start the webserver used for loading ontologies and "
             "connect datasets to concepts in the ontology.",
    )
    make_subcommand_gunicorn(
        parser,
        dirname(dirname(__file__)),
        'dataset_tagger.app:app'
    )
