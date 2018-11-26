# Automatic search-through
import numpy as np
from db.graph import get_ontology, get_dataset, get_similarity, get_autotag
from utils.graph import ODT as OTD  # Open Transport Data makes more sense..?
from odt.opendatasemanticframework import OpenDataSemanticFramework
from rdflib import URIRef
from rdflib import Namespace
from results.confusion import confusion_matrix_scores, precision, recall, true_negative_rate, accuracy, f1_score
from dotenv import load_dotenv, find_dotenv
from os import environ


class SetMap():
    def __init__(self):
        self.config = {}
        self.config['ONTOLOGY_UUID']   = '5b2ab51401d5412566cf4e94'
        self.config['DATASETS_UUID']   = '5b2968c501d5412566cf4e86'
        self.config['SIMILARITY_UUID'] = '5b2ada4d01d5412566cf4ea1'
        self.config['AUTOTAG_UUID']    = '5b2acdfe01d5412566cf4e99'

        print ("Indexing...")
        self.ontology_graph = get_ontology(self.config['ONTOLOGY_UUID'])
        self.datasets_graph = get_dataset(self.config['DATASETS_UUID'])

        CcsId    = "5b2adb9e01d5414513ea9802"
        AutoID   = "5b2adb9c01d5414513ea9800"
        ManualID = "5b2adb3401d5414513ea97fe"
        
        self.ontology = OpenDataSemanticFramework(self.ontology_graph, self.datasets_graph, compute_ccs=False)
        self.ontology.load_ccs(CcsId)
        self.ontology.load_similarity_graph("tagged", ManualID)
        self.ontology.load_similarity_graph("auto", AutoID)
        self.set_map = {}
        self.all_datasets = set()
        print ("Ready")

    def build_set_map(self, uri, group, threshold=0.7):
        self.all_datasets.add(uri)        
        related = self.ontology.related_datasets(group, threshold)
        for r in related:        
            if not r in self.set_map:
                self.set_map[r] = set()
            self.set_map[r].add(uri)
        
    def build_map(self, threshold=0.7):
        self.set_map = {}
        self.all_datasets = set()

        self.build_set_map('http://78.91.98.234/dataset/caefad21-41cc-41e6-9f59-e050486686ea', OTD.ChargingStation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/88d19fa6-3c12-4838-b58e-38d28e860245', OTD.AirQuality, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d473bc01-8d6e-4771-a946-e19d3fff3691', OTD.AirQuality, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1f64a769-9c10-4cc7-9db9-60ac74a7183e', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3e661b0d-d325-4ca4-b536-972b69615629', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9f6d9caa-df3a-4515-8ba3-025c076efaeb', OTD.HydrometeorologicalInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/055880c9-cb7e-4919-ab9f-e6d6ee096346', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0612abbf-1b35-422c-971c-869c6f22214e', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0827894d-5db2-443b-b8fb-e58e60cb6962', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/12bf3448-ec94-4188-8a1f-c89255e6217c', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1a7f9e36-0e6f-41e6-9608-4f184e27c5ed', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4298b3a3-d06e-40bc-9097-4229e993988e', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4fbaaeb9-b6bb-4862-b8cf-aee476725d1f', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/64a3f8ff-5ce8-40f7-bf9d-33e335d406ce', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/6adb0d93-6cb3-4e4b-861f-489f3b9bd9b2', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/6e24e79e-3bda-4a65-87fb-8123f5bb1cde', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/85cd5905-a6a0-422b-ae8c-776b9f84d205', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8966a9f8-c4aa-4c83-ae1c-b9de223a728d', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/89cf5416-caf8-46d7-9d2d-7bf57ea9d1ac', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8f8ac030-0d03-46e2-8eb7-844ee11a6203', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/94016332-2c3f-4c5d-9798-4582961ead79', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9c18dcad-313d-4bb0-bec7-358c40724cf0', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a68c8302-5192-4a34-9134-98500dd44f74', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a8669394-1dc6-4258-be23-09f671d7c513', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a8cb46ae-7441-4a87-b52e-5351685a33d0', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ad9335f3-a405-4811-86a2-e7cb34254e11', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/b6feae31-74cd-4ada-bc44-0a372f518380', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/c028cc71-066c-42d6-8e66-31752b2d3a48', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d1a3a50b-0566-48c1-acc0-15049da971b3', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/de82c50b-52c2-4266-9765-386a32c5302d', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/dfb9b81c-d9a2-4542-8f63-7584a3594e02', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/eca0854c-32dd-4692-8caa-dbdbd41fd95a', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ee2f48ab-5b04-4c80-ad3f-0c6cfb87cc27', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/f5b758cf-9a21-419a-a311-e6eceeb7f29c', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/36ceda99-bbc3-4909-bc52-b05a6d634b3f', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/36ceda99-bbc3-4909-bc52-b05a6d634b3f', OTD.Parking, threshold)
        self.build_set_map('http://78.91.98.234/dataset/52d0d63e-d26c-43b9-91e2-13b3b2a96c89', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/52d0d63e-d26c-43b9-91e2-13b3b2a96c89', OTD.Parking, threshold)
        self.build_set_map('http://78.91.98.234/dataset/95797234-3d9b-415c-a7e2-c4660843ee20', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/95797234-3d9b-415c-a7e2-c4660843ee20', OTD.Parking, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a487ff09-435a-44bf-8c35-36c60b1eb4ad', OTD.Location, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a487ff09-435a-44bf-8c35-36c60b1eb4ad', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/23fef01e-c729-43b2-8fb3-8e127f04b286', OTD.Map, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.Map, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0f0e037e-b5e8-453f-97ca-8ae9be7e523c', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/bf374070-430b-4d30-8818-ff5ca756a3da', OTD.MeteorologicalInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1510b486-ef6a-4c03-a858-b19a3a802f82', OTD.MeteorologicalInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4698e844-2cc0-429a-958e-0853904e8652', OTD.Statistics, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e97fd128-4db5-4b0a-ab36-658c489b76eb', OTD.Statistics, threshold)
        self.build_set_map('http://78.91.98.234/dataset/f2c97ee0-6cad-4833-92fb-4a21d8b68b74', OTD.Statistics, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8feb944e-b50d-4536-a61a-cbdcf52861f1', OTD.Statistics, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8feb944e-b50d-4536-a61a-cbdcf52861f1', OTD.APIDescription, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ab60e637-ef33-44ea-b1d4-0bb0fea81799', OTD.Statistics, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ab60e637-ef33-44ea-b1d4-0bb0fea81799', OTD.EnvironmentInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/027b3371-5d84-4ac4-8dda-bba833189db7', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/027b3371-5d84-4ac4-8dda-bba833189db7', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/90cef5d5-601e-4412-87e4-3e9e8dc59245', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/90cef5d5-601e-4412-87e4-3e9e8dc59245', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/42fb5664-7801-4787-9d93-7b0c87fad360', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/42fb5664-7801-4787-9d93-7b0c87fad360', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9e449b4a-a7c9-4d47-9d5e-94128d179995', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9e449b4a-a7c9-4d47-9d5e-94128d179995', OTD.Road, threshold)
        self.build_set_map('http://78.91.98.234/dataset/52546226-9fc9-4020-bd21-bd869c5ba8bd', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/52546226-9fc9-4020-bd21-bd869c5ba8bd', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/aad23951-b6eb-489e-8bfe-59949eed916a', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/aad23951-b6eb-489e-8bfe-59949eed916a', OTD.Road, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.Road, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.RealTime, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.MeteorologicalInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.TransportNetworkCondition, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8c920c9b-77ad-4f64-8253-085078634e01', OTD.Accident, threshold)
        self.build_set_map('http://78.91.98.234/dataset/fb3cd5ed-c920-4369-aa84-e4a0a802499e', OTD.TrafficInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/fb3cd5ed-c920-4369-aa84-e4a0a802499e', OTD.Train, threshold)
        self.build_set_map('http://78.91.98.234/dataset/8f3b2912-a296-42f9-bd3c-afeea8c678ab', OTD.Law, threshold)
        self.build_set_map('http://78.91.98.234/dataset/482b30a8-1b35-4ed0-85ec-cc52381fa422', OTD.TransferNode, threshold)
        self.build_set_map('http://78.91.98.234/dataset/482b30a8-1b35-4ed0-85ec-cc52381fa422', OTD.BusStop, threshold)
        self.build_set_map('http://78.91.98.234/dataset/08c25788-f90a-452c-bde0-1511cbbeddb8', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/08c25788-f90a-452c-bde0-1511cbbeddb8', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0a4c57ac-386e-4a9b-ad09-c3d17c6a0725', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0a4c57ac-386e-4a9b-ad09-c3d17c6a0725', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0cd2de3b-e76f-49d8-b8cc-4c1013f59f85', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0cd2de3b-e76f-49d8-b8cc-4c1013f59f85', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0e4afab3-e679-4d3d-8052-0f793158cd7f', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0e4afab3-e679-4d3d-8052-0f793158cd7f', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1284a379-64f8-4066-bf2c-155a76c0a80f', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1284a379-64f8-4066-bf2c-155a76c0a80f', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1335971d-58ad-4a95-9b60-a1221636c3e0', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1335971d-58ad-4a95-9b60-a1221636c3e0', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/14027ce4-09de-4a1c-b2bc-61f5ab61bfd0', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/14027ce4-09de-4a1c-b2bc-61f5ab61bfd0', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1a3f7855-45f4-473c-89af-7fda8eede930', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1a3f7855-45f4-473c-89af-7fda8eede930', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/221b490a-b9cc-4430-9bf1-ad59c4bbe06d', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/221b490a-b9cc-4430-9bf1-ad59c4bbe06d', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/22a016c9-c87e-4c14-b955-0b8f813773d9', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/22a016c9-c87e-4c14-b955-0b8f813773d9', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/25a7128a-1daf-485a-967e-dc208d0fa757', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/25a7128a-1daf-485a-967e-dc208d0fa757', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/29078456-a2e4-4659-bd37-b2c029182703', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/29078456-a2e4-4659-bd37-b2c029182703', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2adf0936-b181-4cd5-82f8-fff6802b2214', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2adf0936-b181-4cd5-82f8-fff6802b2214', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2bfa7959-e9bc-4f4c-b1fa-46babdb08f42', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2bfa7959-e9bc-4f4c-b1fa-46babdb08f42', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2e78cdcc-897f-42d7-bd78-a09e6e070457', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/2e78cdcc-897f-42d7-bd78-a09e6e070457', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3433bcbe-e8cc-465f-bee4-95265a29b57b', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3433bcbe-e8cc-465f-bee4-95265a29b57b', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/42e225d3-4bf0-45ca-b579-500c62ad1340', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/42e225d3-4bf0-45ca-b579-500c62ad1340', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/48b50420-74c4-4c0c-9b60-20f203a41a06', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/48b50420-74c4-4c0c-9b60-20f203a41a06', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/49f3ebf9-40a8-4dd8-bd98-e7a0cee9a561', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/49f3ebf9-40a8-4dd8-bd98-e7a0cee9a561', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4a8324d4-f531-41bc-8964-2dc998c05121', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4a8324d4-f531-41bc-8964-2dc998c05121', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4ae81d47-ca9d-4dd8-a65c-47b5e63bf427', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4ae81d47-ca9d-4dd8-a65c-47b5e63bf427', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4c13d555-fdfe-48b1-bfe6-db3c96c05a69', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4c13d555-fdfe-48b1-bfe6-db3c96c05a69', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4cee70c8-2fdc-4d25-a8e7-3daa2d7a376d', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/4cee70c8-2fdc-4d25-a8e7-3daa2d7a376d', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/51f6952b-069d-4af8-9a43-425ec054e41d', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/51f6952b-069d-4af8-9a43-425ec054e41d', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/53a3c05b-973a-4f8d-9ec3-c2fddec576e0', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/53a3c05b-973a-4f8d-9ec3-c2fddec576e0', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/584295a1-248c-4a35-b8d5-3fa2d71de880', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/584295a1-248c-4a35-b8d5-3fa2d71de880', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5bb5d4d6-57db-4bb8-9c0b-e1e43bb15e4b', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5bb5d4d6-57db-4bb8-9c0b-e1e43bb15e4b', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5e5bab6c-0659-4f95-b65e-85fb454f88a4', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5e5bab6c-0659-4f95-b65e-85fb454f88a4', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5e604a17-dab3-4e6a-977d-ff4964338296', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/5e604a17-dab3-4e6a-977d-ff4964338296', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/64938d2c-859b-4370-8f58-9dce554776ae', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/64938d2c-859b-4370-8f58-9dce554776ae', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/650f6dc3-7d13-4472-a83a-3571a38db621', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/650f6dc3-7d13-4472-a83a-3571a38db621', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/6532c035-257d-4808-9883-38614e80fd04', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/6532c035-257d-4808-9883-38614e80fd04', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/725a493d-2942-4585-b72f-df6d1b06bb45', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/725a493d-2942-4585-b72f-df6d1b06bb45', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/92a9b284-6073-47e9-8eee-5f2195d0879a', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/92a9b284-6073-47e9-8eee-5f2195d0879a', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/96c508b9-607d-4ace-a0ba-cf5082ad6441', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/96c508b9-607d-4ace-a0ba-cf5082ad6441', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/99043ac8-9e0d-4cd6-bb1d-7e45adc22556', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/99043ac8-9e0d-4cd6-bb1d-7e45adc22556', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9bc820a1-aea6-4619-a5dd-d375f30c90e3', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/9bc820a1-aea6-4619-a5dd-d375f30c90e3', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a07a14eb-5b51-4484-ab0e-b8ec2bfdb2fa', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a07a14eb-5b51-4484-ab0e-b8ec2bfdb2fa', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a441154d-1c7b-44e9-9d37-2d06b6af6411', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a441154d-1c7b-44e9-9d37-2d06b6af6411', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a5b546fc-b9b1-4766-bd72-866e0edb874d', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a5b546fc-b9b1-4766-bd72-866e0edb874d', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a7e7242e-006f-445a-aee3-928ac6dbead4', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a7e7242e-006f-445a-aee3-928ac6dbead4', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a85bd417-117e-4a63-bf95-65f3ba0852a3', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a85bd417-117e-4a63-bf95-65f3ba0852a3', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/b143d042-cd64-4b0c-9614-17ea71b454a4', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/b143d042-cd64-4b0c-9614-17ea71b454a4', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/b58d8633-0a0c-438c-b283-c4b0ae13cd77', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/b58d8633-0a0c-438c-b283-c4b0ae13cd77', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/bbd70a3e-8fe0-47e5-9624-880beeb19c59', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/bbd70a3e-8fe0-47e5-9624-880beeb19c59', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/bf627d4a-f115-41a2-82b9-d19de3cd5414', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/bf627d4a-f115-41a2-82b9-d19de3cd5414', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/c1392a5e-675e-4e1a-9e79-ed4e0c17328a', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/c1392a5e-675e-4e1a-9e79-ed4e0c17328a', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/c8ac90a3-6525-4653-88af-d897aab86704', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/c8ac90a3-6525-4653-88af-d897aab86704', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d0b9c7e6-29e2-411c-9036-6f7d7e7a2c02', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d0b9c7e6-29e2-411c-9036-6f7d7e7a2c02', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d0ed874c-14ca-4166-a87d-23844fbf114c', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d0ed874c-14ca-4166-a87d-23844fbf114c', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d105d776-596e-4801-976a-c2b465b04f87', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d105d776-596e-4801-976a-c2b465b04f87', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d93c1ea6-4c2d-4df4-acf4-1c57b15e5790', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/d93c1ea6-4c2d-4df4-acf4-1c57b15e5790', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ecb58c29-3169-4eef-8873-1483d1c5e88c', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/ecb58c29-3169-4eef-8873-1483d1c5e88c', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/f6475ec0-099f-4cc8-84f7-4f6b3aaae393', OTD.TransportNetwork, threshold)
        self.build_set_map('http://78.91.98.234/dataset/f6475ec0-099f-4cc8-84f7-4f6b3aaae393', OTD.Trail, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3863c79d-1102-45dc-aecb-6d0c0d0a1696', OTD.TransportService, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3863c79d-1102-45dc-aecb-6d0c0d0a1696', OTD.AirQuality, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1b85ba90-b675-4831-87fd-4d0de893df18', OTD.TransportNetworkCondition, threshold)
        self.build_set_map('http://78.91.98.234/dataset/1b85ba90-b675-4831-87fd-4d0de893df18', OTD.RoutePlan, threshold)
        self.build_set_map('http://78.91.98.234/dataset/78a0cc73-b4de-4c87-84b0-c5bb7ba079c2', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.RealTime, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.Timetable, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TravelPlan, threshold)
        self.build_set_map('http://78.91.98.234/dataset/e871da91-84ca-4703-ae14-2c79eed8aa5a', OTD.TransferNode, threshold)
        self.build_set_map('http://78.91.98.234/dataset/265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.RealTime, threshold)
        self.build_set_map('http://78.91.98.234/dataset/265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.Timetable, threshold)
        self.build_set_map('http://78.91.98.234/dataset/265a373b-0f79-49d8-aba9-65526bc74ce1', OTD.TransportService, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.Timetable, threshold)
        self.build_set_map('http://78.91.98.234/dataset/0e3f86cf-2334-41f3-8762-935e5f83d638', OTD.TransportService, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.Timetable, threshold)
        self.build_set_map('http://78.91.98.234/dataset/3da97ae7-ae64-4d63-bc07-b7cf78d14b1f', OTD.TransportService, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.TravelInformation, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.Bicycle, threshold)
        self.build_set_map('http://78.91.98.234/dataset/a7276da5-6d23-4d60-930c-3ad692ca59b1', OTD.TravelPlan, threshold)
        self.build_set_map('http://78.91.98.234/dataset/16d3afdb-bb20-4593-929a-9fbd3f52ef05', OTD.Location, threshold)

    def gen_analysis(self, query, expected_tag, threshold, *e, **opts):
        search_res = set()
        for tag_type in e:
            res = self.ontology.search_query(query, tag_type, threshold)
            for r in res:
                search_res.add(r[1][2])
        cms = confusion_matrix_scores(search_res, self.set_map[expected_tag], self.all_datasets)
        # total.append([precision(cms), recall(cms), accuracy(cms), f1_score(cms)])
        return [precision(cms),recall(cms),accuracy(cms),f1_score(cms)]
        
    
