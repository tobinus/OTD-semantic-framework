import csv
import io
import sys
from tabulate import tabulate


def evaluate_using_file(file):
    return [
        {'test': 'hei', 'ohai': 'hey'},
        {'test': 'Hello', 'ohai': 'Hey there!'}
    ]


def print_results(results, table_format='psql', destination=None):
    if destination is None:
        destination = sys.stdout

    if table_format.lower() == 'csv':
        output = format_as_csv(results)
    else:
        output = format_using_tabulate(results, table_format)
    print(output, file=destination)


def format_as_csv(results):
    stream = io.StringIO(newline='')
    csv_writer = csv.DictWriter(stream, fieldnames=results[0].keys())
    csv_writer.writeheader()

    for r in results:
        csv_writer.writerow(r)
    return stream.getvalue().strip()


def format_using_tabulate(results, table_format):
    return tabulate(
        results,
        headers='keys',
        tablefmt=table_format,
    )
