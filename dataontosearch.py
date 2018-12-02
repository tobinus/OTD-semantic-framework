"""
This is the entry point for the whole DataOntoSearch project. It gives you
access to the entirety of the project's functionality, through the command line.
"""
import argparse
import itertools
import importlib
import sys
import traceback


"""
Instead of defining all subcommands and their argparse options here, while the
relevant code is found elsewhere, the argparse options are co-located with the
relevant part of the application.

Most commonly, a file called cli.py inside the relevant package is used to
register relevant subcommands. Those packages are named in PACKAGES_WITH_CLI.
It is also possible to directly name the module which will register
subcommands by naming it in CLI_MODULES.
"""
# Packages (directories) containing a module named cli
PACKAGES_WITH_CLI = (
    'ontosearch',
    'dataset_tagger',
    'ontology',
    'dataset',
    'similarity',
    'autotag',
)
# Name of modules that should also be used to create subcommands, but which
# aren't called cli
CLI_MODULES = (
    'utils.nltk_downloads',
)


def main():
    # Create argument parser, complete with subcommand parsers
    parser = create_parser()

    # Use the argument parser on our command line arguments
    args = parser.parse_args()

    # Was a command specified?
    if not args.subcommand:
        parser.error("Please specify a subcommand. Use --help to see available "
                     "subcommands.")
    # Do we have a function to run?
    elif not hasattr(args, 'func'):
        raise RuntimeError(
            "The chosen subcommand '{}' does not define a function to be run "
            "when that subcommand is called. Please ensure 'set_defaults()' "
            "is called on the subparser, assigning 'func' the function to call."
            .format(args.subcommand)
        )
    else:
        # Yes, run the function associated with this command, and give it the
        # parsed arguments
        result = args.func(args)

        try:
            exit_code = int(result)
            parser.exit(exit_code)
        except (ValueError, TypeError):
            pass  # Normal shutdown


def create_parser():
    # Create parser, with overall information about this script
    parser = argparse.ArgumentParser(
        description="Entry point for running anything in DataOntoSearch"
    )

    # Create "argument" for subparsers
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="Use these subcommands to perform the different tasks.",
        dest='subcommand'
    )

    # Actually create subparsers, for the different modules
    load_subcommands(subparsers)

    return parser


def load_subcommands(subparsers):
    for module_name in find_modules_with_subcommands():
        # Try importing this module
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            traceback.print_exc()
            print(
                "Failed to load subcommands from module {}, ignoring module…"
                .format(module_name),
                file=sys.stderr
            )
            continue

        # Does this module expose the function we want to call?
        if not hasattr(module, 'register_subcommand'):
            print(
                "CLI module {} does not expose a 'register_subcommand' "
                "function, ignoring module…".format(module_name),
                file=sys.stderr
            )
            continue

        # It exposes something with that name, at least
        register_subcommand = module.register_subcommand

        # Is it something we can call?
        if not callable(register_subcommand):
            print(
                "Though the CLI module {} exposes something called "
                "'register_subcommand', it is not something callable. Ignoring "
                "module…".format(module_name),
                file=sys.stderr
            )
            continue

        # Ask the module to create/register its subparser
        register_subcommand(subparsers.add_parser)


def find_modules_with_subcommands():
    # Get the modules that were named precisely
    modules = CLI_MODULES

    # Obtain the modules we infer from the list of packages
    packages = PACKAGES_WITH_CLI
    package_modules = map(lambda m: m + '.cli', packages)

    # Combine those two into one generator of CLI modules
    return itertools.chain(modules, package_modules)


# With all the functions defined, call main() if this script was called directly
if __name__ == '__main__':
    main()
