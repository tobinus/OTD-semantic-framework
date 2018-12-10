# Fetch information about datasets and store it
from sys import stderr
from urllib.parse import urlparse
from utils.graph import create_bound_graph
from utils import paginated_api
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


def get_datasets_from_package_search(api_url, page_size=100):
    def get_results(response):
        from_json = response.json()
        return from_json.get('result', dict()).get('results', tuple())

    def get_count(response):
        from_json = response.json()
        return from_json['result']['count']

    results, count = paginated_api.fetch(
        requests.session(),
        api_url,
        page_size,
        'start',
        'rows',
        get_results,
        get_count
    )
    return map(lambda details: details['name'], results), count


def get_datasets_from_package_list(ckan_url):
    # Strip off any trailing slash, since we add slash ourselves
    if ckan_url[-1] == '/':
        ckan_url = ckan_url[:-1]

    def get_results(response):
        return response.json().get('result', tuple())

    def get_count(_):
        unrelated_generator, count = get_datasets_from_package_search(
            f'{ckan_url}/api/3/action/package_search',
            1
        )
        return count

    def check_has_stayed(response):
        # Were we redirected to package search? (Done by catalog.data.gov)
        if is_package_search_url(response.url):
            return get_datasets_from_package_search(response.url)
        else:
            return True

    return paginated_api.fetch(
        requests.session(),
        f'{ckan_url}/api/3/action/package_list',
        200,
        'offset',
        'limit',
        get_results,
        get_count,
        check_has_stayed
    )


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
