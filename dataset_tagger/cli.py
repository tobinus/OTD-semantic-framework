import argparse
import subprocess
from os.path import dirname


def register_subcommand(add_parser):
    parser = add_parser(
        'dataset_tagger',
        help="Start the webserver used for loading ontologies and "
             "connect datasets to concepts in the ontology.",
    )
    parser.add_argument(
        'gunicorn_args',
        help="Optional arguments to be given to Gunicorn, like port. Use -- "
             "before any arguments you would like to pass to Gunicorn, so they "
             "aren't confused with arguments to %(prog)s. Pass --help to see "
             "what you can do with Gunicorn. By default, the webserver will "
             "start, accepting connections from localhost on port 8000.",
        nargs=argparse.REMAINDER,
    )
    parser.set_defaults(func=run_gunicorn)


def run_gunicorn(args):
    gunicorn_args = args.gunicorn_args

    # Strip off any -- used at the beginning (they're not removed by argparse)
    if gunicorn_args and gunicorn_args[0] == '--':
        gunicorn_args = gunicorn_args[1:]

    arguments = ['gunicorn', 'app:app'] + gunicorn_args
    print(" ".join(arguments))
    subprocess.run(arguments, cwd=dirname(__file__))
