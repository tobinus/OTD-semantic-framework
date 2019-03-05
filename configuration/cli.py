from utils.common_cli import show_usage_when_no_action


def register_subcommand(add_parser):
    parser = add_parser(
        'configuration',
        help='Collection of helper commands for managing configurations (saved '
             'combinations of all four graphs).',
        description='Command for managing configurations.'
    )
    show_usage_when_no_action(parser)
    subparser = parser.add_subparsers(
        title='actions',
        description='These actions are available to manipulate configurations.',
        dest='action',
    )

    register_create(subparser.add_parser)
    register_remove(subparser.add_parser)
    register_list(subparser.add_parser)
    register_show(subparser.add_parser)


def register_create(add_parser):
    help_text = (
        'Create a new configuration, which specifies one ontology, dataset, '
        'similarity and autotag graph to use as a combination.'
    )
    parser = add_parser(
        'create',
        help=help_text,
        description='Create a new configuration',
    )
    parser.add_argument(
        '--similarity',
        '-s',
        help='UUID of the similarity graph to use. By default, the '
             'SIMILARITY_UUID environment variable is used, or the first '
             'similarity graph returned by MongoDB.'
    )
    parser.add_argument(
        '--autotag',
        '-a',
        help='UUID of the autotag graph to use. By default, the AUTOTAG_UUID '
             'environment variable is used, or the first autotag graph '
             'returned by MongoDB.'
    )
    parser.add_argument(
        '--uuid',
        '-i',
        help='Force the UUID for the new configuration, potentially overwriting'
             ' an existing configuration with the same UUID. If you do not '
             'provide a UUID, it will be read from the CONFIGURATION_UUID '
             'environment variable. When this flag is not given, a new UUID is '
             'generated and printed.',
        nargs='?',
        const=None,
        default=False
    )
    parser.add_argument(
        '--preview',
        '-p',
        action='store_true',
        help='Preview what the new configuration would look like, then exit '
             'without adding it to the database.',
    )

    parser.set_defaults(
        func=do_create
    )


def do_create(args):
    from configuration.actions import create
    create(args)


def register_remove(add_parser):
    help_text = (
        'Remove the configuration with the specified UUID(s), no questions '
        'asked.'
    )
    parser = add_parser(
        'remove',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        'uuid',
        help='UUID of configuration(s) to remove',
        nargs='+'
    )
    parser.set_defaults(
        func=do_remove
    )


def do_remove(args):
    from configuration.actions import remove
    return remove(args)


def register_list(add_parser):
    help_text = 'List all configurations in the database.'
    parser = add_parser(
        'list',
        help=help_text,
        description=help_text,
    )
    parser.set_defaults(
        func=do_list
    )
    return parser


def do_list(_):
    from configuration.actions import list_all
    list_all()


def register_show(add_parser):
    help_text = (
        'Display the contents of a configuration in the database.'
    )
    parser = add_parser(
        'show',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        'uuid',
        help='The UUID of the configuration to show. If not given, then the '
             'UUID named in the CONFIGURATION_UUID environment variable is '
             'used. If no such variable is found, whatever MongoDB returns '
             'first is shown.',
        nargs='?',
        default=None
    )
    parser.set_defaults(
        func=do_show
    )


def do_show(args):
    from configuration.actions import show
    show(args)
