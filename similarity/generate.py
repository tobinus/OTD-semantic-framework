from uuid import uuid4

from rdflib import Literal, URIRef
from rdflib.namespace import RDF, XSD

from utils.graph import create_bound_graph, QEX, OTD


# Helper method to create a link between a dataset and a concept with
# a given similarity-score
# TODO: Write full doc
# TODO: Refactor into central place (db.graph?)
def add_similarity_link(graph, dataset, concept, score=1.0, check_for_duplicates=True):
    bindings = {
        'dataset': dataset,
        'concept': concept,
    }
    namespaces = {
        'OTD': OTD,
    }

    if check_for_duplicates:
        # Try removing any similarity link that matches this dataset and concept
        # -- if they don't exist, then this still executes just fine (we are
        # just combining searching for existing triples and deleting them)
        graph.update(
            """
            DELETE WHERE {
                ?simlink a           OTD:Similarity ;
                         OTD:dataset ?dataset       ;
                         OTD:concept ?concept       ;
                         # Here we match against any other triples involving the
                         # matched ?simlink:
                         ?property   ?value         .
            }
            """,
            initNs=namespaces,
            initBindings=bindings,
        )

    uuid = uuid4().hex
    simlink = URIRef(QEX[uuid])

    score_literal = Literal(score, datatype=XSD.double)
    bindings['score'] = score_literal
    bindings['simlink'] = simlink

    graph.update(
        """
        # We use INSERT instead of INSERT DATA so variables can be used
        INSERT {
            ?simlink a           OTD:Similarity ;
                     OTD:dataset ?dataset       ;
                     OTD:concept ?concept       ;
                     OTD:score   ?score         .
        } WHERE {}
        """,
        initNs=namespaces,
        initBindings=bindings,
    )
    return simlink


