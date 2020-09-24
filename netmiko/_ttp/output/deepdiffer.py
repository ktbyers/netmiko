import logging

log = logging.getLogger(__name__)

try:
    from deepdiff import DeepDiff

    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False
    log.error(
        "ttp.output failed to import deepdiff library, install 'pip install deepdiff'"
    )

_name_map_ = {"deepdiff_func": "deepdiff"}


def deepdiff_func(
    data,
    input_before=None,
    input_after=None,
    template_before=None,
    mode="bulk",
    add_field=False,
    var_before=None,
    **kwargs
):
    """
    Function to compare two structures.

    * data - list of dictionaries, results data
    * before - name of input that contains old data
    * after - name of input that contains new data
    * add_key - name of the key to add to data instead of replacing it
    * kwargs - arguments supported by deepdiff DeepDiff class e.g. ignore_order or verbose_level
    * mode - 'bulk' or 'iterate'
    """
    if HAS_LIBS is False:
        return data
    # get template object of this output
    template_obj = _ttp_["output_object"].template_obj

    # get data_before - data to compare with
    if input_before:
        # get inputs names to results index mapping, e.g.:
        # {'input_after': [3, 4], 'input_before': [0, 1], 'one_more': [2]}
        if template_obj.results_method.lower() == "per_input":
            input_to_results_index = {}
            counter = 0
            for input_name, details in template_obj.inputs.items():
                data_len = len(details.data)
                input_to_results_index[input_name] = [
                    i + counter for i in range(data_len)
                ]
                counter += data_len
            data_before = [
                data[index] for index in input_to_results_index[input_before]
            ]
        elif template_obj.results_method.lower() == "per_template":
            log.error(
                "ttp.output.deepdiff; Template 'per_template' results method not supported with input_before as a reference to source data"
            )
            return data
    # if template name provided - source data from template results
    elif template_before:
        for template in _ttp_["ttp_object"]._templates:
            if template.name == template_before:
                data_before = template.results
                break
    # if need to use vars content
    elif var_before:
        data_before = template_obj.vars[var_before]

    # get data after - data to compare against
    data_after = data
    if input_after:
        data_after = [data[index] for index in input_to_results_index[input_after]]

    # run compare
    result = {}
    if mode == "bulk":
        result = DeepDiff(data_before, data_after, **kwargs)
    elif mode == "iterate":
        result = [DeepDiff(data_before[0], item, **kwargs) for item in data_after]
    else:
        log.error(
            "ttp.output.deepdiff; Unsupported compare mode: '{}', supported are 'bulk' or 'iterate'".format(
                compare_mode
            )
        )
        return data

    # return results
    if add_field:
        if isinstance(data, list):
            data.append({add_field: result})
        elif isinstance(data, dict):
            data[add_field] = result
        return data
    else:
        return result