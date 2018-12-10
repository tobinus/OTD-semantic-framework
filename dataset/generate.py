# Fetch information about datasets and store it
from sys import stderr
from urllib.parse import urlparse
from utils.graph import create_bound_graph
import requests


def generate_dataset(ckan_url):
    if is_package_search_url(ckan_url):
        api_url = ckan_url
        ckan_url = get_ckan_base_from_api_url(api_url)
        packages, count = get_datasets_from_package_search(api_url)
    else:
        packages, count = get_datasets_from_package_list(ckan_url)

    if not user_confirms_action(count):
        raise RuntimeError('Dataset generation cancelled by user')

    # Using this list, download DCAT RDF for each dataset
    graph = create_bound_graph()
    for res in packages:
        dataset = f'{ckan_url}/dataset/{res}.rdf'
        data = requests.get(dataset)
        data.raise_for_status()
        graph.parse(data=data.text)

    return graph


def is_package_search_url(url):
    # Strip off any query string and so on
    parsed_url = urlparse(url)
    return parsed_url.path.endswith('/action/package_search')


def get_ckan_base_from_api_url(api_url):
    pos = api_url.find('/api/')
    # The base is everything up to /api/
    return api_url[:pos]


def get_datasets_from_package_search(api_url):
    response = requests.get(api_url)
    response.raise_for_status()

    from_json = response.json()
    result = from_json['result']
    count = result['count']
    package_detail_list = result['results']
    return map(lambda details: details['name'], package_detail_list), count


def get_datasets_from_package_list(ckan_url):
    # Strip off any trailing slash, since we add slash ourselves
    if ckan_url[-1] == '/':
        ckan_url = ckan_url[:-1]

    # Download list of packages
    package_list = requests.get(
        f'{ckan_url}/api/3/action/package_list',
    )
    package_list.raise_for_status()

    # Were we redirected to package search? (Done by catalog.data.gov)
    if is_package_search_url(package_list.url):
        return get_datasets_from_package_search(package_list.url)

    result = package_list.json()['result']
    return result, len(result)


def user_confirms_action(count):
    print(
        f'{count} datasets found. Do you want to download their metadata?',
        file=stderr
    )
    while True:
        print(
            '[Y/n]: ',
            file=stderr,
            end=''
        )
        original_response = input()
        response = original_response.lower().strip()

        if response in ('', 'y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print(f'Could not understand "{original_response}"')
