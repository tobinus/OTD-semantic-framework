import argparse
import subprocess
from os.path import dirname


def register_subcommand(add_parser):
    parser = add_parser(
        'dataset_tagger',
        help="Start the webserver used for loading ontologies and "
             "connect datasets to concepts in the ontology.",
    )
    # TODO: Make it possible to pass arguments to Gunicorn
    parser.add_argument(
        'gunicorn_args',
        help="Optional arguments to be given to gunicorn, like port.",
        nargs=argparse.REMAINDER,
    )
    parser.set_defaults(func=run_gunicorn)


def run_gunicorn(args):
    arguments = ['gunicorn', 'app:app'] + args.gunicorn_args
    print(args.gunicorn_args)
    subprocess.run(arguments, cwd=dirname(__file__))
