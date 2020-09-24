import os
import logging

log = logging.getLogger(__name__)


def load_files(path, extensions=[], filters=[], read=False):
    """
    Method to load files from path, and filter file names with
    REs filters and extensions.
    Args:
        path (str): string that contains OS path
        extensions (list): list of strings files' extensions like ['txt', 'log', 'conf']
        filters (list): list of strings regexes to filter files
        read (bool): if False will return file names, if true will
    Returns:
        List of (type, text_data) tuples or empty list []  if
        read True, if read False return (type, url,) or []
    """
    files = []
    # need to use path[:5000] cause if path is actually text of the template
    # and has length more then X symbols, os.path will choke with "path too long"
    # error, hence the safe-assumption that no os path exists longer then 5000 symbols

    # check if structured, non text, data given, return it as is if so
    # to process within input macro/function
    if not isinstance(path, str):
        return [
            (
                "structured_data",
                path,
            )
        ]
    elif _ttp_["python_major_version"] == 2:
        if not isinstance(
            path,
            (
                unicode,
                str,
            ),
        ):
            return [
                (
                    "structured_data",
                    path,
                )
            ]

    # check if path is a path to file:
    if os.path.isfile(path[:5000]):
        if read:
            try:
                if _ttp_["python_major_version"] is 2:
                    with open(path, "r") as file_obj:
                        return [
                            (
                                "text_data",
                                file_obj.read(),
                            )
                        ]
                with open(path, "r", encoding="utf-8") as file_obj:
                    return [
                        (
                            "text_data",
                            file_obj.read(),
                        )
                    ]
            except UnicodeDecodeError:
                log.warning(
                    'ttp_utils.load_files: Unicode read error, file "{}"'.format(path)
                )
        else:
            return [
                (
                    "file_name",
                    path,
                )
            ]
    # check if path is a directory:
    elif os.path.isdir(path[0:5000]):
        from re import search as re_search

        files = [f for f in os.listdir(path) if os.path.isfile(path + f)]
        if extensions:
            files = [f for f in files if f.split(".")[-1] in extensions]
        for filter in filters:
            files = [f for f in files if re_search(filter, f)]
        if read:
            ret = []
            for f in files:
                if _ttp_["python_major_version"] is 2:
                    with open((path + f), "r") as file_obj:
                        ret.append(
                            (
                                "text_data",
                                file_obj.read(),
                            )
                        )
                elif _ttp_["python_major_version"] is 3:
                    with open((path + f), "r", encoding="utf-8") as file_obj:
                        ret.append(
                            (
                                "text_data",
                                file_obj.read(),
                            )
                        )
            return ret
        else:
            return [
                (
                    "file_name",
                    path + f,
                )
                for f in files
            ]
    # check if path is a string:
    elif isinstance(path, str):
        return [
            (
                "text_data",
                path,
            )
        ]
    # check if py2, if so check if path is unicode string:
    elif _ttp_["python_major_version"] == 2:
        if isinstance(path, unicode):
            return [
                (
                    "text_data",
                    path,
                )
            ]
    else:
        return []


def load_struct(text_data="", **kwargs):
    """Method to load structured data from text
    or from file(s) given in include attribute
    Args:
        element (obj): ETree xml tag object
    Returns:
        empy {} dict if nothing found, or python dictionary of loaded
        data from elemnt.text string or from included text files
    """
    result = {}
    loader = kwargs.get("load", "python").lower()
    include = kwargs.get("include", None)
    if not text_data and include is None:
        return None
    elif text_data is None and include:
        text_data = ""
    # dispatcher:
    loaders = {
        "ini": load_ini,
        "python": load_python,
        "yaml": load_yaml,
        "json": load_json,
        "csv": load_csv,
        "text": load_text,
    }
    # run function to load structured data
    result = loaders[loader](text_data, **kwargs)
    return result


def load_text(text_data, include=None, **kwargs):
    return text_data


def _get_include_data(text_data, include):
    files = load_files(path=include, extensions=[], filters=[], read=True)
    for datum in files:
        text_data += "\n" + datum[1]
    return text_data


