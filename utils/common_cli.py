import argparse
import subprocess


def make_subcommand_gunicorn(parser, cwd=None, module='app:app'):
    # Define the function that will start up Gunicorn with the parameters we
    # have received
    def run_gunicorn(args):
        gunicorn_args = args.gunicorn_args

        # Strip off any -- used at the beginning, they're not removed by
        # argparse
        if gunicorn_args and gunicorn_args[0] == '--':
            gunicorn_args = gunicorn_args[1:]

        arguments = ['gunicorn', module] + gunicorn_args
        print(" ".join(arguments))
        subprocess.run(arguments, cwd=cwd)

    # Collect arguments for Gunicorn
    parser.add_argument(
        'gunicorn_args',
        help='Optional arguments to be given to Gunicorn, like port. Use -- '
             'before any arguments you would like to pass to Gunicorn, so they '
             'aren\'t confused with arguments to %(prog)s. Pass --help to see '
             'what you can do with Gunicorn. By default, the webserver will '
             'start, accepting connections from localhost on port 8000.',
        nargs=argparse.REMAINDER,
    )

    # Register so we run gunicorn when this subcommand is invoked
    parser.set_defaults(func=run_gunicorn)


