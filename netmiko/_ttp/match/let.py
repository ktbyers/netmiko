def let(data, name_or_value, var_value="__Undefined_Var_Value__"):
    if var_value == "__Undefined_Var_Value__":
        data = name_or_value
        return data, None
    else:
        return data, {"new_field": {name_or_value: var_value}}
