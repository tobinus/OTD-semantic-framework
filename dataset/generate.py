# Fetch information about datasets and store it
from urllib.parse import urlparse
from utils.graph import create_bound_graph
import requests


def generate_dataset(ckan_url):
    # Is this an API URL?
    parsed_url = urlparse(ckan_url)
    is_api_url = parsed_url.path.endswith('/action/package_search')

    if is_api_url:
        packages = get_datasets_from_package_search(full_url=ckan_url)
    else:
        packages = get_datasets_from_package_list(ckan_url)

    # Using this list, download DCAT RDF for each dataset
    graph = create_bound_graph()
    for res in packages:
        dataset = f'{ckan_url}/dataset/{res}.rdf'
        data = requests.get(dataset)
        data.raise_for_status()
        graph.parse(data=data.text)

    return graph


def get_datasets_from_package_list(ckan_url):
    # Strip off any trailing slash, since we add slash ourselves
    if ckan_url[-1] == '/':
        ckan_url = ckan_url[:-1]

    # Download list of packages
    package_list = requests.get(
        f'{ckan_url}/api/3/action/package_list',

    )
    # TODO: Handle data.gov redirecting to package_search
    package_list.raise_for_status()
    return package_list.json()['result']


