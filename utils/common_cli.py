import argparse
import functools


def make_subcommand_gunicorn(parser, cwd=None, module='app:app'):
    # Define the function that will start up Gunicorn with the parameters we
    # have received
    def run_gunicorn(args):
        import subprocess
        import signal
        import sys

        gunicorn_args = args.gunicorn_args

        # Strip off any -- used at the beginning, they're not removed by
        # argparse
        if gunicorn_args and gunicorn_args[0] == '--':
            gunicorn_args = gunicorn_args[1:]

        # Combine our arguments with optional arguments from user
        arguments = ['gunicorn', module] + gunicorn_args

        # Print preview of the command we'll run, so user can see how their
        # arguments were understood.
        print(" ".join(arguments))

        # We want only Gunicorn, not us, to react to CTRL+C or kill, so that we
        # can propagate its return code. We do this by ignoring the signals in
        # this program (Gunicorn overrides those signal handlers)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        # Run Gunicorn!
        result = subprocess.run(arguments, cwd=cwd)

        # Propagate return code from Gunicorn
        sys.exit(result.returncode)

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


available_rdflib_formats = (
    'n3',
    'nquads',
    'nt',
    'pretty-xml',
    'trig',
    'trix',
    'turtle',
    'xml',
    'json-ld',
)


def register_arguments_for_rdf_output(parser):
    parser.add_argument(
        '--out',
        '-o',
        help='Where to save the serialized graph. By default, it is printed to '
             'stdout.',
        default='-',
    )
    parser.add_argument(
        '--format',
        '-f',
        help='Format to use for rendering the RDF graph. See '
             'https://rdflib.readthedocs.io/en/stable/plugin_serializers.html '
             'for available options, plus json-ld. (Default: %(default)s)',
        choices=available_rdflib_formats,
        default='xml',
    )


def with_rdf_output(func):
    @functools.wraps(func)
    def wrapped_function(args):
        graph = func(args)
        if args.out == '-':
            serialized_graph = graph.serialize(format=args.format)
            print(serialized_graph.decode('utf8'), end='')
        else:
            graph.serialize(args.out, format=args.format)
    return wrapped_function

