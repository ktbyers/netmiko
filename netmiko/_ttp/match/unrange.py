def unrange(data, rangechar, joinchar):
    """
    data - string, e.g. '8,10-13,20'
    rangechar - e.g. '-' for above string
    joinchar - e.g.',' for above string
    returns - e.g. '8,10,11,12,13,20 string
    """
    result = []
    # check if range char actually in data:
    if not rangechar in data:
        return data, None

    for item in data.split(rangechar):
        # form split list checking that i is not empty
        item_split = [i for i in item.split(joinchar) if i]
        if result:
            start_int = int(result[-1])
            try:
                end_int = int(item_split[0])
            except ValueError as e:
                log.error(
                    "ttp.match.unrange: Unrange failed, data '{}', rangechar '{}', joinchar '{}', error: {}".format(
                        data, rangechar, joinchar, e
                    )
                )
                return data, None
            list_of_ints_range = [str(i) for i in list(range(start_int, end_int))]
            result += list_of_ints_range[1:] + item_split
        else:
            result = item_split
    data = joinchar.join(result)
    return data, None