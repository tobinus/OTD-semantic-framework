def register_subcommand(add_parser):
    help_text = (
        'Download the punkt data, used for word tokenizing and required for '
        'autotagging. The data weights about 13MB. The action is idempotent.'
    )
    parser = add_parser(
        'punkt',
        help=help_text,
        description=help_text,
    )
    parser.set_defaults(
        func=download_punkt
    )


def download_punkt(args):
    import nltk
    return nltk.download('punkt', raise_on_error=True)
