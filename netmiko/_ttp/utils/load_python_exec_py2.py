def load_python_exec(text_data, builtins=None):
    """
    Function to provide compatibility with python 2.6 for loading text formatted in 
    python using exec built-in method. Exec syntaxes in pyton 2.6 different
    compared to python3.x and python3 spits "Invlaid Syntaxis error" while trying to 
    run code below.
    """
    data = {} 
    globals_dict = {"__builtins__" : builtins, "_ttp_": _ttp_, "False": False, "True": True, "None": None}
    # below can run on python2.7 as exec is a statements not function for python2.7:
    try:
        exec compile(text_data, '<string>', 'exec') in globals_dict, data
    except NameError:
        # NameError can occure if we have "True" or "False" in text_data
        # that way eval will catch it, but exec will through and error:
        # NameError: name 'True' is not defined
        pass 
    # add extracted functions to globals for recursion to work
    globals_dict.update(data)
    # run eval in case if data still empty as we might have python dictionary or list
    # expressed as string
    if not data:
        data = eval(text_data, None, None)
    return data