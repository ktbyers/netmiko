def is_equal(data):
    data_to_compare_with = _ttp_["output_object"].tag_load
    is_equal = False
    if "_anonymous_" in data:
        if data["_anonymous_"] == data_to_compare_with:
            is_equal = True
    elif data == data_to_compare_with:
        is_equal = True
    return {
        "output_name": _ttp_["output_object"].name,
        "output_description": _ttp_["output_object"].attributes.get(
            "description", "None"
        ),
        "is_equal": is_equal,
    }