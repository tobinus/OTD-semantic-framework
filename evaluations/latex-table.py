import csv
import sys

first_row_macro = r'\firstrow'
row_macro = r'\resultrow'

with open(sys.argv[1], newline='') as f:
    reader = csv.reader(f)

    for index, row in enumerate(reader):
        first_column, rest = row[0], row[1:]
        if first_column not in ('query', 'Total Result'):
            first_column = str(index)
        rest = map(lambda s: str(s).rstrip('%'), rest)

        row = [first_column] + list(rest)

        this_macro = first_row_macro if index == 0 else row_macro
        print('    ' + this_macro + '{' + '}{'.join(row) + '}')
