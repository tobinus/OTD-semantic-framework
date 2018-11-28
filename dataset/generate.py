# Fetch information about datasets and store it
from utils.graph import create_bound_graph
import requests


def generate_dataset(ckan_instance):
    # Strip off any trailing slash, since we add slash ourselves
    if ckan_instance[-1] == '/':
        ckan_instance = ckan_instance[:-1]

    # Download list of packages
    package_list = requests.get(f'{ckan_instance}/api/3/action/package_list')
    package_list.raise_for_status()

    # Using this list, download DCAT RDF for each dataset
    graph = create_bound_graph()
    for res in package_list.json()['result']:
        dataset = f'{ckan_instance}/dataset/{res}.rdf'
        data = requests.get(dataset)
        data.raise_for_status()
        graph.parse(data=data.text)

    return graph
