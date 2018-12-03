import argparse
import sys
import os
import functools


class BrokenPipeHandling:
    """
    Handle broken pipes, which occur when piping to another program which ends
    before reading everything.

    This will stop the program if a broken pipe occurs, and suppress any
    exception that would normally have occurred, had you not handled broken
    pipes.

    Based on https://docs.python.org/3/library/signal.html#note-on-sigpipe
    """
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # There might be a broken pipe incoming, so try to make it happen
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except BrokenPipeError:
                exc_type = BrokenPipeError

        if exc_type is BrokenPipeError:
            # Whatever read our output closed on us, prepare for final flush
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            os.dup2(devnull, sys.stderr.fileno())
            # Python flushes when exiting. We exit with error
            sys.exit(1)


def make_subcommand_gunicorn(parser, cwd=None, module='app:app', pre_hook=None):
    # Define the function that will start up Gunicorn with the parameters we
    # have received
    def run_gunicorn(args):
        if pre_hook is not None:
            pre_hook(args)
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


class GraphSubcommand:
    SKOS_RDF_LOCATION = 'https://www.w3.org/2009/08/skos-reference/skos.rdf'

    def __init__(
            self,
            key,
            plural,
            adjust_loaded_graph=None,
            adjust_parsers=None,
            graph_generate_func=None,
            description=''
    ):
        self.key = key
        self.plural = plural
        self.adjust_loaded_graph = adjust_loaded_graph
        self.adjust_parsers = adjust_parsers
        self.graph_generate_func = graph_generate_func
        self.description = description
        self.__db_graph = None
        self.__utils_graph = None

    @property
    def _db_graph(self):
        if self.__db_graph is None:
            from db import graph
            self.__db_graph = graph
        return self.__db_graph

    @property
    def _utils_graph(self):
        if self.__utils_graph is None:
            from utils import graph
            self.__utils_graph = graph
        return self.__utils_graph

    def insert_potentially_new_graph(
            self,
            uuid=False,
            location=None,
            format=None,
            args=None
    ):
        if uuid is not False:
            return self._insert_graph(uuid, location, format, args)
        else:
            return self._insert_new_graph(location, format, args)

    def _insert_graph(self, uuid, location=None, format=None, args=None):
        g = self._parse_graph_or_use_authoritative(location, format, args)
        uuid = self._db_graph.get_uuid_for_collection(
            self.key, uuid, True, 'insert_graph()'
        )
        self._db_graph.update(g, uuid, self.key)
        return uuid

    def _insert_new_graph(self, location=None, format=None, args=None):
        g = self._parse_graph_or_use_authoritative(location, format, args)
        return self._db_graph.store(g, self.key)

    def _parse_graph_or_use_authoritative(
            self,
            location=None,
            format=None,
            args=None
    ):
        if location and format:
            return self._parse_graph(location, format, args)
        else:
            if self.graph_generate_func:
                return self.graph_generate_func(args)
            else:
                raise RuntimeError('Graph generating has not been implemented '
                                   'for this subcommand, please provide either '
                                   'function for generating graph or a graph '
                                   'to load.')

    def _parse_graph(self, location, format, args):
        g = self._utils_graph.create_bound_graph()
        g.parse(location, format=format)

        if self.adjust_loaded_graph:
            self.adjust_loaded_graph(self, g, args)

        return g

    def register_subcommand(self, add_parser):
        parser = add_parser(
            self.key,
            help=f"Collection of helper commands for dealing with {self.key} "
            f"graphs.",
            description=f"Command for dealing with {self.key} graphs."
            f" {self.description}"
        )
        subcommands = parser.add_subparsers(
            title="actions",
            description=f"These actions are available to manipulate {self.key} "
            f"graphs.",
            dest="action"
        )
        self.register_crud_commands(subcommands)

    def register_crud_commands(self, subparser):
        subparsers = dict()
        if self.graph_generate_func:
            subparsers['generate'] = self._register_generate(
                subparser.add_parser
            )
        subparsers['create'] = self._register_create(subparser.add_parser)
        subparsers['remove'] = self._register_remove(subparser.add_parser)
        subparsers['list'] = self._register_list(subparser.add_parser)
        subparsers['show'] = self._register_show(subparser.add_parser)

        if self.adjust_parsers:
            self.adjust_parsers(subparsers)

    def _register_generate(self, add_parser):
        help_text = (
            f"Generate the authoritative, canonical {self.key} graph."
        )
        parser = add_parser(
            'generate',
            help=help_text,
            description=help_text,
        )
        register_arguments_for_rdf_output(parser)
        parser.set_defaults(
            func=self._do_generate
        )
        return parser

    def _do_generate(self, args):
        return with_rdf_output(self.graph_generate_func)(args)

    def _register_create(self, add_parser):
        help_text = (
            f"Create a new {self.key} graph in the database. The UUID of the "
            f"new {self.key} entry is printed."
        )
        parser = add_parser(
            'create',
            help=help_text,
            description=help_text,
        )
        if self.graph_generate_func:
            parser.add_argument(
                '--read',
                '-r',
                help=f"Location and format of the {self.key} graph to load "
                f"into the database. By default, the authoritative version "
                f"will be generated and used.",
                nargs=2,
                metavar=('LOCATION', 'FORMAT'),
            )
        else:
            parser.add_argument(
                'read',
                help=f"Location and format of the {self.key} graph to load "
                f"into the database.",
                nargs=2,
                metavar=('LOCATION', 'FORMAT'),
            )
        parser.add_argument(
            '--uuid',
            '-i',
            help=f"Force the UUID for the new {self.key} graph, potentially "
            f"overwriting an existing {self.key} graph with the same UUID. If "
            f"you do not provide a UUID, it will be read from the"
            f" {self.key.upper()}_UUID environment variable. When this flag is "
            f"not given, a new UUID is generated and printed.",
            nargs='?',
            const=None,
            default=False
        )
        parser.set_defaults(
            func=self._do_create
        )
        return parser

    def _do_create(self, args):
        if args.read:
            location, rdf_format = args.read
        else:
            location, rdf_format = None, None

        uuid = self.insert_potentially_new_graph(
            args.uuid,
            location,
            rdf_format,
            args
        )
        print(uuid)

    def _register_remove(self, add_parser):
        help_text = (
            f"Remove the {self.key} with the specified UUID(s), no questions "
            f"asked."
        )
        parser = add_parser(
            'remove',
            help=help_text,
            description=help_text,
        )
        parser.add_argument(
            'uuid',
            help=f"UUID of {self.key} document(s) to remove",
            nargs="+"
        )
        parser.set_defaults(
            func=self._do_remove
        )
        return parser

    def _do_remove(self, args):
        from bson.errors import InvalidId
        success = True
        for uuid in args.uuid:
            try:
                result = self._db_graph.remove(uuid, self.key)
                if not result:
                    success = False
                    print('No document with UUID', uuid, 'found')
            except InvalidId:
                success = False
                print('The UUID', uuid, 'is invalid')

        return 0 if success else 1

    def _register_list(self, add_parser):
        help_text = (
            f"List all {self.plural} in the database."
        )
        parser = add_parser(
            'list',
            help=help_text,
            description=help_text,
        )
        parser.set_defaults(
            func=self._do_list
        )
        return parser

    def _do_list(self, args):
        documents = self._db_graph.find_all_ids(self.key)
        for doc in documents:
            print(doc)

    def _register_show(self, add_parser):
        help_text = (
            f"Display the contents of one row of {self.key} in the database."
        )
        parser = add_parser(
            'show',
            help=help_text,
            description=help_text,
        )
        register_arguments_for_rdf_output(parser)
        parser.add_argument(
            'uuid',
            help=f'The UUID of the {self.key} graph to show. If not given, '
            f'then the UUID named in the {self.key.upper()}_UUID environment '
            f'variable is used. If no such variable is found, whatever MongoDB '
            f'returns first is shown.',
            nargs='?',
            default=None
        )
        parser.set_defaults(
            func=self._do_show
        )
        return parser

    def _do_show(self, args):
        # Work around with_rdf_output not made for methods
        get_func = getattr(self._db_graph, f'get_{self.key}')

        def call_get_func(args):
            return get_func(args.uuid, False)

        return with_rdf_output(call_get_func)(args)
