_name_map_ = {"self_returner": "self"}


def self_returner(D, **kwargs):
    """Method to indicate that processed data need to be returned"""
    _ttp_["output_object"].return_to_self = True