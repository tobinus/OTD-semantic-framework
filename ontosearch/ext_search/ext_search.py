import json
from yaml import load
from ontosearch.search import get_queries_from_doc, get_configurations_from_doc
import db.graph


def do_ext_multi_search(engine, file):
    if engine == 'google':
        from ontosearch.ext_search.google import GoogleDatasetSearchExtractor as engine_cls
    else:
        raise ValueError('Unrecognized search engine')

    try:
        document = load(file)

        queries = get_queries_from_doc(document)
        configurations = get_configurations_from_doc(document)

        engine_config = document.get(engine, {})

        is_first_result = True

        for configuration in configurations:
            c = db.graph.Configuration.from_uuid(configuration)
            d = c.get_dataset()
            engine_instance = engine_cls(d)

            for query in queries:
                if not is_first_result:
                    print()
                else:
                    is_first_result = False

                do_single_ext_multi_search(
                    engine,
                    engine_instance,
                    engine_config,
                    configuration,
                    query,
                )

    finally:
        file.close()


def do_single_ext_multi_search(
        engine,
        engine_instance,
        engine_config,
        configuration,
        query
):
    this_search = {
        'configuration': configuration,
        'query': query,
        'engine': engine,
        'engine-config': engine_config,
    }
    print(json.dumps(this_search))

    results = engine_instance.search(query, **engine_config)
    print('\n'.join(results))

