def register_subcommand(add_parser):
    help_text = (
        'Download the NLTK data needed for running DataOntoSearch. The data '
        'weights about 26MiB. The action is idempotent.'
    )
    parser = add_parser(
        'nltk_data',
        help=help_text,
        description=help_text,
    )
    parser.set_defaults(
        func=download_nltk_data
    )


def download_nltk_data(args):
    import nltk
    downloads = (
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet',
    )
    results = [nltk.download(data_id) for data_id in downloads]
    return all(results)
