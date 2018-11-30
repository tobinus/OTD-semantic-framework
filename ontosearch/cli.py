from os.path import dirname
from utils.common_cli import make_subcommand_gunicorn


def register_subcommand(add_parser):
    parser = add_parser(
        'serve',
        help='Start the webserver for searching ontologies.',
    )
    make_subcommand_gunicorn(parser, dirname(dirname(__file__)), 'ontosearch.app:app')