def load_ini(text_data, include=None, **kwargs):
    if _ttp_["python_major_version"] is 3:
        import configparser

        cfgparser = configparser.ConfigParser()
        # to make cfgparser keep the case, e.g. VlaN222 will not become vlan222:
        cfgparser.optionxform = str
        # read from ini files first
        if include:
            files = load_files(path=include, extensions=[], filters=[], read=False)
            for datum in files:
                try:
                    cfgparser.read(datum[1])
                except:
                    log.error(
                        "ttp_utils.load_struct: Pythom3, Unable to load ini formatted data\n'{}'".format(
                            text_data
                        )
                    )
        # read from tag text next to make it more specific:
        if text_data:
            try:
                cfgparser.read_string(text_data)
            except:
                log.error(
                    "ttp_utils.load_struct: Python3, Unable to load ini formatted data\n'{}'".format(
                        text_data
                    )
                )
        # convert configparser object into dictionary
        result = {k: dict(cfgparser.items(k)) for k in list(cfgparser.keys())}
    elif _ttp_["python_major_version"] is 2:
        import ConfigParser
        import StringIO

        cfgparser = ConfigParser.ConfigParser()
        # to make cfgparser keep the case, e.g. VlaN222 will not become vlan222:
        cfgparser.optionxform = str
        # read from ini files first
        if include:
            files = load_files(path=include, extensions=[], filters=[], read=False)
            for datum in files:
                try:
                    cfgparser.read(datum[1])
                except:
                    log.error(
                        "ttp_utils.load_struct: Python2, Unable to load ini formatted data\n'{}'".format(
                            text_data
                        )
                    )
        # read from tag text next to make it more specific:
        if text_data:
            buf_text_data = StringIO.StringIO(text_data)
            try:
                cfgparser.readfp(buf_text_data)
            except:
                log.error(
                    "ttp_utils.load_struct: Python2, Unable to load ini formatted data\n'{}'".format(
                        text_data
                    )
                )
        # convert configparser object into dictionary
        result = {k: dict(cfgparser.items(k)) for k in list(cfgparser.sections())}
    if "DEFAULT" in result:
        if not result["DEFAULT"]:  # delete empty DEFAULT section
            result.pop("DEFAULT")
    return result


def load_python(text_data, include=None, **kwargs):
    data = {}
    if include:
        text_data = _get_include_data(text_data, include)
    try:
        data = _ttp_["utils"]["load_python_exec"](text_data)
        return data
    except SyntaxError as e:
        log.error(
            "ttp_utils.load_struct: Unable to load Python formatted data\n'{}'Make sure that correct loader used to load data, error:\n{}".format(
                text_data, e
            )
        )


def load_yaml(text_data, include=None, **kwargs):
    try:
        from yaml import safe_load
    except ModuleNotFoundError:
        log.error(
            "loaders.load_yaml: failed to import yaml module, install: 'python -m pip install pyyaml'"
        )
    data = {}
    if include:
        text_data = _get_include_data(text_data, include)
    try:
        data = safe_load(text_data)
    except:
        log.error(
            "ttp_utils.load_struct: Unable to load YAML formatted data\n'{}'".format(
                text_data
            )
        )
    return data


def load_json(text_data, include=None, **kwargs):
    from json import loads

    data = {}
    if include:
        text_data = _get_include_data(text_data, include)
    try:
        data = loads(text_data)
        return data
    except:
        log.error(
            "ttp_utils.load_struct: Unable to load JSON formatted data\n'{}'".format(
                text_data
            )
        )


def load_csv(text_data, include=None, **kwargs):
    """Method to load csv data and convert it to dictionary
    using given key-header-column as keys or first column as keys
    """
    from csv import reader

    key = kwargs.get("key", None)
    data = {}
    headers = []
    if include:
        text_data = _get_include_data(text_data, include)
    for row in reader(iter(text_data.splitlines())):
        if not row:
            continue
        if not headers:
            headers = row
            if not key:
                key = headers[0]
            elif key and key not in headers:
                return data
            continue
        temp = {headers[index]: i for index, i in enumerate(row)}
        data[temp.pop(key)] = temp
    return data