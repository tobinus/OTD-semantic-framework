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


def show_usage_when_no_action(parser):
    parser.set_defaults(
        func=lambda _: parser.error('Please specify an action')
    )


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
            graph_class_name,
            plural,
            adjust_loaded_graph=None,
            adjust_parsers=None,
            graph_generate_func=None,
            description=''
    ):
        self.graph_class_name = graph_class_name
        self.collection_name = graph_class_name.lower()
        self.plural = plural
        self.adjust_loaded_graph = adjust_loaded_graph
        self.adjust_parsers = adjust_parsers
        self.graph_generate_func = graph_generate_func
        self.description = description
        self.__graph_class = None
        self.__utils_graph = None

    @property
    def graph_class(self):
        # Avoid loading db.graph (and thereby MongoDb libs) unless needed
        if self.__graph_class is None:
            # Get the class from the db.graph module
            from db import graph
            self.__graph_class = getattr(graph, self.graph_class_name)
        return self.__graph_class

    @property
    def _utils_graph(self):
        # Avoid loading utils.graph (and thereby RDFlib) unless we need it
        if self.__utils_graph is None:
            from utils import graph
            self.__utils_graph = graph
        return self.__utils_graph

    def insert_potentially_new_graph(
            self,
            uuid=None,
            location=None,
            format=None,
            args=None
    ):
        rdf_graph = self._parse_graph_or_use_authoritative(location, format, args)

        if uuid is None:
            # The user provided the --uuid flag without specifying the ID, so
            # use the one provided in the environment variable
            uuid = self.graph_class.find_uuid()
        elif uuid is False:
            # The user did not specify to use a specific UUID, so generate a new
            uuid = None
        graph = self.graph_class(uuid, rdf_graph)
        return graph.save()

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
            self.collection_name,
            help=f"Collection of helper commands for dealing with {self.collection_name} "
            f"graphs.",
            description=f"Command for dealing with {self.collection_name} graphs."
            f" {self.description}"
        )
        show_usage_when_no_action(parser)
        subcommands = parser.add_subparsers(
            title="actions",
            description=f"These actions are available to manipulate {self.collection_name} "
            f"graphs.",
            dest="action"
        )
        self.register_crud_commands(subcommands)
        return parser, subcommands

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
            f"Generate the authoritative, canonical {self.collection_name} graph."
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
            f"Create a new {self.collection_name} graph in the database. The UUID of the "
            f"new {self.collection_name} entry is printed."
        )
        parser = add_parser(
            'create',
            help=help_text,
            description=help_text,
        )
        input_option = parser.add_mutually_exclusive_group()
        if self.graph_generate_func:
            input_option.add_argument(
                '--read',
                '-r',
                help=f"Location and format of the {self.collection_name} graph to load "
                f"into the database. By default, the authoritative version "
                f"will be generated and used.",
                nargs=2,
                metavar=('LOCATION', 'FORMAT'),
            )
            input_option.add_argument(
                '--empty',
                help="Insert an empty graph.",
                action="store_true",
            )
        else:
            input_option.add_argument(
                '--empty',
                help="Insert an empty graph.",
                action="store_true",
            )
            input_option.add_argument(
                'read',
                help=f"Location and format of the {self.collection_name} graph to load "
                f"into the database.",
                nargs=2,
                metavar=('LOCATION', 'FORMAT'),
            )
        parser.add_argument(
            '--uuid',
            '-i',
            help=f"Force the UUID for the new {self.collection_name} graph, potentially "
            f"overwriting an existing {self.collection_name} graph with the same UUID. If "
            f"you do not provide a UUID, it will be read from the"
            f" {self.collection_name.upper()}_UUID environment variable. When this flag is "
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
        elif args.empty:
            # devnull gives 0-byte long file, which is valid, empty turtle graph
            location, rdf_format = os.devnull, "turtle"
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
            f"Remove the {self.collection_name} with the specified UUID(s), no questions "
            f"asked."
        )
        parser = add_parser(
            'remove',
            help=help_text,
            description=help_text,
        )
        parser.add_argument(
            'uuid',
            help=f"UUID of {self.collection_name} document(s) to remove",
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
                result = self.graph_class.remove_by_uuid(uuid)
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
        documents = self.graph_class.find_all_ids()
        for doc in documents:
            print(doc)

    def _register_show(self, add_parser):
        help_text = (
            f"Display the contents of one row of {self.collection_name} in the database."
        )
        parser = add_parser(
            'show',
            help=help_text,
            description=help_text,
        )
        register_arguments_for_rdf_output(parser)
        parser.add_argument(
            'uuid',
            help=f'The UUID of the {self.collection_name} graph to show. If not given, '
            f'then the UUID named in the {self.collection_name.upper()}_UUID environment '
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
        def retrieve_graph(args):
            return self.graph_class.from_uuid(args.uuid).graph

        return with_rdf_output(retrieve_graph)(args)


def float_between_0_and_1(s):
    try:
        value = float(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{s} is not a float')

    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(
            f'{s} is not between 0.0 and 1.0 inclusive'
        )

    return value
