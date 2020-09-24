def load_python_exec(text_data, builtins=None):
    """
    Function to provide compatibility with python 3.7 for loading text formwatted in
    python using exec built-in method. Exec syntaxis in pyton 2.6 different
    compared to python3.x and python3 spits "Invlaid Syntaxis error" while trying to
    run code below.
    """
    data = {}
    globals_dict = {
        "__builtins__": builtins,
        "_ttp_": _ttp_,
        "False": False,
        "True": True,
        "None": None,
    }
    # below can run on python3.7 as exec is a function not statement for python3.7:
    exec(compile(text_data, "<string>", "exec"), globals_dict, data)
    # add extracted functions to globals for recursion to work
    globals_dict.update(data)
    # run eval in case if data still empty as we might have python dictionary or list
    # expressed as string
    if not data:
        data = eval(text_data, None, None)
    return data