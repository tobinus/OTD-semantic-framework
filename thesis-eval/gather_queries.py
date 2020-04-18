# Print queries on a line, ready for putting into run_old.sh
import yaml
import sys


filename = sys.argv[1]
with open(filename) as fp:
    document = yaml.load(fp)

queries = '" "'.join(document['query'].keys())
print(f'"{queries}"')
