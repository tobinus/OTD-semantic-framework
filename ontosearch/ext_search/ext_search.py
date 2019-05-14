import json
import db.graph
from otd.constants import GOOGLE_ENGINE


def do_ext_multi_search(engine, document, queries, configurations):
    if engine == GOOGLE_ENGINE:
        from ontosearch.ext_search.google import GoogleDatasetSearch as engine_cls
    else:
        raise ValueError('Unrecognized search engine')

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
        **engine_config,
    }
    print(json.dumps(this_search))

    results = engine_instance.search(query, **engine_config)
    if results:
        print('\n'.join(results))

