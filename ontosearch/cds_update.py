from otd.opendatasemanticframework import ODSFLoader


def ensure_matrices_are_created():
    odsf_loader = ODSFLoader(True)
    odsf_loader.ensure_all_loaded()

