from db.graph import Configuration, Similarity, Autotag


def create(args):
    config = Configuration()

    if args.uuid is False:
        config.uuid = None
    else:
        config.uuid = Configuration.find_uuid(args.uuid)

    config.label = args.label
    config.similarity_uuid = Similarity.force_find_uuid(args.similarity)
    config.autotag_uuid = Autotag.force_find_uuid(args.autotag)

    if args.preview:
        config.prepare()
        print_config(config)

        if config.uuid is None:
            print('A new UUID would be generated for the new configuration')
        else:
            print('CONFIGURATION_UUID=' + config.uuid)
    else:
        config.save()
        print(config.uuid)


def remove(args):
    from bson.errors import InvalidId
    success = True
    for uuid in args.uuid:
        try:
            result = Configuration.remove_by_uuid(uuid)
            if not result:
                success = False
                print('No document with UUID', uuid, 'found')
        except InvalidId:
            success = False
            print('The UUID', uuid, 'is invalid')

    return 0 if success else 1


def list_all():
    documents = Configuration.find_all_ids()
    for doc in documents:
        config = Configuration.from_uuid(doc)
        print(doc, config.label)


def show(args):
    config = Configuration.from_uuid(args.uuid)
    print_config(config)


def print_config(config):
    print('#', config.label)
    print('ONTOLOGY_UUID=' + config.ontology_uuid)
    print('DATASET_UUID=' + config.dataset_uuid)
    print('SIMILARITY_UUID=' + config.similarity_uuid)
    print('AUTOTAG_UUID=' + config.autotag_uuid)
