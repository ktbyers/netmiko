def itemize(data, key, path=""):
    # if no path given use group path to save results
    if key in data and not path:
        res_path = _ttp_["results_object"].record["PATH"]
        # modify path to have single '*' at the end
        if res_path[-1].endswith("**") or not res_path[-1].endswith("*"):
            res_path[-1] = "{}*".format(res_path[-1].rstrip("*"))
        _ttp_["results_object"].record["PATH"] = res_path
        return data.pop(key), None
    # use path provided
    elif key in data and path:
        # form and check path
        path = [i.strip() for i in path.split(".")]
        if path[-1].endswith("**") or not path[-1].endswith("*"):
            path[-1] = "{}*".format(path[-1].rstrip("*"))
        # save item into results:
        _ttp_["results_object"].save_curelements(
            result_data=data[key], result_path=path
        )
    # group considered to be invalid if no key in it
    else:
        return data, False
    return data, None