def create_manual_tag_graph():
    graph = create_bound_graph()

    # Define a list of dataset-concept pairs that corresponds
    # to the document "manually tagged open transport data"
    dataset_concept_pairs = [
        ('caefad21-41cc-41e6-9f59-e050486686ea', OTD.ChargingStation),
        ('88d19fa6-3c12-4838-b58e-38d28e860245', OTD.AirQuality),
        ('d473bc01-8d6e-4771-a946-e19d3fff3691', OTD.AirQuality),
        ('1f64a769-9c10-4cc7-9db9-60ac74a7183e', OTD.Location),
        ('3e661b0d-d325-4ca4-b536-972b69615629', OTD.Location),
        ('9f6d9caa-df3a-4515-8ba3-025c076efaeb', OTD.HydrometeorologicalInformation),
        ('055880c9-cb7e-4919-ab9f-e6d6ee096346', OTD.Location),
        ('0612abbf-1b35-422c-971c-869c6f22214e', OTD.Location),
        ('0827894d-5db2-443b-b8fb-e58e60cb6962', OTD.Location),
        ('12bf3448-ec94-4188-8a1f-c89255e6217c', OTD.Location),
        ('1a7f9e36-0e6f-41e6-9608-4f184e27c5ed', OTD.Location),
        ('4298b3a3-d06e-40bc-9097-4229e993988e', OTD.Location),
        ('4fbaaeb9-b6bb-4862-b8cf-aee476725d1f', OTD.Location),
        ('64a3f8ff-5ce8-40f7-bf9d-33e335d406ce', OTD.Location),
        ('6adb0d93-6cb3-4e4b-861f-489f3b9bd9b2', OTD.Location),
        ('6e24e79e-3bda-4a65-87fb-8123f5bb1cde', OTD.Location),
        ('85cd5905-a6a0-422b-ae8c-776b9f84d205', OTD.Location),
        ('8966a9f8-c4aa-4c83-ae1c-b9de223a728d', OTD.Location),
        ('89cf5416-caf8-46d7-9d2d-7bf57ea9d1ac', OTD.Location),
        ('8f8ac030-0d03-46e2-8eb7-844ee11a6203', OTD.Location),
        ('94016332-2c3f-4c5d-9798-4582961ead79', OTD.Location),
        ('9c18dcad-313d-4bb0-bec7-358c40724cf0', OTD.Location),
        ('a68c8302-5192-4a34-9134-98500dd44f74', OTD.Location),
        ('a8669394-1dc6-4258-be23-09f671d7c513', OTD.Location),
        ('a8cb46ae-7441-4a87-b52e-5351685a33d0', OTD.Location),
        ('ad9335f3-a405-4811-86a2-e7cb34254e11', OTD.Location),
        ('b6feae31-74cd-4ada-bc44-0a372f518380', OTD.Location),
        ('c028cc71-066c-42d6-8e66-31752b2d3a48', OTD.Location),
        ('d1a3a50b-0566-48c1-acc0-15049da971b3', OTD.Location),
        ('de82c50b-52c2-4266-9765-386a32c5302d', OTD.Location),
        ('dfb9b81c-d9a2-4542-8f63-7584a3594e02', OTD.Location),
        ('eca0854c-32dd-4692-8caa-dbdbd41fd95a', OTD.Location),
        ('ee2f48ab-5b04-4c80-ad3f-0c6cfb87cc27', OTD.Location),
        ('f5b758cf-9a21-419a-a311-e6eceeb7f29c', OTD.Location),
        ('36ceda99-bbc3-4909-bc52-b05a6d634b3f', OTD.Location),
        ('36ceda99-bbc3-4909-bc52-b05a6d634b3f', OTD.Parking),
        ('52d0d63e-d26c-43b9-91e2-13b3b2a96c89', OTD.Location),
        ('52d0d63e-d26c-43b9-91e2-13b3b2a96c89', OTD.Parking),
        ('95797234-3d9b-415c-a7e2-c4660843ee20', OTD.Location),
        ('95797234-3d9b-415c-a7e2-c4660843ee20', OTD.Parking),
        ('a487ff09-435a-44bf-8c35-36c60b1eb4ad', OTD.Location),
        ('a487ff09-435a-44bf-8c35-36c60b1eb4ad', OTD.TravelInformation),
        ('23fef01e-c729-43b2-8fb3-8e127f04b286', OTD.Map),
        ('0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.Map),
        ('0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.Bicycle),
        ('0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.TransportNetwork),
        ('bf374070-430b-4d30-8818-ff5ca756a3da', OTD.MeteorologicalInformation),
        ('1510b486-ef6a-4c03-a858-b19a3a802f82', OTD.MeteorologicalInformation),
        ('4698e844-2cc0-429a-958e-0853904e8652', OTD.Statistics),
        ('e97fd128-4db5-4b0a-ab36-658c489b76eb', OTD.Statistics),
        ('f2c97ee0-6cad-4833-92fb-4a21d8b68b74', OTD.Statistics),
        ('8feb944e-b50d-4536-a61a-cbdcf52861f1', OTD.Statistics),
        ('8feb944e-b50d-4536-a61a-cbdcf52861f1', OTD.APIDescription),
        ('ab60e637-ef33-44ea-b1d4-0bb0fea81799', OTD.Statistics),
        ('ab60e637-ef33-44ea-b1d4-0bb0fea81799', OTD.EnvironmentInformation),
        ('027b3371-5d84-4ac4-8dda-bba833189db7', OTD.TrafficInformation),
        ('027b3371-5d84-4ac4-8dda-bba833189db7', OTD.Bicycle),
        ('90cef5d5-601e-4412-87e4-3e9e8dc59245', OTD.TrafficInformation),
        ('90cef5d5-601e-4412-87e4-3e9e8dc59245', OTD.Bicycle),
        ('42fb5664-7801-4787-9d93-7b0c87fad360', OTD.TrafficInformation),
        ('42fb5664-7801-4787-9d93-7b0c87fad360', OTD.Bicycle),
        ('9e449b4a-a7c9-4d47-9d5e-94128d179995', OTD.TrafficInformation),
        ('9e449b4a-a7c9-4d47-9d5e-94128d179995', OTD.Road),
        ('52546226-9fc9-4020-bd21-bd869c5ba8bd', OTD.TrafficInformation),
        ('52546226-9fc9-4020-bd21-bd869c5ba8bd', OTD.Bicycle),
        ('aad23951-b6eb-489e-8bfe-59949eed916a', OTD.TrafficInformation),
        ('aad23951-b6eb-489e-8bfe-59949eed916a', OTD.Road),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.TrafficInformation),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.Road),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.RealTime),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.MeteorologicalInformation),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.TransportNetworkCondition),
        ('8c920c9b-77ad-4f64-8253-085078634e01', OTD.Accident),
        ('fb3cd5ed-c920-4369-aa84-e4a0a802499e', OTD.TrafficInformation),
        ('fb3cd5ed-c920-4369-aa84-e4a0a802499e', OTD.Train),
        ('8f3b2912-a296-42f9-bd3c-afeea8c678ab', OTD.Law),
        ('482b30a8-1b35-4ed0-85ec-cc52381fa422', OTD.TransferNode),
        ('482b30a8-1b35-4ed0-85ec-cc52381fa422', OTD.BusStop),
        ('08c25788-f90a-452c-bde0-1511cbbeddb8', OTD.TransportNetwork),
        ('08c25788-f90a-452c-bde0-1511cbbeddb8', OTD.Trail),
        ('0a4c57ac-386e-4a9b-ad09-c3d17c6a0725', OTD.TransportNetwork),
        ('0a4c57ac-386e-4a9b-ad09-c3d17c6a0725', OTD.Trail),
        ('0cd2de3b-e76f-49d8-b8cc-4c1013f59f85', OTD.TransportNetwork),
        ('0cd2de3b-e76f-49d8-b8cc-4c1013f59f85', OTD.Trail),
        ('0e4afab3-e679-4d3d-8052-0f793158cd7f', OTD.TransportNetwork),
        ('0e4afab3-e679-4d3d-8052-0f793158cd7f', OTD.Trail),
        ('1284a379-64f8-4066-bf2c-155a76c0a80f', OTD.TransportNetwork),
        ('1284a379-64f8-4066-bf2c-155a76c0a80f', OTD.Trail),
        ('1335971d-58ad-4a95-9b60-a1221636c3e0', OTD.TransportNetwork),
        ('1335971d-58ad-4a95-9b60-a1221636c3e0', OTD.Trail),
        ('14027ce4-09de-4a1c-b2bc-61f5ab61bfd0', OTD.TransportNetwork),
        ('14027ce4-09de-4a1c-b2bc-61f5ab61bfd0', OTD.Trail),
        ('1a3f7855-45f4-473c-89af-7fda8eede930', OTD.TransportNetwork),
        ('1a3f7855-45f4-473c-89af-7fda8eede930', OTD.Trail),
        ('221b490a-b9cc-4430-9bf1-ad59c4bbe06d', OTD.TransportNetwork),
        ('221b490a-b9cc-4430-9bf1-ad59c4bbe06d', OTD.Trail),
        ('22a016c9-c87e-4c14-b955-0b8f813773d9', OTD.TransportNetwork),
        ('22a016c9-c87e-4c14-b955-0b8f813773d9', OTD.Trail),
        ('25a7128a-1daf-485a-967e-dc208d0fa757', OTD.TransportNetwork),
        ('25a7128a-1daf-485a-967e-dc208d0fa757', OTD.Trail),
        ('29078456-a2e4-4659-bd37-b2c029182703', OTD.TransportNetwork),
        ('29078456-a2e4-4659-bd37-b2c029182703', OTD.Trail),
        ('2adf0936-b181-4cd5-82f8-fff6802b2214', OTD.TransportNetwork),
        ('2adf0936-b181-4cd5-82f8-fff6802b2214', OTD.Trail),
        ('2bfa7959-e9bc-4f4c-b1fa-46babdb08f42', OTD.TransportNetwork),
        ('2bfa7959-e9bc-4f4c-b1fa-46babdb08f42', OTD.Trail),
        ('2e78cdcc-897f-42d7-bd78-a09e6e070457', OTD.TransportNetwork),
        ('2e78cdcc-897f-42d7-bd78-a09e6e070457', OTD.Trail),
        ('3433bcbe-e8cc-465f-bee4-95265a29b57b', OTD.TransportNetwork),
        ('3433bcbe-e8cc-465f-bee4-95265a29b57b', OTD.Trail),
        ('42e225d3-4bf0-45ca-b579-500c62ad1340', OTD.TransportNetwork),
        ('42e225d3-4bf0-45ca-b579-500c62ad1340', OTD.Trail),
        ('48b50420-74c4-4c0c-9b60-20f203a41a06', OTD.TransportNetwork),
        ('48b50420-74c4-4c0c-9b60-20f203a41a06', OTD.Trail),
        ('49f3ebf9-40a8-4dd8-bd98-e7a0cee9a561', OTD.TransportNetwork),
        ('49f3ebf9-40a8-4dd8-bd98-e7a0cee9a561', OTD.Trail),
        ('4a8324d4-f531-41bc-8964-2dc998c05121', OTD.TransportNetwork),
        ('4a8324d4-f531-41bc-8964-2dc998c05121', OTD.Trail),
        ('4ae81d47-ca9d-4dd8-a65c-47b5e63bf427', OTD.TransportNetwork),
        ('4ae81d47-ca9d-4dd8-a65c-47b5e63bf427', OTD.Trail),
        ('4c13d555-fdfe-48b1-bfe6-db3c96c05a69', OTD.TransportNetwork),
        ('4c13d555-fdfe-48b1-bfe6-db3c96c05a69', OTD.Trail),
        ('4cee70c8-2fdc-4d25-a8e7-3daa2d7a376d', OTD.TransportNetwork),
        ('4cee70c8-2fdc-4d25-a8e7-3daa2d7a376d', OTD.Trail),
        ('51f6952b-069d-4af8-9a43-425ec054e41d', OTD.TransportNetwork),
        ('51f6952b-069d-4af8-9a43-425ec054e41d', OTD.Trail),
        ('53a3c05b-973a-4f8d-9ec3-c2fddec576e0', OTD.TransportNetwork),
        ('53a3c05b-973a-4f8d-9ec3-c2fddec576e0', OTD.Trail),
        ('584295a1-248c-4a35-b8d5-3fa2d71de880', OTD.TransportNetwork),
        ('584295a1-248c-4a35-b8d5-3fa2d71de880', OTD.Trail),
        ('5bb5d4d6-57db-4bb8-9c0b-e1e43bb15e4b', OTD.TransportNetwork),
        ('5bb5d4d6-57db-4bb8-9c0b-e1e43bb15e4b', OTD.Trail),
        ('5e5bab6c-0659-4f95-b65e-85fb454f88a4', OTD.TransportNetwork),
        ('5e5bab6c-0659-4f95-b65e-85fb454f88a4', OTD.Trail),
        ('5e604a17-dab3-4e6a-977d-ff4964338296', OTD.TransportNetwork),
        ('5e604a17-dab3-4e6a-977d-ff4964338296', OTD.Trail),
        ('64938d2c-859b-4370-8f58-9dce554776ae', OTD.TransportNetwork),
        ('64938d2c-859b-4370-8f58-9dce554776ae', OTD.Trail),
        ('650f6dc3-7d13-4472-a83a-3571a38db621', OTD.TransportNetwork),
        ('650f6dc3-7d13-4472-a83a-3571a38db621', OTD.Trail),
        ('6532c035-257d-4808-9883-38614e80fd04', OTD.TransportNetwork),
        ('6532c035-257d-4808-9883-38614e80fd04', OTD.Trail),
        ('725a493d-2942-4585-b72f-df6d1b06bb45', OTD.TransportNetwork),
        ('725a493d-2942-4585-b72f-df6d1b06bb45', OTD.Trail),
        ('92a9b284-6073-47e9-8eee-5f2195d0879a', OTD.TransportNetwork),
        ('92a9b284-6073-47e9-8eee-5f2195d0879a', OTD.Trail),
        ('96c508b9-607d-4ace-a0ba-cf5082ad6441', OTD.TransportNetwork),
        ('96c508b9-607d-4ace-a0ba-cf5082ad6441', OTD.Trail),
        ('99043ac8-9e0d-4cd6-bb1d-7e45adc22556', OTD.TransportNetwork),
        ('99043ac8-9e0d-4cd6-bb1d-7e45adc22556', OTD.Trail),
        ('9bc820a1-aea6-4619-a5dd-d375f30c90e3', OTD.TransportNetwork),
        ('9bc820a1-aea6-4619-a5dd-d375f30c90e3', OTD.Trail),
        ('a07a14eb-5b51-4484-ab0e-b8ec2bfdb2fa', OTD.TransportNetwork),
        ('a07a14eb-5b51-4484-ab0e-b8ec2bfdb2fa', OTD.Trail),
        ('a441154d-1c7b-44e9-9d37-2d06b6af6411', OTD.TransportNetwork),
        ('a441154d-1c7b-44e9-9d37-2d06b6af6411', OTD.Trail),
        ('a5b546fc-b9b1-4766-bd72-866e0edb874d', OTD.TransportNetwork),
        ('a5b546fc-b9b1-4766-bd72-866e0edb874d', OTD.Trail),
        ('a7e7242e-006f-445a-aee3-928ac6dbead4', OTD.TransportNetwork),
        ('a7e7242e-006f-445a-aee3-928ac6dbead4', OTD.Trail),
        ('a85bd417-117e-4a63-bf95-65f3ba0852a3', OTD.TransportNetwork),
        ('a85bd417-117e-4a63-bf95-65f3ba0852a3', OTD.Trail),
        ('b143d042-cd64-4b0c-9614-17ea71b454a4', OTD.TransportNetwork),
        ('b143d042-cd64-4b0c-9614-17ea71b454a4', OTD.Trail),
        ('b58d8633-0a0c-438c-b283-c4b0ae13cd77', OTD.TransportNetwork),
        ('b58d8633-0a0c-438c-b283-c4b0ae13cd77', OTD.Trail),
        ('bbd70a3e-8fe0-47e5-9624-880beeb19c59', OTD.TransportNetwork),
        ('bbd70a3e-8fe0-47e5-9624-880beeb19c59', OTD.Trail),
        ('bf627d4a-f115-41a2-82b9-d19de3cd5414', OTD.TransportNetwork),
        ('bf627d4a-f115-41a2-82b9-d19de3cd5414', OTD.Trail),
        ('c1392a5e-675e-4e1a-9e79-ed4e0c17328a', OTD.TransportNetwork),
        ('c1392a5e-675e-4e1a-9e79-ed4e0c17328a', OTD.Trail),
        ('c8ac90a3-6525-4653-88af-d897aab86704', OTD.TransportNetwork),
        ('c8ac90a3-6525-4653-88af-d897aab86704', OTD.Trail),
        ('d0b9c7e6-29e2-411c-9036-6f7d7e7a2c02', OTD.TransportNetwork),
        ('d0b9c7e6-29e2-411c-9036-6f7d7e7a2c02', OTD.Trail),
        ('d0ed874c-14ca-4166-a87d-23844fbf114c', OTD.TransportNetwork),
        ('d0ed874c-14ca-4166-a87d-23844fbf114c', OTD.Trail),
        ('d105d776-596e-4801-976a-c2b465b04f87', OTD.TransportNetwork),
        ('d105d776-596e-4801-976a-c2b465b04f87', OTD.Trail),
        ('d93c1ea6-4c2d-4df4-acf4-1c57b15e5790', OTD.TransportNetwork),
        ('d93c1ea6-4c2d-4df4-acf4-1c57b15e5790', OTD.Trail),
        ('ecb58c29-3169-4eef-8873-1483d1c5e88c', OTD.TransportNetwork),
        ('ecb58c29-3169-4eef-8873-1483d1c5e88c', OTD.Trail),
        ('f6475ec0-099f-4cc8-84f7-4f6b3aaae393', OTD.TransportNetwork),
        ('f6475ec0-099f-4cc8-84f7-4f6b3aaae393', OTD.Trail),
        ('3863c79d-1102-45dc-aecb-6d0c0d0a1696', OTD.TransportService),
        ('3863c79d-1102-45dc-aecb-6d0c0d0a1696', OTD.AirQuality),
        ('1b85ba90-b675-4831-87fd-4d0de893df18', OTD.TransportNetworkCondition),
        ('1b85ba90-b675-4831-87fd-4d0de893df18', OTD.RoutePlan),
        ('78a0cc73-b4de-4c87-84b0-c5bb7ba079c2', OTD.TravelInformation),
        ('e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TravelInformation),
        ('e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.RealTime),
        ('e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.Timetable),
        ('e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TravelPlan),
        ('e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TransferNode),
        ('265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.TravelInformation),
        ('265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.RealTime),
        ('265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.Timetable),
        ('265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.TransportService),
        ('0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.TravelInformation),
        ('0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.Timetable),
        ('0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.TransportService),
        ('3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.TravelInformation),
        ('3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.Timetable),
        ('3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.TransportService),
        ('a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.TravelInformation),
        ('a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.Bicycle),
        ('a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.TravelPlan),
        ('16d3afdb-bb20-4593-929a-9fbd3f52ef05', OTD.Location)
    ]

    # Generate similarities
    for uuid, concept in dataset_concept_pairs:
        add_similarity_link(
            graph,
            URIRef('http://78.91.98.234/dataset/{}'.format(uuid)),
            concept,
            check_for_duplicates=False
        )

    return graph
